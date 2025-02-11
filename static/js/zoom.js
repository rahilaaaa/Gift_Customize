const mainImage = document.getElementById('mainImage');
    const imageZoomContainer = document.getElementById('imageZoomContainer');

    // Zoom on hover and move the zoom area
    imageZoomContainer.addEventListener('mousemove', function(e) {
        const zoomContainerRect = imageZoomContainer.getBoundingClientRect();
        const x = e.clientX - zoomContainerRect.left;
        const y = e.clientY - zoomContainerRect.top;
        const xPercent = (x / zoomContainerRect.width) * 100;
        const yPercent = (y / zoomContainerRect.height) * 100;

        mainImage.style.transformOrigin = `${xPercent}% ${yPercent}%`;
        mainImage.style.transform = 'scale(1.5)';
    });

    // Reset the zoom when mouse leaves the container
    imageZoomContainer.addEventListener('mouseleave', function() {
        mainImage.style.transformOrigin = 'center center';
        mainImage.style.transform = 'scale(1)';
    });