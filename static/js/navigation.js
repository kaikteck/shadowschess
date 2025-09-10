// Navigation functionality for static HTML pages
document.addEventListener('DOMContentLoaded', function() {
    // Set active navigation link based on current page
    setActiveNavLink();
    
    // Flash message functionality
    initializeFlashMessages();
});

function setActiveNavLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        if (href === currentPage || 
            (currentPage === '' && href === 'index.html') ||
            (currentPage === 'index.html' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
}

function showFlashMessage(message, category = 'success') {
    const flashContainer = document.getElementById('flash-messages');
    const flashText = document.getElementById('flash-text');
    const alertDiv = flashContainer.querySelector('.alert');
    
    if (flashContainer && flashText) {
        flashText.textContent = message;
        alertDiv.className = `alert alert-${category}`;
        flashContainer.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            flashContainer.style.display = 'none';
        }, 5000);
    }
}

function hideFlashMessage() {
    const flashContainer = document.getElementById('flash-messages');
    if (flashContainer) {
        flashContainer.style.display = 'none';
    }
}

function initializeFlashMessages() {
    // Hide flash messages when clicked
    const flashContainer = document.getElementById('flash-messages');
    if (flashContainer) {
        flashContainer.addEventListener('click', hideFlashMessage);
    }
}