from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class Customer(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=15, verbose_name="Phone Number", blank=True, null=True)
    is_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    is_blocked  = models.BooleanField(default=False, verbose_name="Blocked Status")
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)  # Referral code
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    otp = models.CharField(max_length=128, blank=True, null=True)  # Store hashed OTP
    otp_created_at = models.DateTimeField(blank=True, null=True)  # Track OTP creation time
    failed_login_attempts = models.PositiveIntegerField(default=0)
    lockout_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"




class ReferralOffer(models.Model):
    """
    Model to store referral offers.
    """
    # Offer details
    offer_name = models.CharField(max_length=100, unique=True, verbose_name="Offer Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Amount credited to the referrer and referred user
    referrer_reward = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Referrer Reward"
    )
    referred_reward = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Referred User Reward"
    )
    
    # Offer validity
    start_date = models.DateTimeField(default=timezone.now, verbose_name="Start Date")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="End Date")
    
    # Offer status
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    def __str__(self):
        return f"{self.offer_name} (Active: {self.is_active})"

    class Meta:
        verbose_name = "Referral Offer"
        verbose_name_plural = "Referral Offers"

    def is_valid(self):
        """
        Check if the offer is currently valid.
        """
        now = timezone.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now
    


class Referral(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='referral')
    code = models.CharField(max_length=10, unique=True)  # Referral code
    referred_users = models.ManyToManyField(Customer, related_name='referred_by', blank=True)  # Users referred by this user
    offer = models.ForeignKey(ReferralOffer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Referral Offer")  # Link to the referral offer

    def __str__(self):
        return f"{self.user.username} - {self.code}"

    def generate_referral_code(self):
        """Generates a unique referral code."""
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return code
    


class Wallet(models.Model):
    """
    Wallet model to store the balance for each user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Links to the User model (Customer in your case)
        on_delete=models.CASCADE,  # Delete wallet if the user is deleted
        related_name='wallet'      # Allows access via user.wallet
    )
    balance = models.DecimalField(
        max_digits=10,             # Maximum digits (including decimal places)
        decimal_places=2,          # Two decimal places (e.g., 1000.00)
        default=0.00,             # Default balance is 0.00
        validators=[MinValueValidator(0.00)]  # Ensure balance cannot be negative
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.user.username}'s Wallet (Balance: ₹{self.balance})"

    def add_funds(self, amount):
        """
        Adds funds to the wallet.
        """
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        self.balance += amount
        self.save()

    def deduct_funds(self, amount):
        """
        Deducts funds from the wallet.
        """
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if self.balance < amount:
            raise ValidationError("Insufficient balance.")
        self.balance -= amount
        self.save()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    otp = models.CharField(max_length=128, blank=True, null=True)  # Store hashed OTP

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.user.username} - {self.status}"


    
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100, verbose_name="Name")
    mobile = models.CharField(max_length=15, verbose_name="Mobile Number")
    country = models.CharField(max_length=100, verbose_name="Country")
    state = models.CharField(max_length=100, verbose_name="State")
    city = models.CharField(max_length=100, verbose_name="City")
    street = models.CharField(max_length=255, verbose_name="Street Address")
    pincode = models.CharField(max_length=20, verbose_name="Pincode", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True)  # Mark active/inactive

    def __str__(self):
        return f"{self.name}'s Address - {self.city}, {self.state}, {self.country}"

    def full_address(self):
        return f"{self.name}, {self.street}, {self.city}, {self.state}, {self.country}, {self.pincode}"
        
    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

        