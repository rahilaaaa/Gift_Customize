from django.db import models
from users.models import Customer
from products.models import Product, ProductVariant,ProductCustomization

class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="cart", verbose_name="Customer")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def _str_(self):
        return f"Cart for {self.customer.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items", verbose_name="Product")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="cart_items", verbose_name="Variant")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    customization = models.OneToOneField(ProductCustomization, on_delete=models.SET_NULL, null=True, blank=True)

    def _str_(self):
        return f"{self.quantity} x {self.product.title} in {self.cart.customer.username}'s cart"

    def get_total_price(self):
        return self.quantity * self.price
