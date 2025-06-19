document.addEventListener('DOMContentLoaded', function() {
    console.log('Flask app loaded successfully');
    
    // Add any JavaScript functionality here
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            console.log('Form submitted');
        });
    });
});
