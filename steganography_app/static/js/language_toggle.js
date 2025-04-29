document.addEventListener('DOMContentLoaded', function() {
    // Create the language toggle HTML
    const toggleHTML = `
        <div class="language-toggle">
            <span class="toggle-label english-text">English</span>
            <label class="toggle-switch">
                <input type="checkbox" id="languageToggle">
                <span class="toggle-slider"></span>
            </label>
            <span class="toggle-label english-text">Hinglish</span>
            <span class="toggle-label hinglish-text">English</span>
        </div>
    `;

    // Insert the toggle at the top of the body
    document.body.insertAdjacentHTML('afterbegin', toggleHTML);

    // Get the toggle element
    const languageToggle = document.getElementById('languageToggle');

    // Add event listener to the toggle
    languageToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('hinglish-mode');
            localStorage.setItem('language', 'hinglish');
        } else {
            document.body.classList.remove('hinglish-mode');
            localStorage.setItem('language', 'english');
        }
    });

    // Check if user has a language preference stored
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage === 'hinglish') {
        languageToggle.checked = true;
        document.body.classList.add('hinglish-mode');
    }
    
    // Add an initial animation to draw attention to the toggle
    const toggleElement = document.querySelector('.language-toggle');
    setTimeout(() => {
        toggleElement.style.transform = 'scale(1.1)';
        setTimeout(() => {
            toggleElement.style.transform = 'scale(1)';
        }, 500);
    }, 1000);
});
