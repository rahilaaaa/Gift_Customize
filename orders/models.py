from django.db import models
from users.models import Customer
from products.models import Product, ProductVariant, ProductCustomization,Coupon
from django.contrib.auth.models import User

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
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)  # Add coupon field
    
    def get_total_price(self):
        return self.quantity * self.price

class Order(models.Model):
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders", verbose_name="Customer")
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default=PENDING, verbose_name="Order Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Price")
    shipping_address = models.TextField(verbose_name="Shipping Address")
    billing_address = models.TextField(verbose_name="Billing Address")
    payment_method = models.CharField(max_length=50, verbose_name="Payment Method")
    payment_status = models.CharField(max_length=50, verbose_name="Payment Status")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Shipping Cost")  # Add shipping_cost field
    
    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"
    
    def cancel_order(self):
        self.status = self.CANCELLED
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Order")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items", verbose_name="Product")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items", verbose_name="Variant")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    customization = models.OneToOneField(ProductCustomization, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Customization")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Coupon")

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in Order #{self.order.id}"

    def get_total_price(self):
        return self.quantity * self.price
    

class Wishlist(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"{self.user.username}'s Wishlist"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} in {self.wishlist.user.username}'s Wishlist"
    




        
