// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Password toggle functionality
    const toggleButtons = document.querySelectorAll('.password-toggle');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                icon.className = 'fas fa-eye';
            }
        });
    });

    // Account type card selection
    const accountTypeCards = document.querySelectorAll('.account-type-card');
    
    accountTypeCards.forEach(card => {
        const radio = card.querySelector('.form-check-input');
        
        card.addEventListener('click', function() {
            // Remove selected class from all cards
            accountTypeCards.forEach(c => c.classList.remove('selected'));
            // Add selected class to clicked card
            this.classList.add('selected');
            // Check the radio button
            radio.checked = true;
        });
        
        // Initialize selected state
        if (radio.checked) {
            card.classList.add('selected');
        }
    });

    // Fade in animations for elements with data-delay attribute
    const fadeElements = document.querySelectorAll('[data-delay]');
    
    fadeElements.forEach(el => {
        const delay = parseInt(el.getAttribute('data-delay')) || 0;
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, delay);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});