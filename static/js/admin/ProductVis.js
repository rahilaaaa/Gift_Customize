document.querySelectorAll('.change-image-btn').forEach(button => {
    button.addEventListener('click', function() {
        const imageId = this.getAttribute('data-image'); // Get image number
        const fileInput = document.getElementById(`image${imageId}-input`);
        fileInput.style.display = fileInput.style.display === 'none' ? 'block' : 'none';
    });
});