// Adicionar ao final do arquivo web/static/script.js

// Estender a classe ChatInterface existente
class ChatInterface {
    constructor() {
        console.log('ChatInterface constructor called');
        // ... código existente ...
        this.chatForm = document.getElementById('chatForm'); // Adicionado do código existente
        this.messageInput = document.getElementById('messageInput'); // Adicionado do código existente
        this.sendButton = document.getElementById('sendButton'); // Adicionado do código existente
        this.chatMessages = document.getElementById('chatMessages'); // Adicionado do código existente
        this.loadingIndicator = document.getElementById('loadingIndicator'); // Adicionado do código existente
        this.statusIndicator = document.getElementById('statusIndicator'); // Adicionado do código existente
        this.statusText = document.getElementById('statusText'); // Adicionado do código existente
        this.agentInfo = document.getElementById('agentInfo'); // Adicionado do código existente

        this.agentSelect = document.getElementById('agentSelect');
        this.switchAgentBtn = document.getElementById('switchAgentBtn');
        this.agentInfoBar = document.getElementById('agentInfoBar');
        this.currentAgentName = document.getElementById('currentAgentName');
        this.currentAgentDescription = document.getElementById('currentAgentDescription');
        this.agentsInfo = document.getElementById('agentsInfo');
        
        this.init();
    }
    
    init() {
        console.log('ChatInterface init called');
        // ... código existente ...
        // Event listeners do código existente
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e)); // Adicionado do código existente
        this.messageInput.addEventListener('keypress', (e) => { // Adicionado do código existente
            if (e.key === 'Enter' && !e.shiftKey) { // Adicionado do código existente
                e.preventDefault(); // Adicionado do código existente
                this.handleSubmit(e); // Adicionado do código existente
            } // Adicionado do código existente
        }); // Adicionado do código existente
        // Check initial status do código existente
        this.checkStatus(); // Adicionado do código existente
        // Focus input do código existente
        this.messageInput.focus(); // Adicionado do código existente

        // Event listeners para troca de agente
        this.switchAgentBtn.addEventListener('click', () => this.switchAgent());
        this.agentSelect.addEventListener('change', () => this.switchAgent());
        
        // Carregar informações dos agentes
        this.loadAgentsInfo();
        
    }

    async checkStatus() {
        console.log('ChatInterface checkStatus called');
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            if (data.agent_manager_available && data.api_keys_status.google_api_key && data.api_keys_status.openai_api_key && data.api_keys_status.tavily_api_key) {
                this.setStatus('online', 'Agentes Online');
            } else {
                 let statusText = 'Agentes Offline';
                 const missing = [];
                 if (!data.agent_manager_available) missing.push('Gerenciador');
                 if (!data.api_keys_status.google_api_key) missing.push('Google API Key');
                 if (!data.api_keys_status.openai_api_key) missing.push('OpenAI API Key');
                 if (!data.api_keys_status.tavily_api_key) missing.push('Tavily API Key');
                 if (missing.length > 0) {
                     statusText += `: ${missing.join(', ')}`;
                 }
                this.setStatus('offline', statusText);
            }
        } catch (error) {
            console.error('Erro ao verificar status:', error);
            this.setStatus('offline', 'Erro de Conexão');
        }
    }
    
    async loadAgentsInfo() {
        console.log('ChatInterface loadAgentsInfo called');
        try {
            const response = await fetch('/api/agents-info');
            const data = await response.json();
            
            if (data.available) {
                this.updateAgentInfo(data);
                this.displayAgentsComparison(data);
            } else {
                this.agentsInfo.innerHTML = 'Informações dos agentes não disponíveis';
            }
        } catch (error) {
            console.error('Erro ao carregar informações dos agentes:', error);
            this.agentsInfo.innerHTML = 'Erro ao carregar informações';
        }
    }
    
    async switchAgent() {
        const selectedAgent = this.agentSelect.value;
        console.log(`Attempting to switch agent to: ${selectedAgent}`); // Added logging
        
        try {
            this.switchAgentBtn.disabled = true;
            this.switchAgentBtn.innerHTML = '';
            
            const formData = new FormData();
            formData.append('agent_type', selectedAgent);
            
            const response = await fetch('/switch-agent', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`Agent switched successfully to ${data.current_agent}`); // Added logging
                this.updateAgentInfo(data.agent_info);
                this.addSystemMessage(`Agente alterado para ${selectedAgent.toUpperCase()}`);
            } else {
                console.error(`Failed to switch agent: ${data.error}`); // Added logging
                this.addSystemMessage(`Erro ao trocar agente: ${data.error}`, true);
            }
            
        } catch (error) {
            console.error('Erro ao trocar agente:', error);
            this.addSystemMessage('Erro ao trocar agente. Tente novamente.', true);
        } finally {
            this.switchAgentBtn.disabled = false;
            this.switchAgentBtn.innerHTML = '';
        }
    }
    
    // Atualizar o método addMessage para mostrar qual agente respondeu
    addMessage(content, sender, isError = false, agentInfo = null) {
        console.log(`Adding message from ${sender}. Error: ${isError}`); // Added logging
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message${isError ? ' error-message' : ''}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '' : '';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('p');
        messageText.innerHTML = this.formatMessage(content);
        
        const messageTime = document.createElement('small');
        messageTime.className = 'message-time';
        
        let timeText = new Date().toLocaleTimeString();
        if (sender === 'bot' && agentInfo) {
            timeText += ` -  ${agentInfo.agent_name}`;
        }
        messageTime.textContent = timeText;
        
        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        
        if (sender === 'user') {
            messageDiv.appendChild(messageContent);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    // Atualizar o método handleSubmit para passar informações do agente
    async handleSubmit(e) {
        e.preventDefault();
        console.log('handleSubmit called'); // Added logging
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage(message, 'user');
        
        // Clear input and disable form
        this.messageInput.value = '';
        this.setLoading(true);
        
        try {
            const response = await this.sendMessage(message);
            
            if (response.success) {
                console.log('Message sent successfully. Adding bot response.'); // Added logging
                this.addMessage(response.response, 'bot', false, {
                    agent_name: response.agent_name,
                    agent_type: response.agent
                });
            } else {
                console.error(`Message sending failed: ${response.error}`); // Added logging
                this.addMessage(`Erro: ${response.error}`, 'bot', true);
            }
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            this.addMessage('Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.', 'bot', true);
        } finally {
            this.setLoading(false);
            this.messageInput.focus();
        }
    }

    async sendMessage(message) {
        console.log(`sendMessage called with query: ${message.substring(0, 50)}...`); // Added logging
        const formData = new FormData();
        formData.append('query', message);
        
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    formatMessage(content) {
        // Simple formatting for better readability
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Corrected bold formatting
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Corrected italic formatting
            .replace(/\n/g, '<br>'); // Corrected newline formatting
    }
    
    setLoading(loading) {
        console.log(`setLoading called with: ${loading}`); // Added logging
        if (loading) {
            this.loadingIndicator.style.display = 'flex';
            this.sendButton.disabled = true;
            this.messageInput.disabled = true;
        } else {
            this.loadingIndicator.style.display = 'none';
            this.sendButton.disabled = false;
            this.messageInput.disabled = false;
        }
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        console.log('scrollToBottom called'); // Added logging
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    setStatus(status, text) {
        console.log(`setStatus called with status: ${status}, text: ${text}`); // Added logging
        this.statusIndicator.className = `status-indicator ${status}`;
        this.statusText.textContent = text;
    }
    
    updateAgentInfo(agentInfo) {
        console.log('updateAgentInfo called', agentInfo); // Added logging
        // Atualizar o seletor
        this.agentSelect.value = agentInfo.current_agent;
        
        // Atualizar a barra de informações
        const currentAgent = agentInfo.current_agent;
        const agentStatus = agentInfo.agents_status[currentAgent];
        
        if (agentStatus) {
            this.currentAgentName.textContent = agentStatus.name;
            this.currentAgentDescription.textContent = agentStatus.description;
        }
    }
    
    displayAgentsComparison(agentInfo) {
        console.log('displayAgentsComparison called', agentInfo); // Added logging
        const agentsHtml = Object.entries(agentInfo.agents_status).map(([type, info]) => {
            const isActive = type === agentInfo.current_agent;
            const statusClass = info.available ? 'online' : 'offline';
            const statusText = info.available ? 'Online' : 'Offline';
            
            return `
                
                    
                        ${info.name}
                        ${statusText}
                    
                    ${info.description}
                    ${isActive ? '🟢 Agente Ativo' : ''}
                
            `;
        }).join('');
        
        this.agentsInfo.innerHTML = `
            
                ${agentsHtml}
            
        `;
    }

    addSystemMessage(message, isError = false) {
        console.log(`Adding system message: ${message}. Error: ${isError}`); // Added logging
        const messageDiv = document.createElement('div');
        messageDiv.className = `message system-message${isError ? ' error-message' : ''}`;
        
        messageDiv.innerHTML = `
            
                
            
            
                ${message}
                ${new Date().toLocaleTimeString()}
            
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded. Initializing ChatInterface.'); // Added logging
    new ChatInterface();
});
// Função para alternar o painel de conhecimento
function toggleKnowledgePanel() {
    const panel = document.getElementById('knowledgePanel');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
    } else {
        panel.style.display = 'none';
    }
}

// Adicione ao método init() da classe ChatInterface
// init() {
//     // ... código existente ...

//     // Event listener para formulário de conhecimento
//     const knowledgeForm = document.getElementById('knowledgeForm');
//     if (knowledgeForm) {
//         knowledgeForm.addEventListener('submit', (e) => this.handleKnowledgeSubmit(e));
//     }
// }

// Método para lidar com adição de conhecimento
async function handleKnowledgeSubmit(e) {
    e.preventDefault();

    const content = document.getElementById('knowledgeContent').value.trim();
    const source = document.getElementById('knowledgeSource').value.trim() || 'usuário';

    if (!content) return;

    try {
        const formData = new FormData();
        formData.append('content', content);
        formData.append('source', source);
        formData.append('user_id', this.getCurrentUserId());

        const response = await fetch('/add-knowledge', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            this.addSystemMessage(`✅ Conhecimento adicionado: ${data.content_preview}`);
            document.getElementById('knowledgeContent').value = '';
            toggleKnowledgePanel();
        } else {
            this.addSystemMessage(`❌ Erro: ${data.error}`, true);
        }

    } catch (error) {
        console.error('Erro ao adicionar conhecimento:', error);
        this.addSystemMessage('❌ Erro ao adicionar conhecimento. Tente novamente.', true);
    }
}

// Método para obter ID do usuário atual
function getCurrentUserId() {
    return localStorage.getItem('user_id') || 'web_user_' + Math.random().toString(36).substr(2, 9);
}

// Adicionar event listener para o botão de conhecimento
document.addEventListener('DOMContentLoaded', () => {
    const knowledgeButton = document.getElementById('toggleKnowledgePanelBtn');
    if (knowledgeButton) {
        knowledgeButton.addEventListener('click', toggleKnowledgePanel);
    }

    // Adicionar event listener para o botão de cancelar no painel de conhecimento
    const cancelKnowledgeButton = document.getElementById('cancelKnowledgeBtn');
    if (cancelKnowledgeButton) {
        cancelKnowledgeButton.addEventListener('click', toggleKnowledgePanel);
    }

    // Adicionar event listener para o formulário de conhecimento
    const knowledgeForm = document.getElementById('knowledgeForm');
    if (knowledgeForm) {
        // Bind the method to the ChatInterface instance if needed, or pass 'this'
        // For simplicity, assuming handleKnowledgeSubmit is a standalone function or will be bound later
        knowledgeForm.addEventListener('submit', handleKnowledgeSubmit);
    }

    // Ensure ChatInterface instance is available if needed in handleKnowledgeSubmit
    // This might require passing the instance or making methods static/global
});