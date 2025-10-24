# Create your views here.
# apps/debugger/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import DebugSession, DebugQuery
from .image_processor import DebugImageProcessor
from .web_searcher import WebSearcher
from apps.rag_search.generation import GenerationService
import os
import uuid


@login_required
def debug_assistant(request):
    """Main debug assistant interface"""
    sessions = DebugSession.objects.filter(user=request.user)[:10]
    return render(request, 'debugger/debug_assistant.html', {
        'sessions': sessions
    })


@login_required
@require_http_methods(["POST"])
def submit_debug_query(request):
    """
    Handle debug query submission with STREAMING response
    """
    from django.http import StreamingHttpResponse
    import json
    
    try:
        # Get these OUTSIDE the generator so they're in scope
        query_text = request.POST.get('query', '').strip()
        image_file = request.FILES.get('error_image')
        
        if not query_text and not image_file:
            return JsonResponse({'error': 'Provide query text or image'}, status=400)
        
        # Create or get session
        session, created = DebugSession.objects.get_or_create(
            user=request.user,
            defaults={'title': f"Debug {query_text[:30] if query_text else 'Error'}..."}
        )
        
        # Save image outside generator (file objects can't be passed to generators)
        image_path = None
        if image_file:
            filename = f"debug_{uuid.uuid4().hex}.{image_file.name.split('.')[-1]}"
            image_path = default_storage.save(f"debug_images/{filename}", ContentFile(image_file.read()))
        
        def event_stream():
            """Generator for Server-Sent Events"""
            # Use nonlocal to access outer variables
            nonlocal query_text
            
            try:
                error_info = {}
                
                # Process image if provided
                if image_path:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Processing image...'})}\n\n"
                    
                    full_path = os.path.join(default_storage.location, image_path)
                    
                    # Extract error from image
                    processor = DebugImageProcessor()
                    error_info = processor.extract_error_from_image(full_path)
                    
                    # Send error info
                    yield f"data: {json.dumps({'type': 'error_info', 'data': error_info})}\n\n"
                    
                    # Update query if image contains error and no text query
                    if not query_text:
                        query_text = error_info.get('error_message', 'Debug this error')
                
                # Search external sources
                yield f"data: {json.dumps({'type': 'status', 'message': 'Searching StackOverflow...'})}\n\n"
                
                search_query = f"{error_info.get('error_type', '')} {query_text}".strip()
                searcher = WebSearcher()
                stackoverflow_results = searcher.search_stackoverflow(search_query, top_k=5)
                
                yield f"data: {json.dumps({'type': 'stackoverflow', 'data': stackoverflow_results})}\n\n"
                
                yield f"data: {json.dumps({'type': 'status', 'message': 'Searching web...'})}\n\n"
                web_results = searcher.search_web(search_query, top_k=3)
                
                yield f"data: {json.dumps({'type': 'web', 'data': web_results})}\n\n"
                
                # Generate AI response with STREAMING
                yield f"data: {json.dumps({'type': 'status', 'message': 'Generating solution...'})}\n\n"
                
                full_response = ""
                for chunk in _generate_debug_response_stream(query_text, error_info, stackoverflow_results, web_results):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Save query
                debug_query = DebugQuery.objects.create(
                    session=session,
                    user=request.user,
                    query_text=query_text,
                    has_image=bool(image_path),
                    image_path=image_path or '',
                    error_type=error_info.get('error_type', ''),
                    error_message=error_info.get('error_message', ''),
                    extracted_text=error_info.get('extracted_text', ''),
                    response=full_response,
                    stackoverflow_results=stackoverflow_results,
                    web_results=web_results
                )
                
                yield f"data: {json.dumps({'type': 'done', 'query_id': str(debug_query.id)})}\n\n"
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def _generate_debug_response_stream(query, error_info, stackoverflow_results, web_results):
    """Generate AI response with STREAMING"""
    
    # Build context from sources
    context_parts = []
    
    if error_info:
        context_parts.append(f"**Error Detected:**\n- Type: {error_info.get('error_type')}\n- Message: {error_info.get('error_message')}")
    
    if stackoverflow_results:
        context_parts.append("\n**StackOverflow Solutions:**")
        for i, result in enumerate(stackoverflow_results[:3], 1):
            context_parts.append(f"{i}. [{result['title']}]({result['link']}) (Score: {result['score']})")
    
    if web_results:
        context_parts.append("\n**Web Resources:**")
        for i, result in enumerate(web_results, 1):
            context_parts.append(f"{i}. [{result['title']}]({result['link']})")
    
    context = "\n".join(context_parts)
    
    # Generate response with Gemini STREAMING
    try:
        gen_service = GenerationService()
        
        prompt = f"""You are a debugging assistant. Help solve this error:

**User Query:** {query}

**Available Context:**
{context}

Provide:
1. **Error Explanation** (what's causing it)
2. **Solution Steps** (numbered, actionable)
3. **Code Example** (if applicable)
4. **Prevention Tips** (how to avoid in future)

Use markdown formatting. Be concise but thorough."""

        # Stream response
        response = gen_service.model.generate_content(prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
        
    except Exception as e:
        yield f"\n\n❌ Error generating response: {str(e)}\n\n{context}"
