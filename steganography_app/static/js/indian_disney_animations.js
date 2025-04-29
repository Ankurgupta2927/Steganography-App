// Indian Disney Theme Animations

document.addEventListener('DOMContentLoaded', function() {
    // Create rangoli pattern effect
    createRangoliEffect();
    
    // Add peacock decorations
    addPeacockDecorations();
    
    // Enhance form interactions
    enhanceFormInteractions();
    
    // Add loading animations
    setupLoadingAnimations();
    
    // Add floating elements
    animateFloatingElements();
});

// Create a decorative rangoli pattern effect
function createRangoliEffect() {
    const rangoliContainer = document.createElement('div');
    rangoliContainer.classList.add('rangoli');
    document.body.appendChild(rangoliContainer);
    
    // Add rangoli dots in a pattern
    const colors = ['#FF9933', '#138808', '#000080', '#FF5733', '#C70039'];
    const numDots = window.innerWidth < 768 ? 30 : 60;
    
    for (let i = 0; i < numDots; i++) {
        const dot = document.createElement('div');
        dot.classList.add('rangoli-dot');
        
        // Random position
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        
        // Random size
        const size = 5 + Math.random() * 15;
        
        // Random color
        dot.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        dot.style.width = `${size}px`;
        dot.style.height = `${size}px`;
        dot.style.left = `${x}vw`;
        dot.style.top = `${y}vh`;
        
        // Random animation duration
        const duration = 2 + Math.random() * 4;
        dot.style.animationDuration = `${duration}s`;
        
        // Random delay
        const delay = Math.random() * 2;
        dot.style.animationDelay = `${delay}s`;
        
        rangoliContainer.appendChild(dot);
    }
}

// Add peacock decorations to the page
function addPeacockDecorations() {
    const container = document.querySelector('.container');
    
    if (container) {
        // Create top-right peacock feather
        const peacockTopRight = document.createElement('div');
        peacockTopRight.classList.add('peacock-decoration', 'peacock-top-right');
        container.appendChild(peacockTopRight);
        
        // Create bottom-left peacock feather
        const peacockBottomLeft = document.createElement('div');
        peacockBottomLeft.classList.add('peacock-decoration', 'peacock-bottom-left');
        container.appendChild(peacockBottomLeft);
    }
}

// Enhance form interactions with animations
function enhanceFormInteractions() {
    // Enhance file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const parent = input.parentElement;
        
        // Skip if already enhanced
        if (parent.classList.contains('file-upload-container')) return;
        
        // Create custom file upload container
        const container = document.createElement('div');
        container.classList.add('file-upload-container');
        
        // Add icon
        const icon = document.createElement('div');
        icon.classList.add('file-upload-icon');
        icon.innerHTML = '📁';
        container.appendChild(icon);
        
        // Add text
        const text = document.createElement('p');
        text.textContent = 'Click or drag file to upload';
        container.appendChild(text);
        
        // Add file name display
        const fileNameDisplay = document.createElement('p');
        fileNameDisplay.classList.add('file-name');
        fileNameDisplay.style.marginTop = '10px';
        fileNameDisplay.style.fontWeight = 'bold';
        container.appendChild(fileNameDisplay);
        
        // Replace the input with our container
        parent.insertBefore(container, input);
        container.appendChild(input);
        
        // Update file name on selection
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileNameDisplay.textContent = this.files[0].name;
                container.style.borderColor = 'var(--secondary-color)';
                container.style.backgroundColor = 'rgba(19, 136, 8, 0.05)';
            } else {
                fileNameDisplay.textContent = '';
                container.style.borderColor = 'var(--primary-color)';
                container.style.backgroundColor = '';
            }
        });
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Setup loading animations for form submissions
function setupLoadingAnimations() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Create loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.classList.add('loading-overlay');
            loadingOverlay.style.position = 'fixed';
            loadingOverlay.style.top = '0';
            loadingOverlay.style.left = '0';
            loadingOverlay.style.width = '100%';
            loadingOverlay.style.height = '100%';
            loadingOverlay.style.backgroundColor = 'rgba(255,255,255,0.8)';
            loadingOverlay.style.display = 'flex';
            loadingOverlay.style.justifyContent = 'center';
            loadingOverlay.style.alignItems = 'center';
            loadingOverlay.style.zIndex = '9999';
            
            // Create loading ring
            const loadingRing = document.createElement('div');
            loadingRing.classList.add('loading-ring');
            loadingRing.innerHTML = '<div></div><div></div><div></div><div></div>';
            
            // Create loading text
            const loadingText = document.createElement('p');
            loadingText.textContent = 'Processing your request...';
            loadingText.style.marginTop = '100px';
            loadingText.style.color = 'var(--primary-color)';
            loadingText.style.fontWeight = 'bold';
            
            loadingOverlay.appendChild(loadingRing);
            loadingOverlay.appendChild(loadingText);
            
            document.body.appendChild(loadingOverlay);
        });
    });
}

// Animate floating elements with a gentle hover effect
function animateFloatingElements() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach((card, index) => {
        // Add a subtle floating animation
        card.style.animationName = 'floatingCard';
        card.style.animationDuration = '3s';
        card.style.animationTimingFunction = 'ease-in-out';
        card.style.animationIterationCount = 'infinite';
        card.style.animationDirection = 'alternate';
        
        // Different delay for each card
        card.style.animationDelay = `${index * 0.2}s`;
    });
    
    // Add the keyframe animation if it doesn't exist
    if (!document.querySelector('#floating-animation')) {
        const style = document.createElement('style');
        style.id = 'floating-animation';
        style.textContent = `
            @keyframes floatingCard {
                0% { transform: translateY(0); }
                100% { transform: translateY(-10px); }
            }
        `;
        document.head.appendChild(style);
    }
}
