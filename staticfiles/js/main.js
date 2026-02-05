// Basic back-to-top button behaviour
(function () {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  window.addEventListener('scroll', function () {
    if (window.scrollY > 300) {
      btn.style.display = 'inline-flex';
    } else {
      btn.style.display = 'none';
    }
  });

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// Global Toast Notification System
(function() {
    'use strict';
    
    // Toast notification function - can be called from anywhere
    window.showToast = function(message, type = 'success', duration = 5000) {
        // Map message types to Bootstrap colors and icons
        const typeMap = {
            'success': { bg: 'success', icon: 'fa-check-circle' },
            'error': { bg: 'danger', icon: 'fa-exclamation-circle' },
            'warning': { bg: 'warning', icon: 'fa-exclamation-triangle' },
            'info': { bg: 'info', icon: 'fa-info-circle' },
            'debug': { bg: 'secondary', icon: 'fa-bug' }
        };
        
        // Get type configuration
        const toastType = typeMap[type] || typeMap['info'];
        
        // Create unique ID for this toast
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Create toast HTML
        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="${duration}">
                <div class="toast-header bg-${toastType.bg} text-white">
                    <i class="fas ${toastType.icon} me-2"></i>
                    <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        // Get or create toast container
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Insert toast
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Get the toast element
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });
        
        // Show toast
        toast.show();
        
        // Remove element from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    };
    
    // Initialize toasts for Django messages on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Get messages from data attribute if available
        const messageContainer = document.querySelector('[data-messages]');
        if (messageContainer) {
            try {
                const messages = JSON.parse(messageContainer.getAttribute('data-messages'));
                messages.forEach(function(msg, index) {
                    // Map Django message tags to toast types
                    let toastType = msg.type;
                    if (toastType === 'error') {
                        toastType = 'error'; // error maps to danger in Bootstrap
                    } else if (!['success', 'warning', 'info', 'debug'].includes(toastType)) {
                        toastType = 'info'; // default to info
                    }
                    
                    setTimeout(function() {
                        showToast(msg.text, toastType, 5000);
                    }, index * 300);
                });
            } catch (e) {
                console.error('Error parsing messages:', e);
            }
        }
    });
})();