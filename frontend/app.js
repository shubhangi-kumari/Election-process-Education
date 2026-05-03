document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    const toggleText = document.querySelector('.toggle-text');
    const suggestionItems = document.querySelectorAll('.info-section li');

    // Theme Toggle Logic
    const initTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.body.setAttribute('data-theme', 'dark');
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
            toggleText.textContent = 'Light Mode';
        }
    };

    themeToggle.addEventListener('click', () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
            toggleText.textContent = 'Dark Mode';
        } else {
            document.body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
            toggleText.textContent = 'Light Mode';
        }
    });

    initTheme();

    // Suggestion Click Logic
    suggestionItems.forEach(item => {
        item.addEventListener('click', () => {
            const text = item.textContent.replace(/"/g, ''); // Remove quotes
            userInput.value = text;
            userInput.focus();
        });
    });

    // Formatting helper (very basic markdown for links and bold)
    const formatText = (text) => {
        // Simple bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Simple line breaks
        text = text.replace(/\n/g, '<br>');
        return text;
    };

    const addMessage = (content, isUser = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = isUser ? 'U' : 'AI';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser) {
            const p = document.createElement('p');
            p.textContent = content;
            messageContent.appendChild(p);
        } else {
            messageContent.innerHTML = formatText(content);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const showTypingIndicator = () => {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message assistant-message typing-container';
        indicatorDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = 'AI';

        const content = document.createElement('div');
        content.className = 'message-content';
        
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        content.appendChild(typing);
        indicatorDiv.appendChild(avatar);
        indicatorDiv.appendChild(content);
        
        chatMessages.appendChild(indicatorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    };

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        
        if (!message) return;

        // Disable input while processing
        userInput.value = '';
        userInput.disabled = true;
        sendButton.disabled = true;

        addMessage(message, true);
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            removeTypingIndicator();
            addMessage(data.reply);

        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage("I'm sorry, I couldn't connect to the server. Please make sure the backend is running and try again.");
        } finally {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    });
});
