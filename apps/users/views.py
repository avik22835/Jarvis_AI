# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
import uuid
import secrets
import string

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')

def guest_login_view(request):
    """✅ ONE-CLICK GUEST LOGIN FOR JUDGES - FIXED VERSION"""
    # Generate random username
    username = f"guest_{uuid.uuid4().hex[:8]}"
    
    # Generate random password (FIXED - no more make_random_password)
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    # Create guest user
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name="Guest",
        last_name="User"
    )
    
    # Log them in immediately
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    
    messages.success(request, f"Welcome, Guest! Logged in as {username}")
    return redirect('home')
