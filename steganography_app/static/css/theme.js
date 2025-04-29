// SteganoGuard Theme System - Dark/Light Mode Toggle

// Function to set the theme
function setTheme(themeName) {
    // Set the data-theme attribute on the document
    document.documentElement.setAttribute('data-theme', themeName);
    
    // Store the current theme preference in localStorage
    localStorage.setItem('theme', themeName);
    
    // Update the toggle icon
    updateToggleIcon(themeName);
    
    // Force refresh any stubborn elements that might have inline styles
    refreshThemeElements(themeName);
}

// Function to forcefully update specific elements that might have inline styles
function refreshThemeElements(themeName) {
    // Update body background and text color
    const body = document.body;
    body.style.backgroundColor = themeName === 'dark' ? '#0f1219' : '#f8f9fc';
    body.style.color = themeName === 'dark' ? '#e2e8f0' : '#2c3e50';
    
    // Update all card backgrounds
    document.querySelectorAll('.card, .feature-card, .main-card, .result-card, .message-card').forEach(card => {
        card.style.backgroundColor = themeName === 'dark' ? '#1a1d29' : '#ffffff';
    });
    
    // Update all form inputs, including file inputs
    document.querySelectorAll('.form-control, .form-select, input[type="text"], input[type="file"], textarea').forEach(input => {
        input.style.backgroundColor = themeName === 'dark' ? '#262c3a' : '#f8fafc';
        input.style.color = themeName === 'dark' ? '#e2e8f0' : '#2c3e50';
        input.style.borderColor = themeName === 'dark' ? '#374151' : '#e2e8f0';
    });
    
    // More comprehensive selector for text elements
    document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, label, small, li, a:not(.btn), td, th, code, pre, strong, em, button:not(.btn), summary, option, select, fieldset, legend').forEach(element => {
        // Skip elements inside buttons, footer or items with specific color classes
        if (!element.closest('.btn') && 
            !element.closest('.footer') &&
            !element.classList.contains('text-white') && 
            !element.classList.contains('text-muted') &&
            !element.classList.contains('text-success') &&
            !element.classList.contains('text-primary') &&
            !element.classList.contains('text-danger') &&
            !element.classList.contains('text-warning') &&
            !element.classList.contains('text-info')) {
            element.style.color = themeName === 'dark' ? '#e2e8f0' : '#2c3e50';
        }
    });
    
    // Ensure footer text is always visible with proper contrast
    document.querySelectorAll('.footer p, .footer div, .footer span, .footer a:not(.btn)').forEach(element => {
        element.style.color = '#ffffff';
    });
    
    // Create or update dynamic stylesheet for theme-specific CSS
    let styleElement = document.getElementById('dynamic-theme-styles');
    if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'dynamic-theme-styles';
        document.head.appendChild(styleElement);
    }
    
    if (themeName === 'dark') {
        // Add comprehensive styles for dark mode, including file inputs
        styleElement.textContent = `
            /* File input styling for dark mode */
            input[type="file"]::file-selector-button {
                background-color: #374151;
                color: #e2e8f0;
                border: 1px solid #4b5563;
                border-radius: 0.25rem;
                padding: 0.375rem 0.75rem;
                transition: all 0.3s ease;
            }
            
            input[type="file"]:hover::file-selector-button {
                background-color: #4b5563;
                color: #ffffff;
                border-color: #5a78e2;
            }
            
            input[type="file"]:active::file-selector-button {
                background-color: #5a78e2;
                color: #ffffff;
                border-color: #5a78e2;
            }
            
            /* Force text color for important elements */
            .form-control, input, select, textarea, option {
                color: #e2e8f0 !important;
            }
            
            /* Fix button hover states in dark mode */
            .btn:hover:not(.btn-primary):not(.btn-secondary):not(.btn-success):not(.btn-danger):not(.btn-warning):not(.btn-info) {
                color: #ffffff !important;
                background-color: #4b5563 !important;
            }
            
            /* Ensure selected files text is visible */
            input[type="file"]::file-selector-button + span,
            input[type="file"] {
                color: #e2e8f0 !important;
            }
            
            /* Fix for placeholder text */
            ::placeholder {
                color: #9ca3af !important;
                opacity: 1;
            }
        `;
    } else {
        // Light mode styles
        styleElement.textContent = `
            /* File input styling for light mode */
            input[type="file"]::file-selector-button {
                background-color: #e2e8f0;
                color: #2c3e50;
                border: 1px solid #cbd5e1;
                border-radius: 0.25rem;
                padding: 0.375rem 0.75rem;
                transition: all 0.3s ease;
            }
            
            input[type="file"]:hover::file-selector-button {
                background-color: #cbd5e1;
                color: #1e293b;
                border-color: #94a3b8;
            }
            
            input[type="file"]:active::file-selector-button {
                background-color: #94a3b8;
                color: #1e293b;
                border-color: #94a3b8;
            }
            
            /* Reset any forced dark mode styles */
            .form-control, input, select, textarea, option {
                color: #2c3e50 !important;
            }
            
            /* Fix for placeholder text */
            ::placeholder {
                color: #64748b !important;
                opacity: 1;
            }
        `;
    }
}

// Function to toggle between themes
function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Function to update the toggle icon
function updateToggleIcon(themeName) {
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        themeToggle.className = themeName === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Check for saved theme preference or respect OS setting
document.addEventListener('DOMContentLoaded', function() {
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // Apply saved theme
        setTheme(savedTheme);
    } else {
        // Check if user prefers dark mode at OS level
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDarkMode ? 'dark' : 'light');
    }
    
    // Attach event listener to theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Listen for OS theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        // Only update if user hasn't explicitly set a preference
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
    
    // Apply theme immediately to avoid flash of unstyled content
    const currentTheme = localStorage.getItem('theme') || 
                         (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    refreshThemeElements(currentTheme);
});