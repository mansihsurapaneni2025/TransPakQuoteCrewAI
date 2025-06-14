// TransPak AI Quoter - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('quoteForm');
    const generateBtn = document.getElementById('generateBtn');
    const agentLog = document.getElementById('agentLog');
    
    if (form && generateBtn) {
        form.addEventListener('submit', function(e) {
            // Clear and initialize agent log
            initializeAgentLog();
            
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

// AI Agent Logging System
function initializeAgentLog() {
    const agentLog = document.getElementById('agentLog');
    if (!agentLog) return;
    
    agentLog.innerHTML = `
        <div class="d-flex align-items-center mb-3">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
            <strong>Initializing AI Agent Workflow...</strong>
        </div>
        <div class="border-start border-2 border-primary ps-3 mb-3">
            <div class="text-primary"><i class="fas fa-play-circle me-2"></i>Starting CrewAI Multi-Agent System</div>
            <small class="text-muted">Setting up 4 specialized AI agents for quote generation</small>
        </div>
    `;
    
    // Start simulated agent activity logging
    startAgentActivitySimulation();
}

function startAgentActivitySimulation() {
    const agentLog = document.getElementById('agentLog');
    if (!agentLog) return;
    
    const activities = [
        {
            agent: 'Sales Briefing Agent',
            icon: 'fas fa-user-tie',
            color: 'primary',
            actions: [
                'Analyzing shipment requirements...',
                'Validating provided information...',
                'Checking for missing critical details...',
                'Preparing comprehensive briefing...'
            ]
        },
        {
            agent: 'Crating Design Agent',
            icon: 'fas fa-hard-hat',
            color: 'info',
            actions: [
                'Analyzing item protection requirements...',
                'Designing optimal crating solution...',
                'Selecting appropriate materials...',
                'Calculating material costs and labor...'
            ]
        },
        {
            agent: 'Logistics Planner Agent',
            icon: 'fas fa-route',
            color: 'success',
            actions: [
                'Determining optimal transportation mode...',
                'Planning shipping routes...',
                'Calculating freight costs...',
                'Checking compliance requirements...'
            ]
        },
        {
            agent: 'Quote Consolidator Agent',
            icon: 'fas fa-file-invoice-dollar',
            color: 'warning',
            actions: [
                'Compiling all cost components...',
                'Applying business rules and margins...',
                'Creating service tier options...',
                'Finalizing professional quote...'
            ]
        }
    ];
    
    let currentAgent = 0;
    let currentAction = 0;
    
    function addLogEntry() {
        if (currentAgent >= activities.length) return;
        
        const activity = activities[currentAgent];
        const action = activity.actions[currentAction];
        
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `
            <div class="border-start border-2 border-${activity.color} ps-3 mb-2">
                <div class="d-flex align-items-center">
                    <i class="${activity.icon} text-${activity.color} me-2"></i>
                    <strong class="text-${activity.color}">${activity.agent}</strong>
                    <small class="text-muted ms-auto">${timestamp}</small>
                </div>
                <div class="mt-1">
                    <i class="fas fa-spinner fa-spin text-${activity.color} me-2"></i>
                    ${action}
                </div>
            </div>
        `;
        
        agentLog.insertAdjacentHTML('beforeend', logEntry);
        agentLog.scrollTop = agentLog.scrollHeight;
        
        currentAction++;
        if (currentAction >= activity.actions.length) {
            // Mark agent as completed
            setTimeout(() => {
                const lastEntry = agentLog.lastElementChild;
                const spinner = lastEntry.querySelector('.fa-spinner');
                if (spinner) {
                    spinner.className = 'fas fa-check-circle text-success me-2';
                }
                const actionText = lastEntry.querySelector('div:last-child');
                if (actionText) {
                    actionText.innerHTML = `<i class="fas fa-check-circle text-success me-2"></i>✓ ${activity.agent} completed successfully`;
                }
            }, 1000);
            
            currentAgent++;
            currentAction = 0;
        }
        
        if (currentAgent < activities.length) {
            setTimeout(addLogEntry, Math.random() * 3000 + 2000); // 2-5 second intervals
        } else {
            // All agents completed
            setTimeout(() => {
                agentLog.insertAdjacentHTML('beforeend', `
                    <div class="border border-success rounded p-3 mt-3 bg-light">
                        <div class="text-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>Quote Generation Complete!</strong>
                        </div>
                        <small class="text-muted">All AI agents have successfully completed their tasks</small>
                    </div>
                `);
                agentLog.scrollTop = agentLog.scrollHeight;
            }, 2000);
        }
    }
    
    // Start the simulation after a brief delay
    setTimeout(addLogEntry, 1000);
}

function addRealTimeLogEntry(agentName, action, status = 'working') {
    const agentLog = document.getElementById('agentLog');
    if (!agentLog) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const iconClass = status === 'completed' ? 'fas fa-check-circle text-success' : 'fas fa-spinner fa-spin text-primary';
    
    const logEntry = `
        <div class="border-start border-2 border-primary ps-3 mb-2">
            <div class="d-flex align-items-center">
                <strong class="text-primary">${agentName}</strong>
                <small class="text-muted ms-auto">${timestamp}</small>
            </div>
            <div class="mt-1">
                <i class="${iconClass} me-2"></i>
                ${action}
            </div>
        </div>
    `;
    
    agentLog.insertAdjacentHTML('beforeend', logEntry);
    agentLog.scrollTop = agentLog.scrollHeight;
}
