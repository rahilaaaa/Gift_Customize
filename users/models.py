from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class Customer(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=15, verbose_name="Phone Number", blank=True, null=True)
    is_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    is_blocked  = models.BooleanField(default=False, verbose_name="Blocked Status")  
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

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    otp = models.CharField(max_length=128, blank=True, null=True)  # Store hashed OTP

    def __str__(self):
        return f"{self.user.username}'s Profile"




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

    def __str__(self):
        return f"{self.name}'s Address - {self.city}, {self.state}, {self.country}"

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

        