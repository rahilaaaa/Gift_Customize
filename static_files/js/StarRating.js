 // Star rating functionality
 const stars = document.querySelectorAll('#star-rating i');
 let selectedRating = 0;

 stars.forEach((star, index) => {
   

     // Highlight stars on hover
     star.addEventListener('mouseover', () => {
         highlightStars(index);
     });

     // Reset stars on mouseout
     star.addEventListener('mouseout', () => {
         highlightStars(selectedRating - 1);
     });

     // Select stars on click
     star.addEventListener('click', () => {
         selectedRating = index + 1;
         highlightStars(index);
     });
 });

 // Function to highlight stars up to a given index
 function highlightStars(index) {
     stars.forEach((star, i) => {
         if (i <= index) {
             star.classList.remove('far'); // Empty star
             star.classList.add('fas');   // Filled star
         } else {
             star.classList.remove('fas'); // Filled star
             star.classList.add('far');   // Empty star
         }
     });
    }