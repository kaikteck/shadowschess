// Examples page functionality with localStorage
document.addEventListener('DOMContentLoaded', function() {
    initializeExamplesPage();
});

function initializeExamplesPage() {
    setupDeleteListeners();
    setupExampleForm();
}

function loadExamples() {
    // Para páginas Flask server-side, não precisamos carregar exemplos
    // eles já são renderizados no HTML
    setupDeleteListeners();
}

function getStoredExamples() {
    const stored = localStorage.getItem('chess_examples');
    return stored ? JSON.parse(stored) : [];
}

function saveExamples(examples) {
    localStorage.setItem('chess_examples', JSON.stringify(examples));
}

function addExample(exemplo) {
    const examples = getStoredExamples();
    
    // Add timestamp and ID
    exemplo.id = Date.now().toString();
    exemplo.created_at = new Date().toISOString();
    
    examples.unshift(exemplo); // Add to beginning
    saveExamples(examples);
    
    displayExamples(examples);
    showFlashMessage('Exemplo adicionado com sucesso!', 'success');
}

function deleteExample(id) {
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
            ">Tem certeza que deseja apagar este exemplo?</p>
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
                    // Fazer requisição ao servidor para deletar o exemplo
                    const deleteUrl = `/delete_exemplo/${id}`;
                    fetch(deleteUrl, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => {
                        if (response.ok) {
                            // Recarregar a página para mostrar os exemplos atualizados
                            window.location.reload();
                        } else {
                            throw new Error('Erro ao deletar exemplo');
                        }
                    })
                    .catch(error => {
                        console.error('Erro ao deletar exemplo:', error);
                        showFlashMessage('Erro ao remover exemplo', 'error');
                        removeModal();
                    });
                } catch (error) {
                    console.log('Erro ao deletar exemplo:', error);
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

function displayExamples(examples) {
    // Para a página Flask, não precisamos gerenciar a exibição de exemplos
    // pois os exemplos são renderizados server-side
    // Apenas configuramos os event listeners para botões de deletar existentes
    setupDeleteListeners();
}

function setupDeleteListeners() {
    // Configurar event listeners para todos os botões de deletar na página
    const deleteButtons = document.querySelectorAll('[data-delete-id]');
    deleteButtons.forEach(deleteBtn => {
        // Remove event listeners anteriores para evitar duplicação
        const newBtn = deleteBtn.cloneNode(true);
        deleteBtn.parentNode.replaceChild(newBtn, deleteBtn);
        
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const deleteId = newBtn.getAttribute('data-delete-id');
            if (deleteId) {
                deleteExample(deleteId);
            }
        });
    });
}

function createExampleCard(exemplo) {
    const date = new Date(exemplo.created_at);
    const formattedDate = date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
    
    return `
        <div class="example-card">
            <div class="example-header">
                <h3>${escapeHtml(exemplo.nome)}</h3>
                <a href="#" class="delete-btn" data-delete-id="${exemplo.id}">
                    <i class="fas fa-trash"></i>
                </a>
            </div>
            
            <div class="example-content">
                <div class="example-field">
                    <strong><i class="fas fa-chess-board"></i> Situação:</strong>
                    <p>${escapeHtml(exemplo.situacao)}</p>
                </div>
                
                <div class="example-field">
                    <strong><i class="fas fa-eye-slash"></i> Peça nas Sombras:</strong>
                    <p>${escapeHtml(exemplo.peca_sombra)}</p>
                </div>
                
                <div class="example-field">
                    <strong><i class="fas fa-crown"></i> Resultado:</strong>
                    <p>${escapeHtml(exemplo.resultado)}</p>
                </div>
            </div>
            
            <div class="example-footer">
                <small><i class="fas fa-calendar"></i> ${formattedDate}</small>
            </div>
        </div>
    `;
}

function setupExampleForm() {
    const form = document.getElementById('example-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const exemplo = {
                nome: formData.get('nome').trim(),
                situacao: formData.get('situacao').trim(),
                peca_sombra: formData.get('peca_sombra').trim(),
                resultado: formData.get('resultado').trim()
            };
            
            // Validate
            if (!exemplo.nome || !exemplo.situacao || !exemplo.peca_sombra || !exemplo.resultado) {
                showFlashMessage('Por favor, preencha todos os campos.', 'danger');
                return;
            }
            
            addExample(exemplo);
            form.reset();
            
            // Auto-resize textareas after reset
            const textareas = form.querySelectorAll('textarea');
            textareas.forEach(textarea => {
                textarea.style.height = 'auto';
            });
        });
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Auto-resize textareas
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
});