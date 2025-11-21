// PARMS Advanced Global JavaScript - Enhanced User Experience

document.addEventListener('DOMContentLoaded', function() {
    // Global logout confirmation function
    window.confirmLogout = function(event) {
        event.preventDefault();
        
        // Create custom confirmation modal
        const modal = document.createElement('div');
        modal.className = 'logout-confirmation-modal';
        modal.innerHTML = `
            <div class="logout-modal-backdrop">
                <div class="logout-modal-content">
                    <div class="logout-modal-header">
                        <i class="fas fa-sign-out-alt logout-icon"></i>
                        <h4>Confirm Logout</h4>
                    </div>
                    <div class="logout-modal-body">
                        <p>Are you sure you want to logout from PARMS?</p>
                        <p class="text-muted">You will need to login again to access your dashboard.</p>
                    </div>
                    <div class="logout-modal-footer">
                        <button class="btn-cancel" onclick="closeLogoutModal()">
                            <i class="fas fa-times me-2"></i>Cancel
                        </button>
                        <button class="btn-confirm" onclick="proceedLogout()">
                            <i class="fas fa-sign-out-alt me-2"></i>Logout
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .logout-confirmation-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
            }
            
            .logout-modal-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(5px);
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            }
            
            .logout-modal-content {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 0;
                max-width: 400px;
                width: 90%;
                animation: slideIn 0.3s ease;
                overflow: hidden;
            }
            
            .logout-modal-header {
                background: linear-gradient(135deg, #198754, #20c997);
                color: white;
                padding: 1.5rem;
                text-align: center;
            }
            
            .logout-icon {
                font-size: 2rem;
                margin-bottom: 0.5rem;
                display: block;
            }
            
            .logout-modal-header h4 {
                margin: 0;
                font-weight: 600;
            }
            
            .logout-modal-body {
                padding: 1.5rem;
                text-align: center;
            }
            
            .logout-modal-body p {
                margin-bottom: 0.5rem;
            }
            
            .logout-modal-footer {
                padding: 1rem 1.5rem 1.5rem;
                display: flex;
                gap: 1rem;
                justify-content: center;
            }
            
            .btn-cancel {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
            }
            
            .btn-cancel:hover {
                background: #5a6268;
                transform: translateY(-2px);
            }
            
            .btn-confirm {
                background: linear-gradient(135deg, #dc3545, #c82333);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
            }
            
            .btn-confirm:hover {
                background: linear-gradient(135deg, #c82333, #bd2130);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(220, 53, 69, 0.4);
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideIn {
                from { transform: translateY(-50px) scale(0.9); }
                to { transform: translateY(0) scale(1); }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(modal);
        
        // Close modal functions
        window.closeLogoutModal = function() {
            modal.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(modal);
                document.head.removeChild(style);
                delete window.closeLogoutModal;
                delete window.proceedLogout;
            }, 300);
        };
        
        window.proceedLogout = function() {
            const confirmBtn = modal.querySelector('.btn-confirm');
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Logging out...';
            confirmBtn.disabled = true;
            
            // Create a form to POST to logout with CSRF token
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/logout/';
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                             document.querySelector('meta[name="csrf-token"]')?.content;
            
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
            }
            
            setTimeout(() => {
                document.body.appendChild(form);
                form.submit();
            }, 1000);
        };
        
        // Close on backdrop click
        modal.querySelector('.logout-modal-backdrop').addEventListener('click', function(e) {
            if (e.target === this) {
                window.closeLogoutModal();
            }
        });
        
        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                window.closeLogoutModal();
            }
        });
    };
    
    // Enhanced button interactions
    function enhanceButtons() {
        const buttons = document.querySelectorAll('.btn, .btn-primary, .btn-success, .btn-custom');
        
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px) scale(1.02)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
            
            button.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(0) scale(0.98)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'translateY(-2px) scale(1.02)';
            });
        });
    }
    
    // Form validation enhancement
    function enhanceFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            
            inputs.forEach(input => {
                input.addEventListener('invalid', function(e) {
                    e.preventDefault();
                    this.classList.add('is-invalid');
                    
                    // Create custom error message
                    let errorMsg = this.parentNode.querySelector('.error-message');
                    if (!errorMsg) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        errorMsg.style.cssText = `
                            color: #dc3545;
                            font-size: 0.875rem;
                            margin-top: 0.25rem;
                            font-weight: 500;
                        `;
                        this.parentNode.appendChild(errorMsg);
                    }
                    
                    errorMsg.textContent = this.validationMessage;
                });
                
                input.addEventListener('input', function() {
                    if (this.validity.valid) {
                        this.classList.remove('is-invalid');
                        const errorMsg = this.parentNode.querySelector('.error-message');
                        if (errorMsg) {
                            errorMsg.remove();
                        }
                    }
                });
            });
        });
    }
    
    // Loading state for forms
    function enhanceFormSubmission() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    const originalText = submitBtn.innerHTML || submitBtn.value;
                    submitBtn.disabled = true;
                    
                    if (submitBtn.innerHTML !== undefined) {
                        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                    } else {
                        submitBtn.value = 'Processing...';
                    }
                    
                    // Re-enable after 10 seconds (fallback)
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        if (submitBtn.innerHTML !== undefined) {
                            submitBtn.innerHTML = originalText;
                        } else {
                            submitBtn.value = originalText;
                        }
                    }, 10000);
                }
            });
        });
    }
    
    // Smooth scrolling for anchor links
    function enableSmoothScrolling() {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        
        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    // Notification system
    window.showNotification = function(message, type = 'success', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add notification styles if not already added
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    min-width: 300px;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    animation: slideInRight 0.3s ease;
                }
                
                .notification-success {
                    background: linear-gradient(135deg, #198754, #20c997);
                    color: white;
                }
                
                .notification-error {
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    color: white;
                }
                
                .notification-info {
                    background: linear-gradient(135deg, #0dcaf0, #0a58ca);
                    color: white;
                }
                
                .notification-content {
                    padding: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }
                
                .notification-close {
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                    margin-left: auto;
                    padding: 0.25rem;
                    border-radius: 50%;
                    transition: background 0.3s ease;
                }
                
                .notification-close:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
                
                @keyframes slideInRight {
                    from { transform: translateX(100%); }
                    to { transform: translateX(0); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideInRight 0.3s ease reverse';
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);
    };
    
    // Initialize all enhancements
    enhanceButtons();
    enhanceFormValidation();
    enhanceFormSubmission();
    enableSmoothScrolling();
    
    // Page loading animation
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
    
    console.log('PARMS Advanced Global Scripts Loaded Successfully! 🚀');
});

// Global utility functions
window.PARMS = {
    // Show loading spinner
    showLoading: function(element) {
        if (element) {
            element.style.position = 'relative';
            element.style.pointerEvents = 'none';
            
            const loader = document.createElement('div');
            loader.className = 'parms-loader';
            loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            loader.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #198754;
                font-size: 1.5rem;
                z-index: 1000;
            `;
            
            element.appendChild(loader);
        }
    },
    
    // Hide loading spinner
    hideLoading: function(element) {
        if (element) {
            element.style.pointerEvents = '';
            const loader = element.querySelector('.parms-loader');
            if (loader) {
                loader.remove();
            }
        }
    },
    
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    // Format date
    formatDate: function(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    }
};
