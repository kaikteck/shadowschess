document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatContainer = document.getElementById('chatContainer');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');

    let chatOpen = false;

    // Abrir/fechar chat
    chatButton.addEventListener('click', function(e) {
        e.stopPropagation();
        chatOpen = !chatOpen;
        
        if (chatOpen) {
            chatContainer.classList.add('visible');
            setTimeout(() => {
                chatInput.focus();
            }, 300);
        } else {
            chatContainer.classList.remove('visible');
        }
    });

    closeChatBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        chatOpen = false;
        chatContainer.classList.remove('visible');
    });

    // Limpar chat
    clearChatBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        clearChat();
    });

    // Fechar chat ao clicar fora
    document.addEventListener('click', function(e) {
        if (chatOpen && !chatContainer.contains(e.target) && !chatButton.contains(e.target)) {
            chatOpen = false;
            chatContainer.classList.remove('visible');
        }
    });

    // Prevenir que cliques dentro do chat fechem o modal
    chatContainer.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Enviar mensagem
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Adicionar mensagem do usuário
        addMessage(message, 'user');
        chatInput.value = '';

        // Mostrar indicador de carregamento
        showLoadingIndicator();

        // Enviar para API
        fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoadingIndicator();
            if (data.response) {
                addMessage(data.response, 'bot');
            } else if (data.error) {
                addMessage(`Erro: ${data.error}`, 'bot');
            } else {
                addMessage('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
            }
        })
        .catch(error => {
            hideLoadingIndicator();
            console.error('Erro:', error);
            addMessage('Desculpe, ocorreu um erro de conexão. Verifique sua internet e tente novamente.', 'bot');
        });
    }

    sendButton.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const timestamp = new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-avatar ${sender}">${sender === 'user' ? 'U' : '♔'}</div>
            <div class="message-content">${text}</div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading-message';
        loadingDiv.innerHTML = `
            <div class="message-avatar bot">♔</div>
            <div class="message-content">
                <div class="loading-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideLoadingIndicator() {
        const loadingMessage = chatMessages.querySelector('.loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    function clearChat() {
        // Limpar todas as mensagens
        chatMessages.innerHTML = '';
        
        // Adicionar mensagem inicial novamente
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'message bot';
        welcomeMessage.innerHTML = `
            <div class="message-avatar bot">♔</div>
            <div class="message-content">
                Olá! Eu sou o Rei do Mate, seu assistente de xadrez especializado na estratégia "In the Shadows". Como posso ajudar você hoje?
            </div>
        `;
        chatMessages.appendChild(welcomeMessage);
    }
});