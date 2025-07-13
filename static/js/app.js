/**
 * Allergy Info Nigeria - Main JavaScript Application
 * Handles client-side interactions and enhancements
 */

// Global application object
window.AllergyInfoApp = {
    init: function() {
        this.initFormValidation();
        this.initPasswordToggles();
        this.initAllergenSelection();
        this.initSearchEnhancements();
        this.initModalHandlers();
        this.initTooltips();
        this.initAnimations();
        this.initAccessibility();
    },

    // Form validation and enhancement
    initFormValidation: function() {
        // Real-time email validation
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', this.validateEmail);
            input.addEventListener('input', this.clearValidationError);
        });

        // Password strength indicator
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            if (input.id === 'password' || input.name === 'password') {
                input.addEventListener('input', this.checkPasswordStrength);
            }
        });

        // Form submission prevention for invalid forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmission);
        });

        // Auto-format NAFDAC numbers
        const nafdacInputs = document.querySelectorAll('input[name="nafdac_number"]');
        nafdacInputs.forEach(input => {
            input.addEventListener('input', this.formatNafdacNumber);
        });
    },

    validateEmail: function(event) {
        const email = event.target.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(email);
        
        const input = event.target;
        const feedback = input.parentNode.querySelector('.email-feedback') || 
                        document.createElement('div');
        
        if (!feedback.classList.contains('email-feedback')) {
            feedback.className = 'email-feedback small mt-1';
            input.parentNode.appendChild(feedback);
        }

        if (email && !isValid) {
            input.classList.add('is-invalid');
            feedback.className = 'email-feedback small mt-1 text-danger';
            feedback.textContent = 'Please enter a valid email address';
        } else if (email && isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            feedback.className = 'email-feedback small mt-1 text-success';
            feedback.textContent = 'Valid email address';
        } else {
            input.classList.remove('is-invalid', 'is-valid');
            feedback.textContent = '';
        }
    },

    clearValidationError: function(event) {
        const input = event.target;
        if (input.classList.contains('is-invalid')) {
            input.classList.remove('is-invalid');
            const feedback = input.parentNode.querySelector('.email-feedback');
            if (feedback) {
                feedback.textContent = '';
            }
        }
    },

    checkPasswordStrength: function(event) {
        const password = event.target.value;
        const strengthIndicator = document.getElementById('password-strength') || 
                                 AllergyInfoApp.createPasswordStrengthIndicator(event.target);
        
        const strength = AllergyInfoApp.calculatePasswordStrength(password);
        AllergyInfoApp.updatePasswordStrengthDisplay(strengthIndicator, strength);
    },

    createPasswordStrengthIndicator: function(passwordInput) {
        const indicator = document.createElement('div');
        indicator.id = 'password-strength';
        indicator.className = 'password-strength';
        indicator.innerHTML = `
            <div class="progress">
                <div class="progress-bar" role="progressbar"></div>
            </div>
            <small class="strength-text text-muted"></small>
        `;
        // Insert as absolute positioned element relative to password field container
        const container = passwordInput.closest('.password-field') || 
                         passwordInput.closest('.password-input-container') || 
                         passwordInput.closest('.position-relative') ||
                         passwordInput.parentNode;
        container.appendChild(indicator);
        return indicator;
    },

    calculatePasswordStrength: function(password) {
        let score = 0;
        const checks = {
            length: password.length >= 6,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /[0-9]/.test(password),
            special: /[^A-Za-z0-9]/.test(password)
        };

        Object.values(checks).forEach(check => {
            if (check) score++;
        });

        if (password.length >= 8) score++;
        if (password.length >= 12) score++;

        return {
            score: score,
            checks: checks,
            level: score < 2 ? 'weak' : score < 4 ? 'medium' : score < 6 ? 'strong' : 'very-strong'
        };
    },

    updatePasswordStrengthDisplay: function(indicator, strength) {
        const progressBar = indicator.querySelector('.progress-bar');
        const strengthText = indicator.querySelector('.strength-text');
        
        const levels = {
            weak: { width: '25%', class: 'bg-danger', text: 'Weak' },
            medium: { width: '50%', class: 'bg-warning', text: 'Medium' },
            strong: { width: '75%', class: 'bg-info', text: 'Strong' },
            'very-strong': { width: '100%', class: 'bg-success', text: 'Very Strong' }
        };

        const level = levels[strength.level];
        progressBar.style.width = level.width;
        progressBar.className = `progress-bar ${level.class}`;
        strengthText.textContent = level.text;
        strengthText.className = `strength-text small ${level.class.replace('bg-', 'text-')}`;
    },

    formatNafdacNumber: function(event) {
        let value = event.target.value.replace(/[^A-Za-z0-9]/g, '');
        if (value.length > 2) {
            value = value.substring(0, 2) + '-' + value.substring(2);
        }
        // if (value.length > 7) {
        //     value = value.substring(0, 7) + value.substring(7, 8).toUpperCase();
        // }
        event.target.value = value;
    },

    handleFormSubmission: function(event) {
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        // Add loading state but don't prevent submission
        if (submitButton) {
            submitButton.disabled = true;   
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
            
            // Don't prevent form submission, just show loading state
            // Form will handle the redirect naturally
        }
    },

    // Enhanced password toggle functionality
    initPasswordToggles: function() {
        // Find all password toggle icons and buttons
        const toggleElements = document.querySelectorAll('.password-toggle-icon, .password-toggle, button[onclick*="togglePassword"]');
        
        toggleElements.forEach(toggle => {
            // Remove any existing onclick handlers
            toggle.removeAttribute('onclick');
            
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Find the password input - check multiple container types
                const container = this.closest('.password-field') || 
                                this.closest('.password-input-container') || 
                                this.closest('.position-relative') ||
                                this.closest('.modern-input-group') || 
                                this.closest('.input-group') ||
                                this.parentElement;
                
                const passwordInput = container ? container.querySelector('input[type="password"], input[type="text"]') : null;
                
                if (passwordInput) {
                    const iconElement = this.querySelector('i') || this;
                    
                    if (passwordInput.type === 'password') {
                        passwordInput.type = 'text';
                        if (iconElement.classList) {
                            iconElement.classList.remove('fa-eye');
                            iconElement.classList.add('fa-eye-slash');
                        }
                        this.setAttribute('title', 'Hide password');
                        this.setAttribute('aria-label', 'Hide password');
                    } else {
                        passwordInput.type = 'password';
                        if (iconElement.classList) {
                            iconElement.classList.remove('fa-eye-slash');
                            iconElement.classList.add('fa-eye');
                        }
                        this.setAttribute('title', 'Show password');
                        this.setAttribute('aria-label', 'Show password');
                    }
                }
            });
            
            // Set initial attributes
            toggle.setAttribute('title', 'Show password');
            toggle.setAttribute('aria-label', 'Show password');
            toggle.setAttribute('tabindex', '0');
            toggle.style.cursor = 'pointer';
        });
    },

    // Allergen selection enhancement (Duolingo-style)
    initAllergenSelection: function() {
        const allergenCards = document.querySelectorAll('.allergen-card');
        
        allergenCards.forEach(card => {
            // Remove inline onclick handlers and add proper event listeners
            card.removeAttribute('onclick');
            
            card.addEventListener('click', function() {
                const checkbox = this.querySelector('.allergen-checkbox');
                const allergenOption = this.querySelector('.allergen-option');
                
                if (checkbox && allergenOption) {
                    checkbox.checked = !checkbox.checked;
                    
                    if (checkbox.checked) {
                        allergenOption.classList.add('selected');
                        // Add animation
                        allergenOption.style.transform = 'scale(1.05)';
                        setTimeout(() => {
                            allergenOption.style.transform = '';
                        }, 200);
                    } else {
                        allergenOption.classList.remove('selected');
                    }
                    
                    // Trigger change event for form validation
                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            // Add keyboard support
            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });

            // Add focus support
            card.setAttribute('tabindex', '0');
            card.addEventListener('focus', function() {
                this.style.outline = '2px solid #28a745';
                this.style.outlineOffset = '2px';
            });

            card.addEventListener('blur', function() {
                this.style.outline = '';
                this.style.outlineOffset = '';
            });
        });
    },

    // Search functionality enhancements
    initSearchEnhancements: function() {
        const searchInputs = document.querySelectorAll('input[name="search"], input[name="q"]');
        
        searchInputs.forEach(input => {
            // Add search suggestions (basic implementation)
            input.addEventListener('input', this.handleSearchInput);
            
            // Handle Enter key
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const form = this.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            });
        });

        // Product search filtering on the homepage
        this.initProductFiltering();
    },

    handleSearchInput: function(event) {
        const query = event.target.value.trim();
        
        // Clear previous timeout
        if (window.searchTimeout) {
            clearTimeout(window.searchTimeout);
        }
        
        // Debounce search suggestions
        window.searchTimeout = setTimeout(() => {
            if (query.length >= 2) {
                AllergyInfoApp.showSearchSuggestions(event.target, query);
            } else {
                AllergyInfoApp.hideSearchSuggestions(event.target);
            }
        }, 300);
    },

    showSearchSuggestions: function(input, query) {
        // Basic client-side search suggestions
        const suggestions = [
            'Indomie Instant Noodles',
            'Peak Milk Powder',
            'Golden Morn Cereal',
            'Maggi Chicken Cubes',
            'Bournvita Chocolate Drink',
            'Cowbell Milk Powder',
            'Tom Tom Menthol Candy',
            'Gala Sausage Roll'
        ];

        const filtered = suggestions.filter(item => 
            item.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 5);

        if (filtered.length > 0) {
            const dropdown = this.createSuggestionsDropdown(input, filtered);
            this.positionDropdown(input, dropdown);
        }
    },

    createSuggestionsDropdown: function(input, suggestions) {
        // Remove existing dropdown
        this.hideSearchSuggestions(input);
        
        const dropdown = document.createElement('div');
        dropdown.className = 'search-suggestions-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 0.375rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            z-index: 1000;
            max-height: 200px;
            overflow-y: auto;
        `;

        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.style.cssText = `
                padding: 0.5rem 1rem;
                cursor: pointer;
                border-bottom: 1px solid #f8f9fa;
            `;
            item.textContent = suggestion;
            
            item.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
            
            item.addEventListener('click', function() {
                input.value = suggestion;
                AllergyInfoApp.hideSearchSuggestions(input);
                const form = input.closest('form');
                if (form) {
                    form.submit();
                }
            });
            
            dropdown.appendChild(item);
        });

        input.parentNode.appendChild(dropdown);
        return dropdown;
    },

    positionDropdown: function(input, dropdown) {
        const rect = input.getBoundingClientRect();
        dropdown.style.top = (rect.bottom + window.scrollY) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.width = rect.width + 'px';
    },

    hideSearchSuggestions: function(input) {
        const existing = input.parentNode.querySelector('.search-suggestions-dropdown');
        if (existing) {
            existing.remove();
        }
    },

    initProductFiltering: function() {
        // Client-side product filtering for better UX
        const productCards = document.querySelectorAll('.product-card');
        
        if (productCards.length > 0) {
            // Add filter controls if needed
            this.addProductFilterControls();
        }
    },

    addProductFilterControls: function() {
        const productsContainer = document.querySelector('.row:has(.product-card)');
        if (!productsContainer) return;

        const filterContainer = document.createElement('div');
        filterContainer.className = 'mb-4';
        filterContainer.innerHTML = `
            <div class="card border-0 bg-light">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <label class="form-label small text-muted mb-1">Filter by Category</label>
                            <select class="form-select form-select-sm" id="categoryFilter">
                                <option value="">All Categories</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label small text-muted mb-1">Filter by Safety</label>
                            <select class="form-select form-select-sm" id="safetyFilter">
                                <option value="">All Products</option>
                                <option value="safe">Safe for Me</option>
                                <option value="warning">Contains Allergens</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label small text-muted mb-1">Sort by</label>
                            <select class="form-select form-select-sm" id="sortFilter">
                                <option value="">Default</option>
                                <option value="name">Name A-Z</option>
                                <option value="manufacturer">Manufacturer</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        `;

        productsContainer.parentNode.insertBefore(filterContainer, productsContainer);
        
        // Populate category options
        this.populateFilterOptions();
        
        // Add filter event listeners
        document.getElementById('categoryFilter').addEventListener('change', this.applyFilters);
        document.getElementById('safetyFilter').addEventListener('change', this.applyFilters);
        document.getElementById('sortFilter').addEventListener('change', this.applyFilters);
    },

    populateFilterOptions: function() {
        const productCards = document.querySelectorAll('.product-card');
        const categories = new Set();
        
        productCards.forEach(card => {
            const categoryElement = card.querySelector('.badge:not(.bg-danger):not(.bg-success)');
            if (categoryElement) {
                categories.add(categoryElement.textContent.trim());
            }
        });

        const categorySelect = document.getElementById('categoryFilter');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });
    },

    applyFilters: function() {
        const categoryFilter = document.getElementById('categoryFilter').value;
        const safetyFilter = document.getElementById('safetyFilter').value;
        const sortFilter = document.getElementById('sortFilter').value;
        
        const productCards = document.querySelectorAll('.product-card');
        const productsArray = Array.from(productCards);
        
        // Filter products
        productsArray.forEach(card => {
            let show = true;
            
            // Category filter
            if (categoryFilter) {
                const categoryElement = card.querySelector('.badge:not(.bg-danger):not(.bg-success)');
                const cardCategory = categoryElement ? categoryElement.textContent.trim() : '';
                if (cardCategory !== categoryFilter) {
                    show = false;
                }
            }
            
            // Safety filter
            if (safetyFilter && show) {
                const hasDangerBadge = card.querySelector('.badge.bg-danger');
                const hasSuccessBadge = card.querySelector('.badge.bg-success');
                
                if (safetyFilter === 'safe' && hasDangerBadge) {
                    show = false;
                } else if (safetyFilter === 'warning' && !hasDangerBadge) {
                    show = false;
                }
            }
            
            card.style.display = show ? '' : 'none';
        });
        
        // Sort products
        if (sortFilter) {
            AllergyInfoApp.sortProducts(productsArray, sortFilter);
        }
        
        // Update results count
        AllergyInfoApp.updateResultsCount();
    },

    sortProducts: function(products, sortBy) {
        const container = products[0].parentNode;
        
        products.sort((a, b) => {
            let aValue, bValue;
            
            switch (sortBy) {
                case 'name':
                    aValue = a.querySelector('.card-title').textContent.trim();
                    bValue = b.querySelector('.card-title').textContent.trim();
                    break;
                case 'manufacturer':
                    aValue = a.querySelector('.fa-building').parentNode.textContent.trim();
                    bValue = b.querySelector('.fa-building').parentNode.textContent.trim();
                    break;
                default:
                    return 0;
            }
            
            return aValue.localeCompare(bValue);
        });
        
        products.forEach(product => {
            container.appendChild(product);
        });
    },

    updateResultsCount: function() {
        const visibleProducts = document.querySelectorAll('.product-card:not([style*="display: none"])');
        const totalProducts = document.querySelectorAll('.product-card');
        
        // Find or create results counter
        let counter = document.querySelector('.results-counter');
        if (!counter) {
            counter = document.createElement('p');
            counter.className = 'results-counter text-muted text-center mt-3';
            const container = document.querySelector('.row:has(.product-card)');
            if (container) {
                container.parentNode.appendChild(counter);
            }
        }
        
        counter.textContent = `Showing ${visibleProducts.length} of ${totalProducts.length} products`;
    },

    // Modal handling
    initModalHandlers: function() {
        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.input-group')) {
                const dropdowns = document.querySelectorAll('.search-suggestions-dropdown');
                dropdowns.forEach(dropdown => dropdown.remove());
            }
        });

        // Modal focus management
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', function() {
                const firstInput = this.querySelector('input, textarea, select');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        });

        // Confirm dangerous actions
        const dangerButtons = document.querySelectorAll('.btn-danger[type="submit"]');
        dangerButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const action = this.textContent.trim().toLowerCase();
                if (!confirm(`Are you sure you want to ${action}? This action cannot be undone.`)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });
    },

    // Tooltip initialization
    initTooltips: function() {
        // Initialize Bootstrap tooltips if available
        if (window.bootstrap && bootstrap.Tooltip) {
            const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"], [title]:not([title=""])');
            tooltipElements.forEach(element => {
                if (!element.getAttribute('data-bs-toggle')) {
                    element.setAttribute('data-bs-toggle', 'tooltip');
                }
                new bootstrap.Tooltip(element);
            });
        }
    },

    // Animation and visual enhancements
    initAnimations: function() {
        // Smooth scroll for anchor links
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Fade in animations for cards
        const cards = document.querySelectorAll('.card');
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '0';
                    entry.target.style.transform = 'translateY(20px)';
                    entry.target.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, 100);
                    
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        cards.forEach(card => {
            observer.observe(card);
        });
    },

    // Accessibility enhancements
    initAccessibility: function() {
        // Add ARIA labels where missing
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            const text = button.textContent.trim() || button.title || 'Button';
            button.setAttribute('aria-label', text);
        });

        // Add role attributes to card elements
        const productCards = document.querySelectorAll('.product-card');
        productCards.forEach(card => {
            card.setAttribute('role', 'article');
            card.setAttribute('aria-label', `Product: ${card.querySelector('.card-title')?.textContent || 'Product card'}`);
        });

        // Skip link for keyboard navigation
        if (!document.querySelector('.skip-link')) {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link sr-only sr-only-focusable';
            skipLink.textContent = 'Skip to main content';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: #28a745;
                color: white;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                z-index: 1000;
            `;
            
            skipLink.addEventListener('focus', function() {
                this.style.top = '6px';
            });
            
            skipLink.addEventListener('blur', function() {
                this.style.top = '-40px';
            });
            
            document.body.insertBefore(skipLink, document.body.firstChild);
        }

        // Add main landmark if missing
        const main = document.querySelector('main');
        if (main && !main.id) {
            main.id = 'main-content';
        }

        // Keyboard navigation for allergen cards
        const allergenCards = document.querySelectorAll('.allergen-card');
        allergenCards.forEach((card, index) => {
            card.addEventListener('keydown', function(e) {
                let nextCard;
                
                switch(e.key) {
                    case 'ArrowDown':
                    case 'ArrowRight':
                        e.preventDefault();
                        nextCard = allergenCards[index + 1];
                        if (nextCard) nextCard.focus();
                        break;
                    case 'ArrowUp':
                    case 'ArrowLeft':
                        e.preventDefault();
                        nextCard = allergenCards[index - 1];
                        if (nextCard) nextCard.focus();
                        break;
                }
            });
        });
    },

    // Utility functions
    utils: {
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        throttle: function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        formatDate: function(date) {
            return new Intl.DateTimeFormat('en-NG', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }).format(new Date(date));
        },

        showNotification: function(message, type = 'info') {
            // Create a temporary notification
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = `
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
            `;
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    AllergyInfoApp.init();
});

// Handle browser back/forward navigation
window.addEventListener('popstate', function(event) {
    // Refresh dynamic content if needed
    const searchInput = document.querySelector('input[name="search"], input[name="q"]');
    if (searchInput && searchInput.value) {
        AllergyInfoApp.handleSearchInput({ target: searchInput });
    }
});

// Handle window resize for responsive elements
window.addEventListener('resize', AllergyInfoApp.utils.throttle(function() {
    // Reposition any open dropdowns
    const dropdowns = document.querySelectorAll('.search-suggestions-dropdown');
    dropdowns.forEach(dropdown => {
        const input = dropdown.previousElementSibling;
        if (input && input.matches('input')) {
            AllergyInfoApp.positionDropdown(input, dropdown);
        }
    });
}, 250));

// Error handling for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    
    // Show user-friendly error message for critical errors
    if (event.error && event.error.message) {
        AllergyInfoApp.utils.showNotification(
            'An error occurred. Please refresh the page and try again.',
            'danger'
        );
    }
});

// Service worker registration for offline support (if needed in future)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Service worker registration would go here if implemented
        console.log('App loaded successfully');
    });
}

// Export for global access
window.AllergyInfoApp = AllergyInfoApp;
