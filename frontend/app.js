/**
 * @fileoverview Main application logic for the Election Process Assistant.
 * Implements strict mode, DOMPurify for XSS protection, and modular UI functions.
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    const toggleText = document.querySelector('.toggle-text');
    const suggestionItems = document.querySelectorAll('.info-section li');

    // --- Theme Management ---
    /**
     * Initializes the theme based on localStorage or system preferences.
     */
    const initTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            setTheme('dark');
        } else {
            setTheme('light');
        }
    };

    /**
     * Sets the application theme and updates UI icons.
     * @param {string} theme - 'dark' or 'light'
     */
    const setTheme = (theme) => {
        if (theme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            if (sunIcon && moonIcon && toggleText) {
                sunIcon.style.display = 'block';
                moonIcon.style.display = 'none';
                toggleText.textContent = 'Light Mode';
            }
        } else {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            if (sunIcon && moonIcon && toggleText) {
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'block';
                toggleText.textContent = 'Dark Mode';
            }
        }
    };

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = document.body.getAttribute('data-theme') === 'dark';
            setTheme(isDark ? 'light' : 'dark');
        });
    }

    initTheme();

    // --- UI Interactions ---
    suggestionItems.forEach(item => {
        item.addEventListener('click', () => {
            const text = item.textContent.replace(/"/g, ''); 
            if (userInput) {
                userInput.value = text;
                userInput.focus();
            }
        });
        
        // Keyboard accessibility for suggestions
        item.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                item.click();
            }
        });
    });

    // --- Message Handling ---
    /**
     * Formats raw text into basic HTML securely.
     * @param {string} text - The raw text from the AI.
     * @returns {string} - Sanitized HTML string.
     */
    const formatTextSecurely = (text) => {
        // Simple markdown parsing
        let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Handle links
        formatted = formatted.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Sanitize output to prevent XSS
        // Depends on DOMPurify included in index.html
        if (window.DOMPurify) {
            return window.DOMPurify.sanitize(formatted, { ALLOWED_TAGS: ['b', 'strong', 'i', 'em', 'br', 'a'], ALLOWED_ATTR: ['href', 'target', 'rel'] });
        }
        // Fallback if DOMPurify fails to load (very restrictive)
        return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
    };

    /**
     * Appends a message to the chat interface.
     * @param {string} content - The message content.
     * @param {boolean} [isUser=false] - Whether the message is from the user.
     */
    const addMessage = (content, isUser = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.setAttribute('aria-hidden', 'true');
        avatar.textContent = isUser ? 'U' : 'AI';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser) {
            const p = document.createElement('p');
            p.textContent = content; // Safe from XSS
            messageContent.appendChild(p);
        } else {
            messageContent.innerHTML = formatTextSecurely(content); // Sanitized
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    /**
     * Displays a typing indicator.
     */
    const showTypingIndicator = () => {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message assistant-message typing-container';
        indicatorDiv.id = 'typing-indicator';
        indicatorDiv.setAttribute('aria-live', 'assertive');
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.setAttribute('aria-hidden', 'true');
        avatar.textContent = 'AI';

        const content = document.createElement('div');
        content.className = 'message-content';
        
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        // Hidden text for screen readers
        const srText = document.createElement('span');
        srText.className = 'sr-only';
        srText.textContent = 'Assistant is typing...';
        srText.style.position = 'absolute';
        srText.style.width = '1px';
        srText.style.height = '1px';
        srText.style.overflow = 'hidden';
        
        content.appendChild(typing);
        content.appendChild(srText);
        indicatorDiv.appendChild(avatar);
        indicatorDiv.appendChild(content);
        
        chatMessages.appendChild(indicatorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    /**
     * Removes the typing indicator.
     */
    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    };

    // --- Form Submission ---
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            
            if (!message) return;

            // UI State updates
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

                if (response.status === 429) {
                    throw new Error('Rate limit exceeded. Please wait a moment.');
                }

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();
                removeTypingIndicator();
                addMessage(data.reply);

            } catch (error) {
                console.error('Error:', error);
                removeTypingIndicator();
                addMessage(error.message || "I'm sorry, I couldn't connect to the server. Please make sure the backend is running and try again.");
            } finally {
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
            }
        });
    }
});
