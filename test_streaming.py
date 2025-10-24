<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chat - {{ session.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/showdown@2.1.0/dist/showdown.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/javascript.min.js"></script>
    <style>
        .markdown-body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #24292f;
        }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 {
            font-weight: 600;
            margin: 16px 0 8px 0;
        }
        .markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
        .markdown-body h2 { font-size: 1.3em; }
        .markdown-body h3 { font-size: 1.1em; }
        .markdown-body ul, .markdown-body ol { margin: 8px 0; padding-left: 24px; }
        .markdown-body li { margin: 4px 0; }
        .markdown-body p { margin: 8px 0; }
        .markdown-body strong { font-weight: 600; color: #1f2937; }
        .markdown-body code {
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: #ef4444;
        }
        .markdown-body pre {
            background: #1e1e1e !important;
            color: #d4d4d4;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 12px 0;
        }
        .markdown-body pre code {
            background: none !important;
            padding: 0;
            color: inherit;
        }
        .markdown-body table {
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
        }
        .markdown-body table th, .markdown-body table td {
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }
        .markdown-body table th {
            background: #f6f8fa;
            font-weight: 600;
        }
        .markdown-body blockquote {
            border-left: 4px solid #3b82f6;
            padding-left: 16px;
            margin: 12px 0;
            color: #6b7280;
        }
        @keyframes fade-in {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
            animation: fade-in 0.3s ease-out;
        }
    </style>
</head>
<body class="bg-gray-100">
    <div class="max-w-4xl mx-auto p-4" x-data="chatApp()">
        <div class="bg-white rounded-lg shadow p-4 mb-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold">{{ session.title }}</h1>
                <div class="flex gap-3 text-sm mt-1">
                    <a href="/chat/" class="text-blue-600 hover:underline">← All chats</a>
                    <a href="/repo/" class="text-blue-600 hover:underline">📂 Repositories</a>
                    <a href="/debug/" class="text-blue-600 hover:underline">🔧 Debug Assistant</a>
                </div>
            </div>
            <div class="text-sm text-gray-500" x-show="loading">
                <span class="inline-block animate-pulse">● Jarvis is thinking...</span>
            </div>
        </div>

        <!-- ✅ SUGGESTED PROMPTS SECTION (NEW) -->
        {% if suggested_prompts %}
        <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow p-4 mb-4">
            <h2 class="text-lg font-bold mb-3 flex items-center">
                <span class="text-2xl mr-2">💡</span>
                Suggested Questions
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                {% for prompt in suggested_prompts %}
                <button 
                    onclick="fillQuestion('{{ prompt|escapejs }}')"
                    class="text-left p-3 bg-white hover:bg-blue-50 border border-blue-200 rounded-lg transition text-sm group"
                >
                    <span class="text-blue-600 mr-2 group-hover:scale-110 transition inline-block">🔍</span>
                    <span class="font-medium">{{ prompt }}</span>
                </button>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Messages Area -->
        <div class="bg-white rounded-lg shadow p-4 mb-4 h-96 overflow-y-auto" x-ref="messages">
            {% for message in messages %}
            <div class="mb-4 {% if message.role == 'user' %}text-right{% endif %}">
                <div class="inline-block px-4 py-2 rounded max-w-2xl text-left {% if message.role == 'user' %}bg-blue-500 text-white{% else %}bg-gray-50 border border-gray-200{% endif %}">
                    {% if message.role == 'user' %}
                        <div class="whitespace-pre-wrap text-sm">{{ message.content }}</div>
                        {% if message.has_image %}
                            <img src="/media/{{ message.image_path }}" class="mt-2 rounded max-w-md border">
                        {% endif %}
                    {% else %}
                        <div class="markdown-body"></div>
                        <script>
                            (function() {
                                const el = document.currentScript.previousElementSibling;
                                const content = `{{ message.content|escapejs }}`;
                                const converter = new showdown.Converter({ 
                                    tables: true, 
                                    strikethrough: true, 
                                    emoji: true,
                                    ghCodeBlocks: true,
                                    tasklists: true
                                });
                                el.innerHTML = converter.makeHtml(content);
                                el.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
                            })();
                        </script>
                    {% endif %}
                </div>
            </div>
            {% empty %}
            <div class="text-center text-gray-400 py-8">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <p>No messages yet. Start chatting!</p>
                <p class="text-xs mt-2">💡 You can also paste images with Ctrl+V</p>
            </div>
            {% endfor %}
        </div>

        <!-- Input Form with Image Support -->
        <form @submit.prevent="sendMessage" class="bg-white rounded-lg shadow p-4">
            <!-- Image Preview -->
            <template x-if="imagePreview">
                <div class="mb-3 relative inline-block">
                    <img :src="imagePreview" class="h-24 rounded border">
                    <button @click="clearImage" type="button" 
                            class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 text-xs">
                        ×
                    </button>
                    <p class="text-xs text-gray-600 mt-1">📷 Image attached (will be analyzed)</p>
                </div>
            </template>

            <div class="flex gap-2">
                <!-- Image Upload Button -->
                <label class="cursor-pointer">
                    <input type="file" @change="handleFileSelect" accept="image/*" class="hidden" x-ref="fileInput">
                    <div class="p-2 bg-gray-100 hover:bg-gray-200 rounded transition border border-gray-300" 
                         title="Upload image or press Ctrl+V to paste">
                        📷
                    </div>
                </label>

                <!-- Text Input -->
                <input 
                    type="text" 
                    x-model="input" 
                    placeholder="Ask about your code or paste an image (Ctrl+V)..." 
                    class="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    :disabled="loading" 
                    x-ref="input"
                >

                <!-- Send Button -->
                <button 
                    type="submit" 
                    class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-2 rounded font-semibold transition" 
                    :disabled="loading || (!input.trim() && !selectedFile)"
                >
                    <span x-show="!loading">Send</span>
                    <span x-show="loading">
                        <svg class="animate-spin h-5 w-5 inline-block" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </span>
                </button>
            </div>
        </form>
    </div>

    <script>
    // ✅ GLOBAL FUNCTION FOR FILLING QUESTIONS
    function fillQuestion(question) {
        const app = Alpine.$data(document.querySelector('[x-data]'));
        app.input = question;
        app.$refs.input.focus();
    }

    function chatApp() {
        return {
            input: '',
            loading: false,
            currentContainer: null,
            currentSegment: '',
            inCodeBlock: false,
            codeBuffer: '',
            codeLanguage: '',
            converter: null,
            pendingBuffer: '',
            selectedFile: null,
            imagePreview: null,

            init() {
                this.converter = new showdown.Converter({
                    tables: true,
                    strikethrough: true,
                    emoji: true,
                    ghCodeBlocks: true,
                    tasklists: true
                });

                // Listen for Ctrl+V paste
                document.addEventListener('paste', this.handlePaste.bind(this));
                console.log('📋 Image paste enabled!');

                // ✅ PRE-FILL QUESTION IF PROVIDED
                {% if pre_fill_question %}
                this.input = '{{ pre_fill_question|escapejs }}';
                this.$nextTick(() => {
                    this.$refs.input.focus();
                });
                {% endif %}
            },

            handlePaste(event) {
                const items = (event.clipboardData || event.originalEvent.clipboardData).items;
                
                for (let item of items) {
                    if (item.type.indexOf('image') !== -1) {
                        event.preventDefault();
                        
                        const blob = item.getAsFile();
                        const file = new File([blob], 'pasted-image.png', { type: blob.type });
                        this.selectedFile = file;
                        
                        const reader = new FileReader();
                        reader.onload = (e) => {
                            this.imagePreview = e.target.result;
                            this.showNotification('📷 Image pasted! Ask a question about it.');
                        };
                        reader.readAsDataURL(blob);
                        
                        break;
                    }
                }
            },

            handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    this.selectedFile = file;
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        this.imagePreview = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            },

            clearImage() {
                this.selectedFile = null;
                this.imagePreview = null;
                this.$refs.fileInput.value = '';
            },

            showNotification(message) {
                const notification = document.createElement('div');
                notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.opacity = '0';
                    notification.style.transition = 'opacity 0.5s';
                    setTimeout(() => notification.remove(), 500);
                }, 3000);
            },

            async sendMessage() {
                if ((!this.input.trim() && !this.selectedFile) || this.loading) return;

                const msg = this.input;
                const hasImage = !!this.selectedFile;
                const imageSrc = this.imagePreview;
                
                this.input = '';
                this.loading = true;

                this.addUserMessage(msg || '(Image uploaded)', imageSrc);
                
                this.currentContainer = this.createAssistantContainer();
                this.currentSegment = '';
                this.inCodeBlock = false;
                this.codeBuffer = '';
                this.codeLanguage = '';
                this.pendingBuffer = '';

                try {
                    const formData = new FormData();
                    formData.append('message', msg);
                    if (this.selectedFile) {
                        formData.append('image', this.selectedFile);
                    }

                    this.clearImage();

                    const response = await fetch('/chat/{{ session.id }}/stream/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: formData
                    });

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop();

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.substring(6));
                                    
                                    if (data.type === 'chunk') {
                                        await this.processChunk(data.content);
                                    } else if (data.type === 'done') {
                                        this.finalizePendingContent();
                                        this.loading = false;
                                    } else if (data.type === 'error') {
                                        this.addError('⚠️ Error: ' + data.error);
                                        this.loading = false;
                                    }
                                } catch (e) {
                                    console.error('Parse error:', e);
                                }
                            }
                        }
                    }
                } catch (err) {
                    this.addError('⚠️ Error: ' + err.message);
                    this.loading = false;
                } finally {
                    this.$nextTick(() => this.$refs.input.focus());
                }
            },

            async processChunk(text) {
                this.pendingBuffer += text;
                const parts = this.pendingBuffer.split('```');
                
                if (parts.length === 1) {
                    await this.streamText(text);
                } else if (parts.length >= 2) {
                    if (!this.inCodeBlock) {
                        await this.streamText(parts[0]);
                        this.finalizePendingContent();
                        
                        const remaining = parts.slice(1).join('```');
                        const firstLineMatch = remaining.match(/^(\w+)?\n/);
                        if (firstLineMatch) {
                            this.codeLanguage = firstLineMatch[1] || 'python';
                        } else {
                            this.codeLanguage = 'python';
                        }
                        
                        this.inCodeBlock = true;
                        this.codeBuffer = '';
                        this.pendingBuffer = parts.slice(1).join('```');
                        
                        if (parts.length > 2) {
                            this.codeBuffer = parts[1];
                            this.finalizeCodeBlock();
                            this.inCodeBlock = false;
                            this.pendingBuffer = parts.slice(2).join('```');
                        }
                    } else {
                        this.codeBuffer += parts[0];
                        this.finalizeCodeBlock();
                        this.inCodeBlock = false;
                        this.pendingBuffer = parts.slice(1).join('```');
                    }
                }
            },

            async streamText(text) {
                for (let char of text) {
                    this.currentSegment += char;
                    this.renderCurrentSegment();
                    await new Promise(r => setTimeout(r, 15));
                }
            },

            renderCurrentSegment() {
                const elements = this.currentContainer.querySelectorAll('.markdown-body');
                let lastTextElement = null;
                
                for (let el of elements) {
                    if (!el.querySelector('pre')) {
                        lastTextElement = el;
                    }
                }
                
                if (!lastTextElement) {
                    lastTextElement = this.createTextElement();
                }
                
                lastTextElement.innerHTML = this.converter.makeHtml(this.currentSegment);
            },

            finalizePendingContent() {
                if (this.currentSegment) {
                    this.currentSegment = '';
                }
            },

            createTextElement() {
                const div = document.createElement('div');
                div.className = 'markdown-body';
                this.currentContainer.appendChild(div);
                this.scrollToBottom();
                return div;
            },

            finalizeCodeBlock() {
                const codeDiv = document.createElement('div');
                codeDiv.className = 'markdown-body';
                
                let cleanCode = this.codeBuffer;
                if (cleanCode.match(/^(\w+)?\n/)) {
                    cleanCode = cleanCode.replace(/^(\w+)?\n/, '');
                }
                
                const codeHtml = this.converter.makeHtml('```' + this.codeLanguage + '\n' + cleanCode + '\n```');
                codeDiv.innerHTML = codeHtml;
                codeDiv.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
                
                this.currentContainer.appendChild(codeDiv);
                this.codeBuffer = '';
                this.codeLanguage = '';
                this.currentSegment = '';
                this.scrollToBottom();
            },

            addUserMessage(content, imageSrc = null) {
                const div = document.createElement('div');
                div.className = 'mb-4 text-right';
                let html = `
                    <div class="inline-block px-4 py-2 rounded max-w-2xl bg-blue-500 text-white text-left">
                        <div class="whitespace-pre-wrap text-sm">${this.escapeHtml(content)}</div>
                `;
                if (imageSrc) {
                    html += `<img src="${imageSrc}" class="mt-2 rounded max-w-md border">`;
                }
                html += `</div>`;
                div.innerHTML = html;
                this.$refs.messages.appendChild(div);
                this.scrollToBottom();
            },

            createAssistantContainer() {
                const div = document.createElement('div');
                div.className = 'mb-4 text-left';
                const inner = document.createElement('div');
                inner.className = 'inline-block px-4 py-2 rounded max-w-2xl bg-gray-50 border border-gray-200';
                div.appendChild(inner);
                this.$refs.messages.appendChild(div);
                this.scrollToBottom();
                return inner;
            },

            addError(msg) {
                const div = document.createElement('div');
                div.className = 'markdown-body';
                div.textContent = msg;
                this.currentContainer.appendChild(div);
                this.scrollToBottom();
            },

            scrollToBottom() {
                this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight;
            },

            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        };
    }
    </script>
</body>
</html>






























<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chat - {{ session.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/showdown@2.1.0/dist/showdown.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
    <style>
        .markdown-body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            font-size: 14px; 
            line-height: 1.6; 
            color: #24292f; 
        }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { 
            font-weight: 600; 
            margin: 16px 0 8px 0; 
        }
        .markdown-body h1 { 
            font-size: 1.5em; 
            border-bottom: 1px solid #e5e7eb; 
            padding-bottom: 6px; 
        }
        .markdown-body h2 { font-size: 1.3em; }
        .markdown-body h3 { font-size: 1.1em; }
        .markdown-body ul, .markdown-body ol { 
            margin: 8px 0; 
            padding-left: 24px; 
        }
        .markdown-body li { margin: 4px 0; }
        .markdown-body p { margin: 8px 0; }
        .markdown-body strong { 
            font-weight: 600; 
            color: #1f2937; 
        }
        .markdown-body em { font-style: italic; }
        .markdown-body code { 
            background: #f6f8fa; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-family: 'Consolas', monospace; 
            font-size: 0.9em; 
            color: #ef4444; 
        }
        .markdown-body pre { 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 16px; 
            border-radius: 6px; 
            overflow-x: auto; 
            margin: 12px 0; 
        }
        .markdown-body pre code { 
            background: none; 
            padding: 0; 
            color: inherit; 
        }
        .markdown-body table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 12px 0; 
        }
        .markdown-body table th, .markdown-body table td { 
            border: 1px solid #d0d7de; 
            padding: 8px 12px; 
            text-align: left; 
        }
        .markdown-body table th { 
            background: #f6f8fa; 
            font-weight: 600; 
        }
        .markdown-body blockquote { 
            border-left: 4px solid #3b82f6; 
            padding-left: 16px; 
            margin: 12px 0; 
            color: #6b7280; 
        }
        .markdown-body a { 
            color: #0969da; 
            text-decoration: none; 
        }
        .markdown-body a:hover { 
            text-decoration: underline; 
        }
        .code-generating { 
            background: linear-gradient(90deg, #e5e7eb, #d1d5db, #e5e7eb); 
            background-size: 200%; 
            animation: shimmer 1.5s infinite; 
            padding: 16px; 
            border-radius: 6px; 
            margin: 12px 0; 
            color: #6b7280; 
            font-size: 14px; 
        }
        @keyframes shimmer { 
            0%, 100% { background-position: 0%; } 
            50% { background-position: 100%; } 
        }
        .streaming-segment { display: inline; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="max-w-4xl mx-auto p-4" x-data="chatApp()">
        <div class="bg-white rounded-lg shadow p-4 mb-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold">{{ session.title }}</h1>
                <a href="/chat/" class="text-blue-600 hover:underline">← Back to chats</a>
            </div>
            <div class="text-sm text-gray-500" x-show="loading">
                <span class="inline-block animate-pulse">● Jarvis is thinking...</span>
            </div>
        </div>
        <div class="bg-white rounded-lg shadow p-4 mb-4 h-96 overflow-y-auto" x-ref="messages">
            {% for message in messages %}
            <div class="mb-4 {% if message.role == 'user' %}text-right{% endif %}">
                <div class="inline-block px-4 py-2 rounded max-w-2xl text-left {% if message.role == 'user' %}bg-blue-500 text-white{% else %}bg-gray-50 border border-gray-200{% endif %}">
                    {% if message.role == 'user' %}
                        <div class="whitespace-pre-wrap text-sm">{{ message.content }}</div>
                    {% else %}
                        <div class="markdown-body"></div>
                        <script>
                            (function() {
                                const el = document.currentScript.previousElementSibling;
                                const content = `{{ message.content|escapejs }}`;
                                const converter = new showdown.Converter({ 
                                    tables: true, 
                                    strikethrough: true, 
                                    emoji: true 
                                });
                                el.innerHTML = converter.makeHtml(content);
                                el.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
                            })();
                        </script>
                    {% endif %}
                </div>
            </div>
            {% empty %}
            <div class="text-center text-gray-400 py-8">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <p>No messages yet. Start chatting!</p>
            </div>
            {% endfor %}
        </div>
        <form @submit.prevent="sendMessage" class="bg-white rounded-lg shadow p-4 flex gap-2">
            <input 
                type="text" 
                x-model="input" 
                placeholder="Ask me anything..." 
                class="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                :disabled="loading" 
                x-ref="input"
            >
            <button 
                type="submit" 
                class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-2 rounded font-semibold" 
                :disabled="loading || !input.trim()"
            >
                <span x-show="!loading">Send</span>
                <span x-show="loading">●●●</span>
            </button>
        </form>
    </div>
    
    <script>
        function chatApp() {
            return {
                input: '',
                loading: false,
                currentContainer: null,
                segments: [],
                currentSegment: '',
                inCodeBlock: false,
                codeBuffer: '',
                converter: null,
                pendingBuffer: '',

                init() {
                    this.converter = new showdown.Converter({ 
                        tables: true, 
                        strikethrough: true, 
                        emoji: true 
                    });
                },

                async sendMessage() {
                    if (!this.input.trim() || this.loading) return;
                    
                    const msg = this.input;
                    this.input = '';
                    this.loading = true;
                    
                    this.addUserMessage(msg);
                    this.currentContainer = this.createAssistantContainer();
                    this.segments = [];
                    this.currentSegment = '';
                    this.inCodeBlock = false;
                    this.codeBuffer = '';
                    this.pendingBuffer = '';
                    
                    try {
                        const response = await fetch('/chat/{{ session.id }}/stream/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': '{{ csrf_token }}'
                            },
                            body: JSON.stringify({ message: msg })
                        });
                        
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        let buffer = '';
                        
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            buffer += decoder.decode(value, { stream: true });
                            const lines = buffer.split('\n');
                            buffer = lines.pop();
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.substring(6));
                                        if (data.type === 'chunk') {
                                            await this.processChunk(data.content);
                                        } else if (data.type === 'done') {
                                            this.finalizePendingContent();
                                            this.loading = false;
                                        }
                                    } catch (e) {
                                        console.error('Parse error:', e);
                                    }
                                }
                            }
                        }
                    } catch (err) {
                        this.addError('⚠️ Error: ' + err.message);
                        this.loading = false;
                    } finally {
                        this.$nextTick(() => this.$refs.input.focus());
                    }
                },

                async processChunk(text) {
                    this.pendingBuffer += text;
                    const parts = this.pendingBuffer.split('```');
                    
                    if (parts.length === 1) {
                        await this.streamText(text);
                    } else if (parts.length >= 2) {
                        if (!this.inCodeBlock) {
                            await this.streamText(parts[0]);
                            this.finalizePendingContent();
                            this.createCodePlaceholder();
                            this.inCodeBlock = true;
                            this.codeBuffer = '';
                            this.pendingBuffer = parts.slice(1).join('```');
                            
                            if (parts.length > 2) {
                                this.codeBuffer = parts[1];
                                this.finalizeCodeBlock();
                                this.inCodeBlock = false;
                                this.pendingBuffer = parts.slice(2).join('```');
                            }
                        } else {
                            this.codeBuffer += parts[0];
                            this.finalizeCodeBlock();
                            this.inCodeBlock = false;
                            this.pendingBuffer = parts.slice(1).join('```');
                        }
                    }
                },

                async streamText(text) {
                    for (let char of text) {
                        this.currentSegment += char;
                        this.renderCurrentSegment();
                        await new Promise(r => setTimeout(r, 15));
                    }
                },

                renderCurrentSegment() {
                    if (!this.segments.length || this.segments[this.segments.length - 1].type !== 'text') {
                        this.segments.push({
                            type: 'text',
                            content: this.currentSegment,
                            element: this.createTextElement()
                        });
                    } else {
                        this.segments[this.segments.length - 1].content = this.currentSegment;
                        this.segments[this.segments.length - 1].element.innerHTML = this.converter.makeHtml(this.currentSegment);
                    }
                },

                finalizePendingContent() {
                    if (this.currentSegment) {
                        this.segments.push({
                            type: 'text',
                            content: this.currentSegment,
                            element: this.createTextElement()
                        });
                        this.currentSegment = '';
                    }
                },

                createTextElement() {
                    const div = document.createElement('div');
                    div.className = 'streaming-segment markdown-body';
                    this.currentContainer.appendChild(div);
                    this.scrollToBottom();
                    return div;
                },

                createCodePlaceholder() {
                    const div = document.createElement('div');
                    div.className = 'code-generating';
                    div.textContent = '⏳ Generating code...';
                    this.segments.push({
                        type: 'code-placeholder',
                        element: div
                    });
                    this.currentContainer.appendChild(div);
                    this.scrollToBottom();
                },

                finalizeCodeBlock() {
                    const placeholder = this.segments.find(s => s.type === 'code-placeholder');
                    if (placeholder) {
                        const codeDiv = document.createElement('div');
                        codeDiv.className = 'markdown-body';
                        const codeHtml = this.converter.makeHtml('```\n' + this.codeBuffer + '\n```');
                        codeDiv.innerHTML = codeHtml;
                        codeDiv.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
                        placeholder.element.replaceWith(codeDiv);
                        placeholder.type = 'code';
                        placeholder.element = codeDiv;
                        this.codeBuffer = '';
                        this.scrollToBottom();
                    }
                },

                addUserMessage(content) {
                    const div = document.createElement('div');
                    div.className = 'mb-4 text-right';
                    div.innerHTML = `<div class="inline-block px-4 py-2 rounded max-w-2xl bg-blue-500 text-white"><div class="whitespace-pre-wrap text-sm">${this.escapeHtml(content)}</div></div>`;
                    this.$refs.messages.appendChild(div);
                    this.scrollToBottom();
                },

                createAssistantContainer() {
                    const div = document.createElement('div');
                    div.className = 'mb-4 text-left';
                    const inner = document.createElement('div');
                    inner.className = 'inline-block px-4 py-2 rounded max-w-2xl bg-gray-50 border border-gray-200';
                    div.appendChild(inner);
                    this.$refs.messages.appendChild(div);
                    this.scrollToBottom();
                    return inner;
                },

                addError(msg) {
                    const div = document.createElement('div');
                    div.className = 'markdown-body';
                    div.textContent = msg;
                    this.currentContainer.appendChild(div);
                    this.scrollToBottom();
                },

                scrollToBottom() {
                    this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight;
                },

                escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }
            }
        }
    </script>
</body>
</html>