const charms = document.querySelectorAll('.charm-item');
charms.forEach(item => {
    item.addEventListener('click', function() {
        charms.forEach(item => item.querySelector('.charm').style.border = '2px solid transparent');
        this.querySelector('.charm').style.border = '2px solid #007bff'; // Active state color
    });
});