    // JavaScript to handle toggle functionality
    document.getElementById('review-tab').addEventListener('click', function (event) {
        event.preventDefault(); // Prevent default scrolling behavior
        const reviewContent = document.getElementById('review-content');
        if (reviewContent.style.display === 'none' || reviewContent.style.display === '') {
            reviewContent.style.display = 'block'; // Show the reviews section
        } else {
            reviewContent.style.display = 'none'; // Hide the reviews section
        }
    });