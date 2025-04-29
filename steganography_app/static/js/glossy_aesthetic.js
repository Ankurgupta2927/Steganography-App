// Optimized Glossy Aesthetic JavaScript - Fixed File Upload Functionality

document.addEventListener('DOMContentLoaded', function() {
    // Create minimal glowing elements (optimized)
    createSimplifiedGlowElements();
    
    // Fix file upload functionality
    fixFileUploads();
    
    // Add optimized form interactions
    enhanceFormElements();
    
    // Add basic page transitions (optimized)
    addSimplePageTransitions();
});

// Create simplified glow elements for better performance
function createSimplifiedGlowElements() {
    const container = document.querySelector('.container');
    
    if (container) {
        // Create only one glow element for better performance
        const glowElement = document.createElement('div');
        glowElement.classList.add('glow-element', 'glow-1');
        container.appendChild(glowElement);
    }
}

// Fix file upload functionality
function fixFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        // Make sure the input is visible and clickable
        input.style.opacity = "1";
        input.style.position = "relative";
        input.style.zIndex = "10";
        input.style.cursor = "pointer";
        
        // Add 'hidden-file-input' class for CSS targeting
        input.classList.add('hidden-file-input');
        
        // Add click handler to ensure it works
        input.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent event bubbling
        });
        
        // Wrap in a container if not already wrapped
        if (!input.parentElement.classList.contains('file-input-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('file-input-wrapper');
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            
            // Add a label to show the selected file name
            const fileNameDisplay = document.createElement('div');
            fileNameDisplay.classList.add('file-name-display');
            fileNameDisplay.textContent = "No file selected";
            fileNameDisplay.style.marginTop = "8px";
            fileNameDisplay.style.fontSize = "0.9rem";
            fileNameDisplay.style.color = "rgba(255, 255, 255, 0.7)";
            wrapper.appendChild(fileNameDisplay);
            
            // Update file name display when a file is selected
            input.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    fileNameDisplay.textContent = "Selected: " + this.files[0].name;
                    fileNameDisplay.style.color = "var(--primary-color)";
                } else {
                    fileNameDisplay.textContent = "No file selected";
                    fileNameDisplay.style.color = "rgba(255, 255, 255, 0.7)";
                }
            });
        }
    });
}

// Optimized form element enhancements
function enhanceFormElements() {
    // Add optimized button click effect
    const buttons = document.querySelectorAll('button');
    
    buttons.forEach(button => {
        button.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(2px)';
        });
        
        button.addEventListener('mouseup', function() {
            this.style.transform = '';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Optimize focus effects on form elements
    const formElements = document.querySelectorAll('input, textarea, select');
    
    formElements.forEach(element => {
        element.addEventListener('focus', function() {
            this.style.borderColor = 'var(--primary-color)';
            this.style.boxShadow = '0 0 0 3px rgba(109, 40, 217, 0.2)';
        });
        
        element.addEventListener('blur', function() {
            this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            this.style.boxShadow = 'none';
        });
    });
}

// Add simple page transitions for better performance
function addSimplePageTransitions() {
    // Simple fade in for the page
    document.body.style.opacity = "0";
    setTimeout(() => {
        document.body.style.transition = "opacity 0.5s ease";
        document.body.style.opacity = "1";
    }, 10);
    
    // Detect form submissions and show loading state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Create and show a simple loading spinner
            const spinner = document.createElement('div');
            spinner.classList.add('loading-spinner');
            
            const loadingText = document.createElement('p');
            loadingText.textContent = "Processing...";
            loadingText.style.textAlign = "center";
            
            const loadingContainer = document.createElement('div');
            loadingContainer.appendChild(spinner);
            loadingContainer.appendChild(loadingText);
            loadingContainer.style.position = "fixed";
            loadingContainer.style.top = "50%";
            loadingContainer.style.left = "50%";
            loadingContainer.style.transform = "translate(-50%, -50%)";
            loadingContainer.style.zIndex = "1000";
            loadingContainer.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
            loadingContainer.style.padding = "2rem";
            loadingContainer.style.borderRadius = "10px";
            
            document.body.appendChild(loadingContainer);
        });
    });
}
