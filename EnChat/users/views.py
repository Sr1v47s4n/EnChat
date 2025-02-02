from .models import User, DEFAULT_PROFILE_PICS
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse


def register(request):
    if  request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        is_private = request.POST.get("is_private")
        profile_picture = request.POST.get("profile_picture")
        if not profile_picture or profile_picture not in DEFAULT_PROFILE_PICS:
            profile_picture = DEFAULT_PROFILE_PICS[0]
        if not username or not email or not password:
            return render(request, "users/register.html", {"error": "All fields are required", "profile_pics": DEFAULT_PROFILE_PICS})
        if User.objects.filter(username=username).exists():
            return render(request, "users/register.html", {"error": "Username is taken", "profile_pics": DEFAULT_PROFILE_PICS})
        if User.objects.filter(email=email).exists():
            return render(request, "users/register.html", {"error": "Email id already exists", "profile_pics": DEFAULT_PROFILE_PICS})
        User.objects.create_user(username, email, password, profile_picture, is_private)
        return redirect("login")
    return render(request, "users/register.html", {"profile_pics": DEFAULT_PROFILE_PICS})

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(email=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            messages.success(request, "You are now logged in")
            return redirect("conversations")
        return render(request, "users/login.html", {"error": "Invalid credentials"})
    return render(request, "users/login.html")

@login_required
def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You are now logged out")
    return redirect("login")

@login_required
def profile(request):
    print(request.user.is_private)
    return render(request, "users/profile.html", {"profile_pics": DEFAULT_PROFILE_PICS})


@login_required
def edit_profile(request):
    """Edit Profile via AJAX"""
    if request.method == "POST":
        username = request.POST.get("username")
        profile_picture = request.POST.get("profile_picture")
        private = request.POST.get("is_private")
        request.user.username = username
        request.user.profile_picture = profile_picture
        request.user.is_private = private if private else False
        request.user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})
