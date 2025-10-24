# apps/chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .memory_manager import ChatMemoryManager
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from .image_handler import ChatImageHandler
from django.core.files.storage import default_storage
from django.views.decorators.http import require_http_methods
import json
import traceback


from .models import ChatSession, ChatMessage
from apps.rag_search.rag_pipeline import RAGPipeline


@login_required
def chat_session_list(request):
    """Display list of user's chat sessions"""
    sessions = ChatSession.objects.filter(user=request.user)
    return render(request, 'chat/chat_list.html', {'sessions': sessions})





@login_required
def chat_session_detail(request, session_id):
    """Display a specific chat session with messages"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = ChatMessage.objects.filter(session=session).order_by('created_at')
    return render(request, 'chat/chat_detail.html', {'session': session, 'messages': messages})


@login_required
def chat_session_create(request):
    """Create a new chat session with optional repository context"""
    from apps.repo_ingest.models import Repository
    
    # Get parameters from URL
    repo_id = request.GET.get('repo_id')
    pre_fill_question = request.GET.get('question', '')
    
    # Create new session
    session = ChatSession.objects.create(
        user=request.user,
        title=f"Chat {timezone.now().strftime('%b %d, %Y %I:%M %p')}"
    )
    
    # Get repository prompts if repo_id provided
    suggested_prompts = []
    if repo_id:
        try:
            repo = Repository.objects.get(id=repo_id, user=request.user)
            suggested_prompts = repo.suggested_prompts or []
        except:
            pass
    
    # If coming from repository status, render with prompts
    if repo_id or pre_fill_question or suggested_prompts:
        return render(request, 'chat/chat_detail.html', {
            'session': session,
            'messages': [],
            'suggested_prompts': suggested_prompts,
            'pre_fill_question': pre_fill_question
        })
    
    # Otherwise redirect to session detail
    return redirect('chat:session_detail', session_id=session.id)


@login_required
def memory_debug(request):
    """Debug view to check memory stats"""
    from .memory_manager import ChatMemoryManager
    
    manager = ChatMemoryManager()
    
    # Get stats
    stats = manager.get_memory_stats(request.user.id)
    
    # Search memories
    memories = manager.search_memories(
        user_id=request.user.id,
        query="authentication",
        top_k=5
    )
    
    return render(request, 'chat/memory_debug.html', {
        'stats': stats,
        'memories': memories
    })


@login_required
def memory_stats(request):
    """Get user's memory statistics"""
    try:
        memory_manager = ChatMemoryManager()
        stats = memory_manager.get_memory_stats(request.user.id)
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def chat_message_stream(request, session_id):
    """Stream AI response in real-time with CODE RETRIEVAL + IMAGE SUPPORT"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    try:
        # Get text question
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            question = data.get('message', '').strip()
        else:
            question = request.POST.get('message', '').strip()
            
        # Get image if uploaded
        image_file = request.FILES.get('image')
        
        if not question and not image_file:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        # Save image if provided
        image_path = None
        if image_file:
            image_handler = ChatImageHandler()
            image_path = image_handler.save_image(image_file)
        
        # Create user message
        user_msg = ChatMessage.objects.create(
            session=session,
            user=request.user,
            role='user',
            content=question or '(Image uploaded)',
            has_image=bool(image_path),
            image_path=image_path or ''
        )
        
        def event_stream():
            yield f"data: {json.dumps({'type': 'start', 'user_message_id': str(user_msg.id)})}\n\n"
            
            try:
                rag_pipeline = RAGPipeline()
                
                # ✅ ENHANCED: Check for image analysis
                if image_path:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing image...'})}\n\n"
                    
                    # Get code context for image analysis
                    try:
                        query_embedding = rag_pipeline.embed_service.embed_query(question or "analyze this image")
                        code_chunks = rag_pipeline._retrieve_code_context(
                            query_embedding=query_embedding,
                            user_id=request.user.id,
                            top_k=3  # Less chunks for image context
                        )
                        code_context = "\n\n".join([c['source']['content'][:500] for c in code_chunks[:3]])
                    except:
                        code_context = ""
                    
                    # Stream image analysis
                    image_handler = ChatImageHandler()
                    full_answer = ""
                    for chunk in image_handler.analyze_image_stream(image_path, question or "Analyze this image", code_context):
                        full_answer += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                else:
                    # Regular text-only chat with code retrieval
                    try:
                        print(f"🔍 Processing query with code retrieval for user {request.user.id}")
                        
                        session_messages = list(
                            ChatMessage.objects.filter(session=session)
                            .order_by('created_at')
                            .values('role', 'content')
                        )
                        
                        intent = rag_pipeline._detect_query_intent_ai(question)
                        print(f"🎯 Intent: {intent['type']}, retrieving {intent['top_k']} chunks")
                        
                        query_embedding = rag_pipeline.embed_service.embed_query(question)

                        if intent['type'] == 'aggregation':
                            code_chunks = rag_pipeline._retrieve_code_aggregation(
                                query_embedding=query_embedding,
                                user_id=request.user.id,
                                question=question,
                                top_k=intent['top_k']
                            )
                        else:
                            code_chunks = rag_pipeline._retrieve_code_context(
                                query_embedding=query_embedding,
                                user_id=request.user.id,
                                top_k=intent['top_k']
                            )

                        past_summaries = rag_pipeline._retrieve_past_summaries(
                            query_embedding=query_embedding,
                            user_id=request.user.id,
                            top_k=3
                        )

                        print(f"✅ Retrieved {len(code_chunks)} code chunks, {len(past_summaries)} summaries")
                        
                        full_answer = ""
                        for chunk in rag_pipeline.generation_service.generate_with_full_context_stream(
                            question=question,
                            code_chunks=code_chunks,
                            past_summaries=past_summaries,
                            session_messages=session_messages,
                            max_code_chunks=len(code_chunks),
                            max_summaries=3
                        ):
                            full_answer += chunk
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                        
                    except Exception as e:
                        print(f"⚠️ Full RAG failed: {str(e)}, using fallback")
                        traceback.print_exc()
                        
                        full_answer = ""
                        session_messages = list(
                            ChatMessage.objects.filter(session=session)
                            .order_by('created_at')
                            .values('role', 'content')
                        )
                        for chunk in rag_pipeline.generation_service.generate_with_full_context_stream(
                            question=question,
                            code_chunks=[],
                            past_summaries=[],
                            session_messages=session_messages,
                        ):
                            full_answer += chunk
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                assistant_msg = ChatMessage.objects.create(
                    session=session,
                    user=request.user,
                    role='assistant',
                    content=full_answer
                )
                
                session.updated_at = timezone.now()
                session.save()
                
                # Check for memory summarization
                try:
                    memory_manager = ChatMemoryManager()
                    memory_manager.check_and_summarize(
                        session_id=session.id,
                        user_id=request.user.id
                    )
                except Exception as e:
                    print(f"⚠️ Memory check failed: {e}")
                
                yield f"data: {json.dumps({'type': 'done', 'assistant_message_id': str(assistant_msg.id)})}\n\n"
                
            except Exception as e:
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
        
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def chat_message_create(request, session_id):
    """Handle new message (NON-STREAMING fallback with CODE RETRIEVAL)"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            question = data.get('message', '').strip()
        else:
            question = request.POST.get('message', '').strip()
    except Exception as e:
        return JsonResponse({'error': f'Invalid request: {str(e)}'}, status=400)
    
    if not question:
        return JsonResponse({'error': 'Empty message'}, status=400)
    
    try:
        user_msg = ChatMessage.objects.create(
            session=session,
            user=request.user,
            role='user',
            content=question
        )
        
        rag_pipeline = RAGPipeline()
        
        # ✅ Use full RAG pipeline with code retrieval
        try:
            answer = rag_pipeline.process_query(
                question=question,
                user_id=request.user.id,
                session_id=session.id
            )
        except Exception as e:
            print(f"⚠️ Full RAG failed, using simple version: {str(e)}")
            answer = rag_pipeline.process_query_simple(
                question=question,
                user_id=request.user.id,
                session_id=session.id
            )
        
        assistant_msg = ChatMessage.objects.create(
            session=session,
            user=request.user,
            role='assistant',
            content=answer
        )
        
        session.updated_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'role': user_msg.role,
                'content': user_msg.content,
                'created_at': user_msg.created_at.isoformat()
            },
            'assistant_message': {
                'id': assistant_msg.id,
                'role': assistant_msg.role,
                'content': assistant_msg.content,
                'created_at': assistant_msg.created_at.isoformat()
            }
        })
    
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'Failed to process message: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def chat_session_delete(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def chat_session_rename(request, session_id):
    """Rename a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            new_title = data.get('title', '').strip()
        else:
            new_title = request.POST.get('title', '').strip()
    except Exception as e:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    if not new_title:
        return JsonResponse({'error': 'Empty title'}, status=400)
    
    session.title = new_title
    session.save()
    
    return JsonResponse({'success': True, 'title': session.title})
