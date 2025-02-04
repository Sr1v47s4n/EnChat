from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from .models import User, DEFAULT_PROFILE_PICS


def register_user(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        is_private = request.POST.get("is_private") == "on"
        profile_picture = request.POST.get("profile_picture")

        # Validate required fields
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        # Validate profile picture selection
        if profile_picture not in DEFAULT_PROFILE_PICS:
            profile_picture = DEFAULT_PROFILE_PICS[0]

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect("register")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.profile_picture = profile_picture
        user.is_private = is_private
        user.save()

        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login")

    return render(
        request, "users/register.html", {"profile_pics": DEFAULT_PROFILE_PICS}
    )


def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        # Retrieve user by email
        user = User.objects.filter(email=email).first()
        if user:
            user = authenticate(email=email, password=password)

        if user:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("conversations")

        messages.error(request, "Invalid email or password.")
        return redirect("login")

    return render(request, "users/login.html")


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@login_required
def user_profile(request):
    return render(request, "users/profile.html", {"profile_pics": DEFAULT_PROFILE_PICS})


@login_required
def edit_profile(request):
    """Handles AJAX profile edits."""
    if request.method == "POST":
        new_username = request.POST.get("username", "").strip()
        new_profile_picture = request.POST.get("profile_picture")
        is_private = request.POST.get("is_private") == "on"

        # Ensure username is not empty
        if not new_username:
            return JsonResponse(
                {"success": False, "error": "Username cannot be empty."}
            )

        # Ensure username is unique if changed
        if (
            new_username != request.user.username
            and User.objects.filter(username=new_username).exists()
        ):
            return JsonResponse(
                {"success": False, "error": "Username is already taken."}
            )

        # Validate profile picture
        if new_profile_picture not in DEFAULT_PROFILE_PICS:
            new_profile_picture = DEFAULT_PROFILE_PICS[0]

        # Update user profile
        request.user.username = new_username
        request.user.profile_picture = new_profile_picture
        request.user.is_private = is_private
        request.user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request."})
