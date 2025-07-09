// Main JavaScript file for AI Podcast Generator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFormValidation();
    initializeAudioPlayers();
    initializeAnimations();
    initializeTooltips();
    initializeVoiceSelection();
    
    console.log('AI Podcast Generator initialized');
});

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
            
            // Add loading state to submit button
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && form.checkValidity()) {
                addLoadingState(submitBtn);
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Custom validation messages
    if (!isValid) {
        showFieldError(field);
    }
}

function showFieldError(field) {
    let errorMessage = field.validationMessage;
    
    // Custom error messages
    if (field.type === 'email' && field.validity.typeMismatch) {
        errorMessage = 'Please enter a valid email address.';
    } else if (field.name === 'password' && field.validity.tooShort) {
        errorMessage = 'Password must be at least 6 characters long.';
    } else if (field.name === 'confirm_password') {
        const password = document.querySelector('input[name="password"]');
        if (password && field.value !== password.value) {
            errorMessage = 'Passwords do not match.';
            field.setCustomValidity(errorMessage);
        } else {
            field.setCustomValidity('');
        }
    }
    
    // Show error message
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = errorMessage;
}

// Audio Players Enhancement
function initializeAudioPlayers() {
    const audioElements = document.querySelectorAll('audio');
    
    audioElements.forEach(audio => {
        // Add custom styling and controls
        audio.addEventListener('loadstart', function() {
            addAudioLoadingState(audio);
        });
        
        audio.addEventListener('canplay', function() {
            removeAudioLoadingState(audio);
        });
        
        audio.addEventListener('error', function() {
            showAudioError(audio);
        });
        
        // Add download button functionality
        addDownloadButton(audio);
    });
}

function addAudioLoadingState(audio) {
    const container = audio.parentNode;
    let loader = container.querySelector('.audio-loader');
    
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'audio-loader text-center py-2';
        loader.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading audio...';
        container.insertBefore(loader, audio);
    }
    
    audio.style.display = 'none';
}

function removeAudioLoadingState(audio) {
    const container = audio.parentNode;
    const loader = container.querySelector('.audio-loader');
    
    if (loader) {
        loader.remove();
    }
    
    audio.style.display = 'block';
}

function showAudioError(audio) {
    const container = audio.parentNode;
    removeAudioLoadingState(audio);
    
    const error = document.createElement('div');
    error.className = 'alert alert-danger';
    error.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Failed to load audio file.';
    
    container.replaceChild(error, audio);
}

function addDownloadButton(audio) {
    const src = audio.querySelector('source')?.src || audio.src;
    if (!src) return;
    
    const container = audio.parentNode;
    let downloadBtn = container.querySelector('.audio-download-btn');
    
    if (!downloadBtn) {
        downloadBtn = document.createElement('a');
        downloadBtn.href = src;
        downloadBtn.download = 'podcast.mp3';
        downloadBtn.className = 'btn btn-sm btn-outline-primary audio-download-btn mt-2';
        downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i>Download';
        
        container.appendChild(downloadBtn);
    }
}

// Loading States
function addLoadingState(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    // Store original text for restoration
    button.dataset.originalText = originalText;
    
    // Auto-restore after 30 seconds (fallback)
    setTimeout(() => {
        removeLoadingState(button);
    }, 30000);
}

function removeLoadingState(button) {
    if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
        button.disabled = false;
        delete button.dataset.originalText;
    }
}

// Animations
function initializeAnimations() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .podcast-item, .auth-card').forEach(el => {
        observer.observe(el);
    });
}

// Tooltips
function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Password Confirmation Validation
document.addEventListener('input', function(e) {
    if (e.target.name === 'confirm_password') {
        const password = document.querySelector('input[name="password"]');
        const confirmPassword = e.target;
        
        if (password && confirmPassword.value !== password.value) {
            confirmPassword.setCustomValidity('Passwords do not match.');
        } else {
            confirmPassword.setCustomValidity('');
        }
    }
});

// Character Count for Textarea
document.querySelectorAll('textarea').forEach(textarea => {
    const maxLength = textarea.getAttribute('maxlength');
    if (maxLength) {
        addCharacterCounter(textarea, parseInt(maxLength));
    }
});

function addCharacterCounter(textarea, maxLength) {
    const counter = document.createElement('div');
    counter.className = 'character-counter text-end mt-1';
    counter.style.fontSize = '0.875rem';
    counter.style.color = '#666';
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${textarea.value.length}/${maxLength}`;
        
        if (remaining < 50) {
            counter.style.color = '#dc3545';
        } else if (remaining < 100) {
            counter.style.color = '#ffc107';
        } else {
            counter.style.color = '#666';
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    textarea.parentNode.appendChild(counter);
    updateCounter();
}

// Auto-save for form data (optional enhancement)
function initializeAutoSave() {
    const forms = document.querySelectorAll('.generator-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            // Load saved data
            const savedValue = localStorage.getItem(`autosave_${input.name}`);
            if (savedValue && !input.value) {
                input.value = savedValue;
            }
            
            // Save on input
            input.addEventListener('input', function() {
                localStorage.setItem(`autosave_${input.name}`, input.value);
            });
        });
        
        // Clear on successful submit
        form.addEventListener('submit', function() {
            inputs.forEach(input => {
                localStorage.removeItem(`autosave_${input.name}`);
            });
        });
    });
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    
    // Show user-friendly error message
    showNotification('An error occurred. Please refresh the page and try again.', 'error');
});

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
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

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
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
}

// Voice Selection Enhancement
function initializeVoiceSelection() {
    const voiceSelect = document.getElementById('voice');
    if (!voiceSelect) return;
    
    // Add change event listener
    voiceSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.value) {
            showVoiceInfo(selectedOption);
        }
    });
    
    // Add search functionality
    addVoiceSearch(voiceSelect);
}

function showVoiceInfo(option) {
    const language = option.getAttribute('data-language');
    const gender = option.getAttribute('data-gender');
    const accent = option.getAttribute('data-accent');
    
    let infoHtml = '<div class="voice-info mt-2 p-2 bg-light rounded"><small>';
    if (language) infoHtml += `<strong>Language:</strong> ${language} `;
    if (gender) infoHtml += `<strong>Gender:</strong> ${gender} `;
    if (accent) infoHtml += `<strong>Accent:</strong> ${accent}`;
    infoHtml += '</small></div>';
    
    // Remove existing info
    const existingInfo = document.querySelector('.voice-info');
    if (existingInfo) existingInfo.remove();
    
    // Add new info
    const voiceContainer = document.getElementById('voice').parentNode;
    voiceContainer.insertAdjacentHTML('beforeend', infoHtml);
}

function addVoiceSearch(selectElement) {
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control mb-2';
    searchInput.placeholder = 'Search voices by name, language, or gender...';
    
    selectElement.parentNode.insertBefore(searchInput, selectElement);
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const options = selectElement.querySelectorAll('option');
        
        options.forEach(option => {
            if (option.value === '') return; // Keep the default option
            
            const text = option.textContent.toLowerCase();
            const language = (option.getAttribute('data-language') || '').toLowerCase();
            const gender = (option.getAttribute('data-gender') || '').toLowerCase();
            const accent = (option.getAttribute('data-accent') || '').toLowerCase();
            
            const matches = text.includes(searchTerm) || 
                          language.includes(searchTerm) || 
                          gender.includes(searchTerm) || 
                          accent.includes(searchTerm);
            
            option.style.display = matches ? 'block' : 'none';
        });
    });
}

// Export functions for use in other scripts
window.PodcastGenerator = {
    showNotification,
    addLoadingState,
    removeLoadingState,
    validateField
};
