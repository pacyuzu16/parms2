/**
 * PARMS Chatbot Widget
 * Floating chatbot powered by Anthropic Claude API
 * Appears on home, contact, login, and signup pages
 */

(function() {
    const CHATBOT_HTML = `
    <div id="parms-chatbot" class="parms-chatbot" style="display: none;">
        <div class="chatbot-header">
            <div class="chatbot-title">
                <i class="fas fa-comments"></i>
                PARMS Assistant
            </div>
            <button class="chatbot-close" onclick="closeParmsChatbot()" title="Close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="chatbot-messages" id="chatbot-messages">
            <div class="chatbot-message bot-message">
                <div class="message-content">
                    👋 Hi! I'm your PARMS parking assistant. I can help you learn about our smart parking system, answer questions, and get you started. What would you like to know?
                </div>
            </div>
        </div>
        
        <div class="chatbot-input-area">
            <input 
                type="text" 
                id="chatbot-input" 
                class="chatbot-input" 
                placeholder="Ask me anything..." 
                onkeypress="handleChatbotKeypress(event)">
            <button class="chatbot-send" onclick="sendChatbotMessage()" title="Send">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
        
        <div class="chatbot-contact-form" id="chatbot-contact-form" style="display: none;">
            <div class="contact-header">
                <h4>Share Your Details</h4>
                <p>So we can follow up with you</p>
            </div>
            
            <div class="form-group">
                <label>Name</label>
                <input type="text" id="chatbot-contact-name" placeholder="Your name" class="contact-input">
            </div>
            
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="chatbot-contact-email" placeholder="your@email.com" class="contact-input">
            </div>
            
            <div class="form-group">
                <label>Phone (optional)</label>
                <input type="tel" id="chatbot-contact-phone" placeholder="Your phone number" class="contact-input">
            </div>
            
            <div class="form-group">
                <label>Message</label>
                <textarea id="chatbot-contact-message" placeholder="Tell us more..." class="contact-input" rows="3"></textarea>
            </div>
            
            <div class="contact-actions">
                <button class="btn-submit" onclick="submitChatbotContact()">Send Info</button>
                <button class="btn-cancel" onclick="cancelChatbotContact()">Cancel</button>
            </div>
        </div>
    </div>
    
    <button id="parms-chatbot-toggle" class="parms-chatbot-toggle" onclick="toggleParmsChatbot()" title="Chat with us">
        <i class="fas fa-comments"></i>
        <span class="toggle-text">Chat</span>
    </button>
    `;

    const CHATBOT_CSS = `
    <style>
        /* Chatbot Widget Styles */
        .parms-chatbot {
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 380px;
            height: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
            display: flex;
            flex-direction: column;
            z-index: 9998;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            border: 1px solid #dde3e0;
        }

        .chatbot-header {
            background: linear-gradient(135deg, #2c5f47 0%, #1a4a2e 100%);
            color: white;
            padding: 16px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }

        .chatbot-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            font-size: 1rem;
        }

        .chatbot-title i {
            font-size: 1.2rem;
        }

        .chatbot-close {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 1.2rem;
            padding: 4px 8px;
            border-radius: 6px;
            transition: background 0.2s;
        }

        .chatbot-close:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .chatbot-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: #f7f8f7;
        }

        .chatbot-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chatbot-messages::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        .chatbot-messages::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 3px;
        }

        .chatbot-message {
            display: flex;
            margin-bottom: 8px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .user-message {
            justify-content: flex-end;
        }

        .bot-message {
            justify-content: flex-start;
        }

        .message-content {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.95rem;
            line-height: 1.4;
            word-wrap: break-word;
        }

        .user-message .message-content {
            background: #2c5f47;
            color: white;
            border-radius: 12px 0 12px 12px;
        }

        .bot-message .message-content {
            background: white;
            color: #161b19;
            border: 1px solid #dde3e0;
            border-radius: 0 12px 12px 12px;
        }

        .message-loading {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ccc;
            animation: typing 1.4s infinite;
        }

        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                opacity: 0.3;
            }
            30% {
                opacity: 1;
            }
        }

        .chatbot-input-area {
            display: flex;
            gap: 8px;
            padding: 12px;
            background: white;
            border-top: 1px solid #dde3e0;
            border-radius: 0 0 12px 12px;
            flex-shrink: 0;
        }

        .chatbot-input {
            flex: 1;
            border: 1px solid #dde3e0;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 0.9rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }

        .chatbot-input:focus {
            border-color: #2c5f47;
            box-shadow: 0 0 0 3px rgba(44, 95, 71, 0.1);
        }

        .chatbot-send {
            background: #2c5f47;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .chatbot-send:hover {
            background: #1a4a2e;
        }

        .chatbot-send:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        /* Contact Form */
        .chatbot-contact-form {
            padding: 16px;
            border-top: 1px solid #dde3e0;
            overflow-y: auto;
            background: white;
        }

        .contact-header {
            margin-bottom: 16px;
        }

        .contact-header h4 {
            margin: 0 0 4px 0;
            font-size: 1rem;
            color: #161b19;
        }

        .contact-header p {
            margin: 0;
            font-size: 0.85rem;
            color: #4f5a55;
        }

        .form-group {
            margin-bottom: 12px;
        }

        .form-group label {
            display: block;
            margin-bottom: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #161b19;
        }

        .contact-input {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid #dde3e0;
            border-radius: 6px;
            font-size: 0.9rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
            box-sizing: border-box;
        }

        .contact-input:focus {
            border-color: #2c5f47;
            box-shadow: 0 0 0 3px rgba(44, 95, 71, 0.1);
        }

        .contact-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .btn-submit,
        .btn-cancel {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-submit {
            background: #2c5f47;
            color: white;
        }

        .btn-submit:hover {
            background: #1a4a2e;
        }

        .btn-cancel {
            background: #f0f0f0;
            color: #161b19;
        }

        .btn-cancel:hover {
            background: #e0e0e0;
        }

        /* Toggle Button */
        .parms-chatbot-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #2c5f47;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(44, 95, 71, 0.3);
            transition: all 0.3s;
            z-index: 9999;
        }

        .parms-chatbot-toggle:hover {
            background: #1a4a2e;
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(44, 95, 71, 0.4);
        }

        .toggle-text {
            font-size: 0.75rem;
            font-weight: 600;
            display: none;
        }

        /* Responsive */
        @media (max-width: 600px) {
            .parms-chatbot {
                width: calc(100vw - 40px);
                height: calc(100vh - 120px);
                left: 20px;
                right: 20px;
                bottom: 90px;
            }

            .toggle-text {
                display: inline;
            }
        }
    </style>
    `;

    // Initialize chatbot on page load
    function initParmsChatbot() {
        // Only show on specific pages
        const pathname = window.location.pathname;
        const allowedPages = ['/', '/contact/', '/login/', '/signup/', '/about/'];
        const isAllowed = allowedPages.some(page => pathname === page || pathname.startsWith(page));
        
        if (!isAllowed) return;

        // Inject CSS
        const styleTag = document.createElement('style');
        styleTag.innerHTML = CHATBOT_CSS.replace(/<style>|<\/style>/g, '');
        document.head.appendChild(styleTag);

        // Inject HTML
        const container = document.createElement('div');
        container.innerHTML = CHATBOT_HTML;
        document.body.appendChild(container);

        // Store conversation history
        window.chatbotConversation = [
            {
                role: 'assistant',
                content: "👋 Hi! I'm your PARMS parking assistant. I can help you learn about our smart parking system, answer questions, and get you started. What would you like to know?"
            }
        ];
    }

    // Global functions
    window.toggleParmsChatbot = function() {
        const chatbot = document.getElementById('parms-chatbot');
        const toggle = document.getElementById('parms-chatbot-toggle');
        if (chatbot.style.display === 'none') {
            chatbot.style.display = 'flex';
            toggle.style.opacity = '0.5';
        } else {
            chatbot.style.display = 'none';
            toggle.style.opacity = '1';
        }
    };

    window.closeParmsChatbot = function() {
        document.getElementById('parms-chatbot').style.display = 'none';
        document.getElementById('parms-chatbot-toggle').style.opacity = '1';
    };

    window.handleChatbotKeypress = function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendChatbotMessage();
        }
    };

    window.sendChatbotMessage = function() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to UI
        addChatbotMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        const messagesDiv = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message message-loading';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messagesDiv.appendChild(typingDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Send to API
        fetch('/api/chatbot/message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            typingDiv.remove();
            if (data.success) {
                const botMessage = data.message;
                addChatbotMessage(botMessage, 'bot');
                
                // Check if bot suggests collecting contact info
                if (shouldShowContactForm(botMessage)) {
                    setTimeout(() => showChatbotContactForm(), 800);
                }
            } else {
                addChatbotMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        })
        .catch(error => {
            typingDiv.remove();
            console.error('Chatbot error:', error);
            addChatbotMessage('Sorry, there was a connection error. Please try again.', 'bot');
        });
    };

    window.addChatbotMessage = function(content, sender) {
        const messagesDiv = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        messageDiv.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    };

    window.shouldShowContactForm = function(botMessage) {
        const keywords = ['contact info', 'email', 'phone', 'interested', 'follow up', 'reach out', 'share your'];
        return keywords.some(keyword => botMessage.toLowerCase().includes(keyword));
    };

    window.showChatbotContactForm = function() {
        const form = document.getElementById('chatbot-contact-form');
        form.style.display = 'block';
    };

    window.cancelChatbotContact = function() {
        const form = document.getElementById('chatbot-contact-form');
        form.style.display = 'none';
    };

    window.submitChatbotContact = function() {
        const name = document.getElementById('chatbot-contact-name').value.trim();
        const email = document.getElementById('chatbot-contact-email').value.trim();
        const phone = document.getElementById('chatbot-contact-phone').value.trim();
        const message = document.getElementById('chatbot-contact-message').value.trim();

        if (!name || !email) {
            alert('Please provide at least name and email');
            return;
        }

        fetch('/api/chatbot/contact-submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                name: name,
                email: email,
                phone: phone,
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('chatbot-contact-form').style.display = 'none';
                addChatbotMessage('✅ Thank you! We received your contact info and will reach out soon.', 'bot');
                
                // Reset form
                document.getElementById('chatbot-contact-name').value = '';
                document.getElementById('chatbot-contact-email').value = '';
                document.getElementById('chatbot-contact-phone').value = '';
                document.getElementById('chatbot-contact-message').value = '';
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Submit error:', error);
            alert('Error submitting contact info');
        });
    };

    window.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    window.escapeHtml = function(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initParmsChatbot);
    } else {
        initParmsChatbot();
    }
})();
