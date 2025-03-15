
    // Function to filter products by category
    function filterProducts() {
        const selectedCategory = document.getElementById('categoryDropdown').value;
        const selectedDate = document.getElementById('dateFilter').value;
        const url = new URL(window.location.href);
        url.searchParams.set('category', selectedCategory);
        if (selectedDate) {
            url.searchParams.set('date', selectedDate);  // Add date filter to URL
        } else {
            url.searchParams.delete('date');  // Remove date filter if not selected
        }
        window.location.href = url.toString();
    }

    // Function to filter products by date
    function filterProductsByDate() {
        const selectedCategory = document.getElementById('categoryDropdown').value;
        const selectedDate = document.getElementById('dateFilter').value;
        const url = new URL(window.location.href);
        url.searchParams.set('category', selectedCategory);
        if (selectedDate) {
            url.searchParams.set('date', selectedDate);  // Add date filter to URL
        } else {
            url.searchParams.delete('date');  // Remove date filter if not selected
        }
        window.location.href = url.toString();
    }
