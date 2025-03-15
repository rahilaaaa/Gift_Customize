from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from users.models import Customer
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    description = models.TextField(null=True, blank=True, verbose_name="Description")  # Added description field

    
    def __str__(self):
        return self.name



class Product(models.Model):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

    PRIORITY_CHOICES = [
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="Product Title")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=LOW, verbose_name="Priority")
    
    # Change the category to a ForeignKey to Category model
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Category")
    default_variant = models.ForeignKey('ProductVariant', null=True, blank=True, on_delete=models.SET_NULL, related_name="default_for_product", verbose_name="Default Variant")
    is_active = models.BooleanField(default=True)  # Soft delete flag

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return self.title



class Offer(models.Model):
    CATEGORY_OFFER = 'category'
    PRODUCT_OFFER = 'product'
    
    OFFER_TYPE_CHOICES = [
        (CATEGORY_OFFER, 'Category '),
        (PRODUCT_OFFER, 'Product '),
    ]
    
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('blocked', 'Blocked'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    
    # Fields to store the type of object (Category or Product) and its ID
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    offer_name = models.CharField(max_length=255, verbose_name="Offer Name")
    offer_description = models.TextField(verbose_name="Offer Description")
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Offer Percentage")
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES, verbose_name="Offer Type")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return f"{self.offer_name} - {self.get_offer_type_display()}"
    
    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.CharField(max_length=50, null=True, blank=True, verbose_name="Color")
    size = models.CharField(max_length=50, null=True, blank=True, verbose_name="Size")
    quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="Quantity")
    liter = models.CharField(max_length=50, null=True, blank=True, verbose_name="Liter")
    viewflex = models.CharField(max_length=50, null=True, blank=True, verbose_name="Viewflex")
    charm = models.CharField(max_length=50, null=True, blank=True, verbose_name="Charm")
    charmImg = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="CharmImg")
    is_valid_combination = models.BooleanField(default=True)  # Add this field to mark valid combinations
    
    def __str__(self):
        variant = f"{self.color}" if self.color else ""
        variant += f" {self.size}" if self.size else ""
        variant += f" {self.liter}L" if self.liter else "" 
        return f"Variant of {self.product.title}: {variant.strip()}"
    
    def clean(self):
        super().clean()
        
        if self.product.category:
            category_name = self.product.category.name.upper()
            

            if category_name == "wallet":
                if self.size or self.liter:
                    raise ValidationError("For 'wallet' category, only 'color' and 'quantity' fields are allowed.")
            
            elif category_name == "3d_crystal":
                if self.color or self.liter:
                    raise ValidationError("For '3d_crystal' category, only 'size' and 'quantity' fields are allowed.")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures validation is run before saving
        super().save(*args, **kwargs)



class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Image")
    
    def __str__(self):
        return f"Image for {self.product.title}"




class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    name = models.CharField(max_length=255)  # User's name
    email = models.EmailField()  # User's email
    rating = models.PositiveSmallIntegerField()  # Rating (1-5 stars)
    review_text = models.TextField()  # Review content
    created_at = models.DateTimeField(default=now)  # Timestamp of the review

    def __str__(self):
        return f"Review by {self.name} for {self.product.name}"

    class Meta:
        ordering = ['-created_at']  # Latest reviews appear first


class Coupon(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    
    DISCOUNT_TYPES = [
        (PERCENT, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Coupon Code")
    discount_type = models.CharField(
        max_length=10, 
        choices=DISCOUNT_TYPES, 
        default=FIXED,
        verbose_name="Discount Type"
    )
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Discount Value"
    )
    valid_from = models.DateTimeField(default=timezone.now, verbose_name="Valid From")
    valid_to = models.DateTimeField(verbose_name="Valid To")
    active = models.BooleanField(default=True, verbose_name="Active")
    max_uses = models.PositiveIntegerField(default=1, verbose_name="Maximum Uses")
    total_uses = models.PositiveIntegerField(default=0, verbose_name="Total Uses")
    is_deleted = models.BooleanField(default=False, verbose_name="Deleted")
    
    # Relationships with Product and Category
    products = models.ManyToManyField(
        Product, 
        blank=True,
        related_name='coupons',
        verbose_name="Applicable Products"
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='coupons',
        verbose_name="Applicable Categories"
    )
    
    # Optional minimum purchase amount
    minimum_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Minimum Purchase Amount"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        self.code = self.code.upper()  # Convert code to lowercase before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (
            self.active and
            self.total_uses < self.max_uses and
            self.valid_from <= now <= self.valid_to
        )

    def apply_discount(self, amount):
        if self.discount_type == self.PERCENT:
            return amount * (self.discount_value / 100)
        return min(amount, self.discount_value)

    class Meta:
        ordering = ['-valid_from']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"





class CouponUsage(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="coupon_usages"
    )
    coupon = models.ForeignKey(
        Coupon, 
        on_delete=models.CASCADE, 
        related_name="coupon_usages"
    )
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"

    def __str__(self):
        return f"{self.user} used {self.coupon.code}"

class CustomizationOption(models.Model):
    IMAGE = 'image'
    TEXT = 'text'

    OPTION_TYPES = [
        (IMAGE, 'Image'),
        (TEXT, 'Text'),
    ]

    category = models.OneToOneField("Category", on_delete=models.CASCADE, related_name="customization_option", verbose_name="Category")
    option_type = models.CharField(max_length=10, choices=OPTION_TYPES, verbose_name="Option Type")

    def _str_(self):
        return f"Customization for {self.category.name}: {self.option_type}"


class ProductCustomization(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="customizations", verbose_name="Product")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customizations", verbose_name="Customer")
    customization_text = models.TextField(null=True, blank=True, verbose_name="Customization Text")
    customization_image = models.ImageField(upload_to='customizations/', null=True, blank=True, verbose_name="Customization Image")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def _str_(self):
        return f"Customization for {self.product.title} by {self.customer.username}"