// Simple script for mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.querySelector('.fa-bars').parentElement;
    const navLinks = document.querySelector('nav .hidden.md\\:flex');
    mobileMenuBtn.addEventListener('click', function() {
        // This would toggle a mobile menu in a real implementation
        alert('Mobile menu would open here in a full implementation');
        });
        // Add hover effect to recipe cards
        const recipeCards = document.querySelectorAll('.recipe-card');
        recipeCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.3)';
            });
            card.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
});