from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .forms import ProfileForm
import uuid
from .models import Profile


# ===========================
#        Login View
# ===========================
def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.error(request, 'User not found')
            return redirect('login')

        profile_obj = Profile.objects.filter(user=user_obj).first()
        if profile_obj is None:
            messages.error(request, 'Profile not found')
            return redirect('login')

        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

        if not profile_obj.is_verified:
            messages.error(request, 'User is not verified. Please confirm your email.')
            return redirect('login')

        if profile_obj.is_blocked:
            messages.error(request, 'User is blocked. Please contact support.')
            return redirect('login')

        login(request, user)
        return redirect('home')

    return render(request, 'login.html')


# ===========================
#       Register View
# ===========================
def register_attempt(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        username = request.POST.get('username')
        profile_name = request.POST.get('prf_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        user = User.objects.create(email=email, username=username)
        user.set_password(password1)
        user.save()

        auth_token = str(uuid.uuid4())
        profile = Profile.objects.create(
            user=user,
            auth_token=auth_token,
            profile_name=profile_name,  # Or any default image path
        )
        profile.save()

        send_verification_email(user, auth_token)
        messages.success(request, 'Account created! Please check your email to verify.')
        return redirect('login')

    return render(request, 'register.html')


# ===========================
#   Send Verification Email
# ===========================
def send_verification_email(user, token):
    subject = 'Verify your email address'
    verification_link = f"http://192.168.1.12:8000/accounts/verify/{token}"

    message = f"""
Hi {user.username},

Thank you for signing up! Please verify your email address to activate your account.

Click the link below to verify:
{verification_link}

If the above link doesn’t work, you can copy and paste it into your browser.

If you did not create an account, you can safely ignore this email.

Thanks,
The Message Me Team
"""

    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)


# ===========================
#      Verify Account
# ===========================

def verify(request, token):
    profile_obj = Profile.objects.filter(auth_token=token).first()

    if not profile_obj:
        # ✅ If token is totally invalid (doesn't exist)
        messages.error(request, 'This verification link is invalid or has already been used.')
        return redirect('register')

    # ✅ Check expiration time
    expiration_time = profile_obj.created_at + timedelta(minutes=15)
    if timezone.now() > expiration_time:
        messages.error(request, 'This verification link has expired. Please request a new one.')
        return redirect('resend_verification')  # redirect user to request new link

    if profile_obj.is_verified:
        messages.info(request, 'Your email is already verified. Please login.')
        return redirect('login')

    # ✅ Everything is good: verify the user
    profile_obj.is_verified = True
    profile_obj.auth_token = uuid.uuid4()  # Invalidate the token
    profile_obj.save()

    messages.success(request, 'Email verified successfully. You can now login.')
    return redirect('login')

# ===========================
#     Forgot Password
# ===========================
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        user = User.objects.filter(email=email).first()

        if user is None:
            messages.error(request, 'User not found')
            return redirect('forgot_password')

        profile = Profile.objects.filter(user=user).first()

        if not profile or not profile.is_verified:
            messages.error(request, 'User is not verified.')
            return redirect('forgot_password')

        profile.auth_token = str(uuid.uuid4())
        profile.created_at = timezone.now()
        profile.save()

        send_forgot_password_link(user, profile.auth_token)
        messages.success(request, 'Password reset link has been sent to your email.')
        return redirect('login')

    return render(request, 'forgot_password.html')


# ===========================
#   Send Forgot Password Link
# ===========================
def send_forgot_password_link(user, token):
    subject = 'Reset Your Password'
    reset_link = f"http://192.168.1.12:8000/accounts/reset-password/{token}"

    message = f"""
Hi {user.username},

We received a request to reset your password.

Click the link below to reset your password:
{reset_link}

If you did not request this, simply ignore this email.

Thanks,
The Message Me Team
"""

    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)


# ===========================
#     Reset Password View
# ===========================
def reset_password(request, token):
    profile = Profile.objects.filter(auth_token=token).first()

    if not profile:
        messages.error(request, 'This password reset link is invalid or has already been used.')
        return redirect('forgot_password')

    expiration_time = profile.created_at + timedelta(minutes=15)
    if timezone.now() > expiration_time:
        messages.error(request, 'This password reset link has expired. Please try again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('conf_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('reset_password', token=token)

        user = profile.user
        user.set_password(password)
        user.save()

        profile.auth_token = uuid.uuid4()  # Invalidate token
        profile.created_at = timezone.now()
        profile.save()

        messages.success(request, 'Password changed successfully. Please login.')
        return redirect('login')

    return render(request, 'reset_password.html')




@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})


def logout_attempt(request):
    logout(request.user)
    return redirect('login')