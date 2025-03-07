function toggleCoupons() {
    const couponsSection = document.getElementById('couponsSection');
    if (couponsSection.style.display === 'none' || couponsSection.style.display === '') {
        couponsSection.style.display = 'block';
    } else {
        couponsSection.style.display = 'none';
    }
}