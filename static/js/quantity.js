
function increaseQuantity() {
    var quantityInput = document.getElementById('quantity');
    var currentValue = parseInt(quantityInput.value.trim()) || 0; 
    quantityInput.value = currentValue + 1;
}

function decreaseQuantity() {
    var quantityInput = document.getElementById('quantity');
    var currentValue = parseInt(quantityInput.value.trim()) || 1; 
    if (currentValue > 1) {
        quantityInput.value = currentValue - 1;
    }
}
