// TransPak AI Quoter - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('quoteForm');
    const generateBtn = document.getElementById('generateBtn');
    
    if (form && generateBtn) {
        form.addEventListener('submit', function(e) {
            // Show loading state
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating Quote...';
            generateBtn.disabled = true;
            
            // Optional: Add form validation feedback
            const requiredFields = form.querySelectorAll('[required]');
            let allValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    allValid = false;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            if (!allValid) {
                e.preventDefault();
                generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Generate AI Quote';
                generateBtn.disabled = false;
                
                // Show error message
                showAlert('Please fill in all required fields.', 'danger');
                return;
            }
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Form field enhancements
    enhanceFormFields();
});

function enhanceFormFields() {
    // Add input formatting and validation helpers
    const dimensionsField = document.getElementById('dimensions');
    const weightField = document.getElementById('weight');
    
    if (dimensionsField) {
        dimensionsField.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value && !value.match(/\d+\s*[x×]\s*\d+\s*[x×]\s*\d+/i)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Please use format: Length x Width x Height (e.g., 48 x 36 x 24 inches)');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }
    
    if (weightField) {
        weightField.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value && !value.match(/\d+.*?(lb|kg|ton|pound|kilogram)/i)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Please include weight units (e.g., 500 lbs, 227 kg)');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }
}

function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const firstCard = document.querySelector('.card');
    if (firstCard) {
        firstCard.parentNode.insertBefore(alertContainer.firstElementChild, firstCard);
    }
}

function showFieldError(field, message) {
    hideFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.id = field.id + '_error';
    
    field.parentNode.appendChild(errorDiv);
}

function hideFieldError(field) {
    const errorDiv = document.getElementById(field.id + '_error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Auto-save form data to localStorage (optional enhancement)
function saveFormData() {
    const form = document.getElementById('quoteForm');
    if (form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        localStorage.setItem('transpak_form_data', JSON.stringify(data));
    }
}

function loadFormData() {
    const savedData = localStorage.getItem('transpak_form_data');
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(key => {
            const field = document.getElementById(key);
            if (field && !field.value) {
                field.value = data[key];
            }
        });
    }
}

// Load saved form data on page load (if no server-side form data)
document.addEventListener('DOMContentLoaded', function() {
    const hasFormData = document.querySelector('[name="item_description"]').value;
    if (!hasFormData) {
        loadFormData();
    }
});

// Save form data periodically
setInterval(saveFormData, 30000); // Save every 30 seconds
