function changeImage(image) {
    // Update main image
    document.getElementById('mainImage').src = image.src;

    // Remove 'active' class and styles from all small images
    let smallImages = document.querySelectorAll('.small-image');
    smallImages.forEach(function(img) {
        img.style.border = ''; // Remove border
        img.style.boxShadow = ''; // Remove glow effect
    });

    // Apply 'active' style to clicked image
    image.style.border = '2px solid #007bff'; // Blue border
    image.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.5)'; // Blue glow effect
} 