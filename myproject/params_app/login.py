from django.shortcuts import render, redirect
from .login import login_user

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect logged-in users to the dashboard

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = login_user(email, password, request)
        if user:
            return redirect('dashboard')  # Replace with your dashboard URL

    return render(request, 'login.html')
