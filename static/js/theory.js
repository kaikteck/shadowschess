// Theory page functionality with localStorage
document.addEventListener('DOMContentLoaded', function() {
    initializeTheoryPage();
});

function initializeTheoryPage() {
    setupTheoryForm();
    displaySavedIdeas();
    loadTextareaContent();
}

function loadTextareaContent() {
    const textarea = document.getElementById('teoria_content');
    if (textarea) {
        const savedContent = localStorage.getItem('current_theory_text');
        if (savedContent) {
            textarea.value = savedContent;
        }
    }
}

function saveTextareaContent() {
    const textarea = document.getElementById('teoria_content');
    if (textarea) {
        localStorage.setItem('current_theory_text', textarea.value);
    }
}



function saveTheory() {
    const textarea = document.getElementById('teoria_content');
    if (textarea) {
        const content = textarea.value.trim();
        if (content === '') {
            showFlashMessage('Escreva algo antes de salvar!', 'error');
            return false;
        }
        
        // Salvar ideia na lista
        const ideas = getSavedIdeas();
        const newIdea = {
            id: Date.now().toString(),
            content: content,
            date: new Date().toISOString()
        };
        
        ideas.unshift(newIdea);
        localStorage.setItem('saved_ideas', JSON.stringify(ideas));
        
        // Salvar conteúdo atual do textarea
        saveTextareaContent();
        
        // Atualizar display
        displaySavedIdeas();
        showFlashMessage('Ideia salva com sucesso!', 'success');
        return true;
    }
    return false;
}

function getSavedIdeas() {
    const saved = localStorage.getItem('saved_ideas');
    return saved ? JSON.parse(saved) : [];
}

function displaySavedIdeas() {
    const ideas = getSavedIdeas();
    const ideasList = document.getElementById('ideas-list');
    const noIdeas = document.getElementById('no-ideas');
    
    if (ideas.length === 0) {
        ideasList.innerHTML = '';
        noIdeas.style.display = 'block';
    } else {
        noIdeas.style.display = 'none';
        ideasList.innerHTML = ideas.map(createIdeaHTML).join('');
        
        // Adicionar event listeners para deletar
        ideas.forEach(idea => {
            const deleteBtn = document.querySelector(`[data-idea-id="${idea.id}"]`);
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => deleteIdea(idea.id));
            }
        });
    }
}

function createIdeaHTML(idea) {
    const date = new Date(idea.date);
    const formattedDate = date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
    
    return `
        <div class="idea-item">
            <div class="idea-content">${escapeHtml(idea.content)}</div>
            <div class="idea-footer">
                <span class="idea-date">${formattedDate}</span>
                <button class="delete-idea-btn" data-idea-id="${idea.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}

function deleteIdea(ideaId) {
    // Criar confirmação customizada no site com design do tema
    const confirmDiv = document.createElement('div');
    confirmDiv.className = 'delete-confirm-overlay';
    confirmDiv.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(5px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease;
    `;
    
    confirmDiv.innerHTML = `
        <div class="delete-confirm-modal" style="
            background: linear-gradient(135deg, #3a3a3a 0%, #2d2d2d 100%);
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            max-width: 350px;
            width: 90%;
            box-shadow: 0 15px 40px rgba(220, 53, 69, 0.4);
            color: #e0e0e0;
            animation: slideIn 0.3s ease;
        ">
            <div style="margin-bottom: 15px;">
                <i class="fas fa-exclamation-triangle" style="
                    font-size: 36px;
                    color: #dc3545;
                    margin-bottom: 10px;
                "></i>
                <h3 style="
                    margin: 0;
                    color: #dc3545;
                    font-weight: 700;
                    font-size: 1.2rem;
                ">Confirmar Exclusão</h3>
            </div>
            <p style="
                color: #e0e0e0;
                margin: 15px 0;
                font-size: 1rem;
                line-height: 1.4;
            ">Tem certeza que deseja apagar esta ideia?</p>
            <div style="margin-top: 20px; display: flex; gap: 12px; justify-content: center;">
                <button class="confirm-delete-btn" style="
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(220, 53, 69, 0.3);
                ">
                    <i class="fas fa-trash"></i> Sim, apagar
                </button>
                <button class="cancel-delete-btn" style="
                    background: rgba(108, 117, 125, 0.2);
                    color: #e0e0e0;
                    border: 2px solid rgba(108, 117, 125, 0.5);
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                ">
                    <i class="fas fa-times"></i> Cancelar
                </button>
            </div>
        </div>
        <style>
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideIn {
                from { transform: scale(0.8) translateY(-20px); opacity: 0; }
                to { transform: scale(1) translateY(0); opacity: 1; }
            }
            .confirm-delete-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4) !important;
            }
            .cancel-delete-btn:hover {
                background: rgba(108, 117, 125, 0.3) !important;
                border-color: rgba(108, 117, 125, 0.8) !important;
                transform: translateY(-2px);
            }
        </style>
    `;
    
    document.body.appendChild(confirmDiv);
    
    // Função para remover o modal
    function removeModal() {
        try {
            if (confirmDiv && document.body.contains(confirmDiv)) {
                confirmDiv.style.animation = 'fadeOut 0.2s ease';
                setTimeout(() => {
                    try {
                        if (confirmDiv && document.body.contains(confirmDiv)) {
                            document.body.removeChild(confirmDiv);
                        }
                    } catch (error) {
                        console.log('Modal já foi removido');
                    }
                }, 200);
            }
        } catch (error) {
            console.log('Erro ao remover modal:', error);
        }
    }
    
    // Esperar o modal ser adicionado ao DOM antes de configurar eventos
    setTimeout(() => {
        // Adicionar eventos
        const confirmBtn = confirmDiv.querySelector('.confirm-delete-btn');
        const cancelBtn = confirmDiv.querySelector('.cancel-delete-btn');
        
        if (confirmBtn) {
            confirmBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const ideas = getSavedIdeas();
                    const filteredIdeas = ideas.filter(idea => idea.id !== ideaId);
                    localStorage.setItem('saved_ideas', JSON.stringify(filteredIdeas));
                    displaySavedIdeas();
                    showFlashMessage('Ideia removida com sucesso!', 'info');
                    removeModal();
                } catch (error) {
                    console.log('Erro ao deletar ideia:', error);
                    removeModal();
                }
            };
        }
        
        if (cancelBtn) {
            cancelBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                removeModal();
            };
        }
    }, 50);
    
    // Fechar ao clicar fora do modal
    confirmDiv.onclick = function(e) {
        if (e.target === confirmDiv) {
            removeModal();
        }
    };
    
    // Fechar com ESC
    const escHandler = function(e) {
        if (e.key === 'Escape') {
            removeModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setupTheoryForm() {
    const saveButton = document.getElementById('save-theory');
    const textarea = document.getElementById('teoria_content');
    
    if (saveButton) {
        saveButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            saveTheory();
            return false;
        });
    }
    
    // Salvar automaticamente o conteúdo do textarea enquanto digita
    if (textarea) {
        let saveTimer;
        textarea.addEventListener('input', function() {
            clearTimeout(saveTimer);
            saveTimer = setTimeout(() => {
                saveTextareaContent();
            }, 1000); // Salva 1 segundo após parar de digitar
        });
    }
}

function setupAutoSave() {
    // Removido auto-save - salvamento apenas manual
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('teoria_content');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initial resize
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }
});