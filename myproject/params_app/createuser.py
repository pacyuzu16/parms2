# createuser.py
from django.contrib.auth.models import User
from django.contrib import messages

def create_user(username, email, password, confirm_password, request=None):
    if password != confirm_password:
        if request:
            messages.error(request, "Passwords do not match.")
        return False

    # Check if username or email already exists
    if User.objects.filter(username=username).exists():
        if request:
            messages.error(request, "Username already exists.")
        return False

    if User.objects.filter(email=email).exists():
        if request:
            messages.error(request, "Email already exists.")
        return False

    # Create the user
    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()
    if request:
        messages.success(request, "User registered successfully.")
    return user
