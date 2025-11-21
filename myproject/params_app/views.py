from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

from .models import ContactMessage

from .forms import ContactMessageForm


# from django.http import HttpResponse
def home(request):
    return render(request,"index.html")




def contact(request):
    return render(request, 'contact.html')
def dashboard_data(request):
    data = {
        "users": 140,
        "parkings": 140,
        "cars": 200,
    }
    return JsonResponse(data)
def about(request):
    return render(request, 'aboutus.html')
@login_required
def userin(request):
    return render(request, 'userin.html')
@login_required
def users(request):
    return render(request, 'users.html')
@login_required
def billings(request):
    return render(request, 'billings.html')
@login_required
def locations(request):
    return render(request, 'locations.html')
@login_required
def parkings(request):
    return render(request, 'parkings.html')
@login_required
def settings(request):
    return render(request, 'settings.html')
@login_required
def slots(request):
    return render(request, 'slots.html')
@login_required
def ticket(request):
    return render(request, 'ticket.html')
@login_required
def destination(request):
    return render(request, 'destination.html')


#just for qr code
# views.py
import qrcode
from django.http import HttpResponse


def generate_qr_code(request):
    data = "https://example.com"  # Replace this with your desired data

    # Generate QR code
    img = qrcode.make(data)

    # Save the image to a BytesIO object
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Return the image response
    return HttpResponse(buf, content_type="image/png")

#generating ticket

from django.shortcuts import render
from django.http import FileResponse
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
import datetime
import random

def generate_ticket(request):
    ticket_data = {
        'id': random.randint(1000, 9999),  # Random 4-digit ID
        'name': 'Happy Tumukunde',
        'parking_area': 'Makuza43',
        'duration': '4 hrs',
        'date': datetime.datetime.now().strftime('%d-%m-%Y'),
        'vehicle_plate': 'RAB8598J',
        'parking_slot': 'Makuza43',
        'time': '3:00 to 7:00 PM',
        'phone': '+250799999999'
    }

    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    # Title and logo
    c.drawString(250, 800, "PARMS")
    c.drawImage('C:/Users/user/Desktop/ParmsBackup ishpauline/ParmsBackup/myproject/params_app/static/imgs/TrafficJam.png', 100, 750, width=100, height=100)  # Adjust path to your logo image

    # Ticket content
    c.drawString(100, 700, f"Name: {ticket_data['name']}")
    c.drawString(100, 680, f"Parking Area: {ticket_data['parking_area']}")
    c.drawString(100, 660, f"Duration: {ticket_data['duration']}")
    c.drawString(100, 640, f"Date: {ticket_data['date']}")
    c.drawString(100, 620, f"Vehicle Plate: {ticket_data['vehicle_plate']}")
    c.drawString(100, 600, f"Parking Slot: {ticket_data['parking_slot']}")
    c.drawString(100, 580, f"Time: {ticket_data['time']}")
    c.drawString(100, 560, f"Phone: {ticket_data['phone']}")

    # Draw QR Code
    qr_data = f"https://example.com{ticket_data['id']}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create an image for the QR code
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image_path = '/Users/user/Desktop/ParmsBackup ishpauline/ParmsBackup/myproject/params_app/static/imgs/temp_qr.png'  # Temporary path to save the QR code image
    qr_image.save(qr_image_path)

    # Draw the QR code
    c.drawImage(qr_image_path, 250, 500, width=100, height=100)

    c.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename="ticket.pdf")



##user
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def signup(request):
    if request.method == 'POST':
        # Collect user input
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another one.")
            return redirect('signup')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered. Please use a different email.")
            return redirect('signup')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "User created successfully! You can now log in.")
        return redirect('login')

    return render(request, 'signup.html')



# Login View
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Get the user by email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email address.")
            return redirect('login')

        # Authenticate the user
        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            auth_login(request, user)

            # Redirect based on user role
            if user.is_staff:
                return redirect('dashboard')  # Admin redirected here
            else:
                return redirect('userin')  # Regular user redirected here

        else:
            messages.error(request, "Invalid password.")
            return redirect('login')

    return render(request, 'login.html')

# Admin Dashboard View
@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect('userin')  # If non-admin user tries to access the admin dashboard

    return render(request, 'dashboard.html')

# Regular User Page
@login_required
def userin(request):
    return render(request, 'userin.html')



def logout(request):
    auth_logout(request)  # Log out the user
    return redirect('home')  # Redirect to the 'home' page after logging out



# view  author paulina
# @login_required
# def create_vehicle(request):   
#     if request.method == 'POST':
#         form = VehicleForm(request.POST)
#         if form.is_valid():
#             vehicle = form.save(commit=False)
#             vehicle.car_owner = request.user
#             vehicle.save()
#             return redirect('vehicle_list')  
#     else:
#         form = VehicleForm()
#     return render(request, 'vehicles/create_vehicle.html', {'form': form})


# @login_required
# def list_vehicles(request):
    
    # vehicles = Vehicle.objects.all()  # Or use a custom filter if needed
    # return render(request, 'vehicles/list_vehicles.html', {'vehicles': vehicles})



def user_list(request):
    users = User.objects.all()  # Fetch all users
    return render(request, 'users.html', {'users': users})


def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('contact')  # Redirect to the same page or a success page
    else:
        form = ContactMessageForm()
    return render(request, 'contact.html', {'form': form})

def contact_messages_view(request):
    messages = ContactMessage.objects.all().order_by('-created_at')  # Fetch all contact messages
    return render(request, 'contact_messages.html', {'messages': messages})

#contact 
from django.shortcuts import render
from django.contrib import messages

def contact_us(request):
    if request.method == 'POST':
        # Collect form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Validate inputs
        if not full_name or not email or not message:
            messages.error(request, "All fields are required.")
            return render(request, 'contact.html')

        # Save or process the data (e.g., send an email or save to a database)
        # For now, just display a success message
        messages.success(request, "Your message has been sent successfully!")
        return render(request, 'contact.html')

    return render(request, 'contact.html')

