from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
import random
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.views.decorators.cache import never_cache,cache_control
from django.utils.timezone import now, timedelta
from datetime import datetime
from .models import Customer
from .models import Address
from .forms import AddressForm  # Assuming you have a form for adding addresses



# Generate a 4-digit OTP
def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Field validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('register')

        # Create user and send OTP
        user = User.objects.create_user(username=username, email=email, phone=phone, password=password)
        otp = generate_otp()
        user.otp = make_password(otp)  # Hash the OTP
        user.otp_created_at = timezone.now()
        user.is_verified = False
        user.save()

        # Send OTP via email
        send_mail(
            'Your OTP Code',
            f'Your OTP code is: {otp}',
            'meherjk68@gmail.com',
            [email],
            fail_silently=False,
        )

        # Store email in session
        request.session['email'] = email

        messages.success(request, "Account created successfully! Please verify your email.")
        return redirect('otp_verification')
    

    return render(request, 'users/account_register.html')


@never_cache
def logout_view(request):
    logout(request)  # Logs out the user by clearing the session
    messages.success(request, "You have been logged out successfully.")  # Show a logout success message
    return redirect('login_user')  # Redirect to the login page or home page



def otp_verification(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        email = request.session.get('email', None)
        if not email:
            messages.error(request, "Email is required to verify OTP.")
            return redirect('register')

        user = get_user_model().objects.filter(email=email).first()

        if not user:
            messages.error(request, "Email not registered.")
        elif user.is_verified:
            messages.info(request, "Your email is already verified. Please login.")
        elif timezone.now() > user.otp_created_at + timedelta(seconds=60):  # OTP expires in 1 minutes
            messages.error(request, "OTP expired. Please request a new one.")
        elif not check_password(entered_otp, user.otp):
            messages.error(request, "Incorrect OTP. Please try again.")
        else:
            user.is_verified = True
            user.save()
            messages.success(request, "Email verified successfully! Please log in.")
            return redirect('login_user')

        return render(request, 'users/otp_verification.html', {"email": email})

    email = request.session.get('email', '')
    return render(request, 'users/otp_verification.html', {"email": email})

def resend_otp(request):
    email = request.session.get('email', None)  # Retrieve email from session
    if not email:
        messages.error(request, "Email not found.")
        return redirect('register')  # Redirect to registration page if no email in session

    user = get_user_model().objects.filter(email=email).first()  # Fetch user by email

    if not user:
        messages.error(request, "Email not registered.")
    else:
        otp = generate_otp()  # Generate new OTP
        user.otp = make_password(otp)  # Hash the OTP
        user.otp_created_at = timezone.now()  # Set the new OTP creation time
        user.save()  # Save the updated OTP

        # Send OTP via email
        send_mail(
            'Your New OTP Code',
            f'Your new OTP code is: {otp}',
            'meherjk68@gmail.com',
            [email],  # Send to the user's email
            fail_silently=False,
        )
        messages.success(request, "A new OTP has been sent to your email.")

    return redirect('otp_verification')  # Redirect back to OTP verification page



User = get_user_model()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # reset_url = request.build_absolute_uri(
            #     f'/reset_password/{uid}/{token}/'
            # )
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[uid, token]))

            send_mail(
                'Reset Your Password',
                f'Click the link to reset your password: {reset_url}',
                'meherjk68@gmail.com',
                [email],
                fail_silently=False,
            )
            return render(request, 'users/reset_password_form.html', {
                'message': 'A password reset link has been sent to your email.'
            })
        except User.DoesNotExist:
            return render(request, 'users/reset_password_form.html', {
                'error': 'Email not found'
            })
    return render(request, 'users/reset_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        if not default_token_generator.check_token(user, token):
            return render(request, 'users/reset_password_form.html', {
                'message': 'The password reset link is invalid or has expired.'
            })
    except (User.DoesNotExist, ValueError, TypeError):
        return render(request, 'users/reset_password_form.html', {
            'message': 'The password reset link is invalid or has expired.'
        })

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            user.password = make_password(new_password)
            user.save()
            return render(request, 'users/reset_password_form.html', {
                'message': 'Your password has been successfully reset. You can now log in with the new password.'
            })
        else:
            return render(request, 'users/reset_password_form.html', {
                'error': 'Passwords do not match.',
                'uidb64': uidb64,
                'token': token,
            })
    return render(request, 'users/reset_password_form.html', {
        'uidb64': uidb64,
        'token': token,
    })


def profile(request):
    addresses = Address.objects.filter(user=request.user)
    form = AddressForm()

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('profile')

    context = {
        'addresses': addresses,
        'form': form
    }
    return render(request, 'users/profile/profile.html', context)

def add_new_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user  # Associate the address with the logged-in user
            address.save()
            return redirect('profile')  # Redirect back to profile or address list
    else:
        form = AddressForm()

    return render(request, 'users/profile/address/add_address.html', {'form': form})

def edit_address(request, pk):
    address = get_object_or_404(Address, pk=pk)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('profile')
    else:
        form = AddressForm(instance=address)
    return render(request, 'users/profile/address/edit_address.html', {'form': form})

def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully.')
        return redirect('profile')
    return render(request, 'users/profile/address/delete_address_confirm.html', {'address': address})

@never_cache
def login_view(request):  
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect('login_user')

        # Check if user is locked out
        if user.lockout_until and user.lockout_until > now():
            messages.error(request, "You have reached your login attempt limit. Please try again after 24 hours.")
            return redirect('login_user')

        user_auth = authenticate(request, email=email, password=password)

        if user_auth is not None:
            if user_auth.is_active == False:
                messages.error(request, "Your account has been blocked. Please contact support.")
                return redirect('login_user')
            
           

            if user_auth.is_verified:
                user.failed_login_attempts = 0  # Reset on successful login
                user.lockout_until = None
                user.save()
                login(request, user_auth)
                messages.success(request, "Successfully logged in.")
                return redirect('home')
            else:
                messages.error(request, "Your email is not verified. Please verify your email first.")
                return redirect('otp_verification')
        else:
            # Handle failed login attempt
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= 3:
                user.lockout_until = now() + timedelta(hours=24)
                user.save()
                messages.error(request, "You have reached your login attempt limit. Please try again after 24 hours.")
            else:
                user.save()
                messages.error(request, "Invalid email or password. Please try again.")

            return redirect('login_user')

    return render(request, 'users/account_login.html')
 

def contact(request):
    return render(request, 'users/contact.html')

