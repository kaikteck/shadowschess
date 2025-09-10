// Main JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tab functionality
    initializeTabs();
    
    // Initialize form enhancements
    initializeForms();
    
    // Initialize navigation highlighting
    highlightCurrentPage();
});

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all buttons and panels
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));
            
            // Add active class to clicked button and corresponding panel
            this.classList.add('active');
            const targetPanel = document.getElementById(targetTab);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

function initializeForms() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Initial resize
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });
    
    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#dc3545';
                    isValid = false;
                } else {
                    field.style.borderColor = '#444';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Por favor, preencha todos os campos obrigatórios.', 'error');
            }
        });
    });
}

function highlightCurrentPage() {
    // This functionality is now handled by navigation.js
    // Keep function for compatibility but delegate to navigation.js
    if (typeof setActiveNavLink === 'function') {
        setActiveNavLink();
    }
}

function showNotification(message, type = 'info') {
    // Use the flash message system from navigation.js
    if (typeof showFlashMessage === 'function') {
        showFlashMessage(message, type);
    } else {
        // Fallback notification system
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-info-circle"></i>
            ${message}
        `;
        
        // Insert at top of main content
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(notification, mainContent.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Smooth scrolling for internal links
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});

// Modal de confirmação de exclusão removido - agora cada página tem seu próprio modal customizado
/*
document.addEventListener('click', function(e) {
    if (e.target.closest('.delete-btn')) {
        e.preventDefault();
        // ... código removido para evitar conflito com modais específicos das páginas
    }
});
*/

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save forms
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        // Handle different save actions based on page
        if (window.location.pathname.includes('teoria.html') && typeof saveTheory === 'function') {
            saveTheory();
        } else {
            const activeForm = document.querySelector('form');
            if (activeForm) {
                activeForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        }
    }
    
    // Escape to close modals - cada página tem seu próprio handler de ESC agora
    // if (e.key === 'Escape') { ... }
});

// Loading state management
function showLoading(element) {
    const originalText = element.textContent;
    element.textContent = 'Carregando...';
    element.disabled = true;
    
    return function hideLoading() {
        element.textContent = originalText;
        element.disabled = false;
    };
}

// Add loading states to forms (only for actual form submissions, not JS handled ones)
document.addEventListener('submit', function(e) {
    // Skip if this is a JS-handled form
    if (e.target.id === 'example-form') return;
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        const hideLoading = showLoading(submitBtn);
        // Hide loading after a short delay for static forms
        setTimeout(hideLoading, 1000);
    }
});
