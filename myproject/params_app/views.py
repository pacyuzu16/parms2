from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import ContactMessage, ParkingLot, Vehicle, ParkingSpace, ParkingTicket, Payment
from .forms import ContactMessageForm


# from django.http import HttpResponse
def home(request):
    return render(request,"index.html")




def contact(request):
    return render(request, 'contact.html')
def dashboard_data(request):
    from django.contrib.auth.models import User
    from .models import ParkingLot, Vehicle, ParkingTicket
    
    data = {
        "users": User.objects.count(),
        "parkings": ParkingLot.objects.count(),
        "cars": Vehicle.objects.count(),
        "tickets": ParkingTicket.objects.count(),
        "active_tickets": ParkingTicket.objects.filter(exit_time__isnull=True).count(),
    }
    return JsonResponse(data)
def about(request):
    return render(request, 'aboutus.html')
@login_required
def userin(request):
    return render(request, 'userin.html')
@login_required
def users(request):
    # This view is now handled by user_list function below
    return redirect('user_list')
@login_required
def billings(request):
    from .models import Payment, ParkingTicket
    from django.db.models import Sum
    
    payments = Payment.objects.select_related('ticket', 'ticket__vehicle').order_by('-date')
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get monthly revenue (current year)
    from django.utils import timezone
    current_year = timezone.now().year
    monthly_revenue = payments.filter(date__year=current_year).extra(
        select={'month': 'EXTRACT(month FROM date)'}
    ).values('month').annotate(total=Sum('amount')).order_by('month')
    
    context = {
        'payments': payments[:20],  # Last 20 payments
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_payments': payments.count(),
        'unpaid_tickets': ParkingTicket.objects.filter(payment__isnull=True).count(),
    }
    
    return render(request, 'billings.html', context)
@login_required
def locations(request):
    return render(request, 'locations.html')
@login_required
def parkings(request):
    from .models import ParkingLot, ParkingSpace
    
    parking_lots = ParkingLot.objects.all()
    parking_spaces = ParkingSpace.objects.select_related('parking_lot').all()
    
    context = {
        'parking_lots': parking_lots,
        'parking_spaces': parking_spaces,
        'total_lots': parking_lots.count(),
        'total_spaces': parking_spaces.count(),
        'occupied_spaces': parking_spaces.filter(is_occupied=True).count(),
        'available_spaces': parking_spaces.filter(is_occupied=False).count(),
    }
    
    return render(request, 'parkings.html', context)
@login_required
def settings(request):
    return render(request, 'settings.html')
@login_required
def slots(request):
    from .models import ParkingSpace, ParkingTicket
    
    parking_spaces = ParkingSpace.objects.select_related('parking_lot').all()
    recent_bookings = ParkingTicket.objects.select_related('parking_space', 'vehicle').order_by('-entry_time')[:10]
    
    context = {
        'parking_spaces': parking_spaces,
        'recent_bookings': recent_bookings,
        'total_spaces': parking_spaces.count(),
        'occupied_spaces': parking_spaces.filter(is_occupied=True).count(),
        'available_spaces': parking_spaces.filter(is_occupied=False).count(),
    }
    
    return render(request, 'slots.html', context)
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

    from .models import ParkingLot, Vehicle, ParkingTicket, Payment, ContactMessage, ParkingSpace
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Get comprehensive dashboard statistics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Revenue statistics
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_revenue = Payment.objects.filter(date__gte=last_30_days).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Ticket statistics
    total_tickets = ParkingTicket.objects.count()
    active_tickets = ParkingTicket.objects.filter(exit_time__isnull=True).count()
    completed_tickets = total_tickets - active_tickets
    
    # Popular parking lots
    popular_lots = ParkingLot.objects.annotate(
        ticket_count=Count('spaces__tickets')
    ).order_by('-ticket_count')[:5]
    
    context = {
        'total_users': User.objects.count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'regular_users': User.objects.filter(is_staff=False).count(),
        'total_parking_lots': ParkingLot.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_tickets': total_tickets,
        'active_tickets': active_tickets,
        'completed_tickets': completed_tickets,
        'total_payments': Payment.objects.count(),
        'total_messages': ContactMessage.objects.count(),
        'unread_messages': ContactMessage.objects.count(),  # All are unread by default
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'recent_tickets': ParkingTicket.objects.select_related('vehicle', 'parking_space').order_by('-entry_time')[:10],
        'recent_messages': ContactMessage.objects.order_by('-submitted_at')[:10],
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'popular_lots': popular_lots,
        'total_spaces': ParkingSpace.objects.count(),
        'occupied_spaces': ParkingSpace.objects.filter(is_occupied=True).count(),
        'available_spaces': ParkingSpace.objects.filter(is_occupied=False).count(),
    }

    return render(request, 'dashboard.html', context)

# Regular User Page
@login_required
def userin(request):
    from .models import Vehicle, ParkingTicket
    
    # Get user's vehicles and tickets
    user_vehicles = Vehicle.objects.filter(owner_name=request.user.get_full_name() or request.user.username)
    user_tickets = ParkingTicket.objects.filter(vehicle__in=user_vehicles).order_by('-entry_time')
    active_tickets = user_tickets.filter(exit_time__isnull=True)
    
    context = {
        'user_vehicles': user_vehicles,
        'user_tickets': user_tickets[:10],  # Last 10 tickets
        'active_tickets': active_tickets,
        'total_vehicles': user_vehicles.count(),
        'total_tickets': user_tickets.count(),
        'active_tickets_count': active_tickets.count(),
    }
    
    return render(request, 'userin.html', context)



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



@login_required
def user_list(request):
    if not request.user.is_staff:
        return redirect('userin')
        
    users = User.objects.all().order_by('-date_joined')
    staff_users = users.filter(is_staff=True)
    regular_users = users.filter(is_staff=False)
    
    context = {
        'users': users,
        'staff_users': staff_users,
        'regular_users': regular_users,
        'total_users': users.count(),
        'staff_count': staff_users.count(),
        'regular_count': regular_users.count(),
    }
    
    return render(request, 'users.html', context)


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

# ==================================================
# ADMIN CRUD OPERATIONS
# ==================================================

# Contact Messages Management
@login_required
def admin_contacts(request):
    """Admin view to manage all contact messages"""
    if not request.user.is_staff:
        return redirect('userin')
    
    messages = ContactMessage.objects.all().order_by('-submitted_at')
    
    context = {
        'messages': messages,
        'total_messages': messages.count(),
    }
    return render(request, 'admin/contacts.html', context)

@login_required
def admin_contact_detail(request, message_id):
    """View individual contact message with reply option"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.shortcuts import get_object_or_404
    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            message.delete()
            messages.success(request, 'Message deleted successfully!')
            return redirect('admin_contacts')
    
    return render(request, 'admin/contact_detail.html', {'message': message})

# Vehicle Management
@login_required
def admin_vehicles(request):
    """Admin view to manage all vehicles"""
    if not request.user.is_staff:
        return redirect('userin')
    
    vehicles = Vehicle.objects.all().order_by('-vehicle_id')
    
    context = {
        'vehicles': vehicles,
        'total_vehicles': vehicles.count(),
    }
    return render(request, 'admin/vehicles.html', context)

@login_required
def admin_vehicle_create(request):
    """Create new vehicle"""
    if not request.user.is_staff:
        return redirect('userin')
    
    if request.method == 'POST':
        plate_number = request.POST.get('plate_number')
        vehicle_type = request.POST.get('vehicle_type')
        owner_name = request.POST.get('owner_name')
        
        if Vehicle.objects.filter(plate_number=plate_number).exists():
            messages.error(request, 'Vehicle with this plate number already exists!')
        else:
            Vehicle.objects.create(
                plate_number=plate_number,
                vehicle_type=vehicle_type,
                owner_name=owner_name
            )
            messages.success(request, 'Vehicle created successfully!')
            return redirect('admin_vehicles')
    
    vehicle_types = ['Car', 'Motorcycle', 'Truck']
    return render(request, 'admin/vehicle_form.html', {'vehicle_types': vehicle_types})

@login_required
def admin_vehicle_edit(request, vehicle_id):
    """Edit existing vehicle"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.shortcuts import get_object_or_404
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            vehicle.delete()
            messages.success(request, 'Vehicle deleted successfully!')
            return redirect('admin_vehicles')
        else:
            vehicle.plate_number = request.POST.get('plate_number')
            vehicle.vehicle_type = request.POST.get('vehicle_type')
            vehicle.owner_name = request.POST.get('owner_name')
            vehicle.save()
            messages.success(request, 'Vehicle updated successfully!')
            return redirect('admin_vehicles')
    
    vehicle_types = ['Car', 'Motorcycle', 'Truck']
    context = {
        'vehicle': vehicle,
        'vehicle_types': vehicle_types,
        'is_edit': True
    }
    return render(request, 'admin/vehicle_form.html', context)

# Parking Lot Management
@login_required
def admin_parking_lots(request):
    """Admin view to manage parking lots"""
    if not request.user.is_staff:
        return redirect('userin')
    
    lots = ParkingLot.objects.all().order_by('-lot_id')
    
    context = {
        'lots': lots,
        'total_lots': lots.count(),
    }
    return render(request, 'admin/parking_lots.html', context)

@login_required
def admin_parking_lot_create(request):
    """Create new parking lot"""
    if not request.user.is_staff:
        return redirect('userin')
    
    if request.method == 'POST':
        location = request.POST.get('location')
        total_spaces = int(request.POST.get('total_spaces', 0))
        available_spaces = int(request.POST.get('available_spaces', 0))
        
        lot = ParkingLot.objects.create(
            location=location,
            total_spaces=total_spaces,
            available_spaces=available_spaces
        )
        
        # Create parking spaces for this lot
        space_types = ['Compact', 'Large', 'Electric Vehicle']
        for i in range(total_spaces):
            ParkingSpace.objects.create(
                parking_lot=lot,
                space_type=space_types[i % len(space_types)],
                is_occupied=False
            )
        
        messages.success(request, f'Parking lot created with {total_spaces} spaces!')
        return redirect('admin_parking_lots')
    
    return render(request, 'admin/parking_lot_form.html')

@login_required
def admin_parking_lot_edit(request, lot_id):
    """Edit existing parking lot"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.shortcuts import get_object_or_404
    lot = get_object_or_404(ParkingLot, lot_id=lot_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            lot.delete()
            messages.success(request, 'Parking lot deleted successfully!')
            return redirect('admin_parking_lots')
        else:
            lot.location = request.POST.get('location')
            lot.total_spaces = int(request.POST.get('total_spaces', 0))
            lot.available_spaces = int(request.POST.get('available_spaces', 0))
            lot.save()
            messages.success(request, 'Parking lot updated successfully!')
            return redirect('admin_parking_lots')
    
    context = {
        'lot': lot,
        'is_edit': True,
        'spaces': lot.spaces.all()
    }
    return render(request, 'admin/parking_lot_form.html', context)

# Ticket Management
@login_required
def admin_tickets(request):
    """Admin view to manage parking tickets"""
    if not request.user.is_staff:
        return redirect('userin')
    
    tickets = ParkingTicket.objects.select_related('vehicle', 'parking_space').order_by('-entry_time')
    
    # Filter options
    status = request.GET.get('status', 'all')
    if status == 'active':
        tickets = tickets.filter(exit_time__isnull=True)
    elif status == 'completed':
        tickets = tickets.filter(exit_time__isnull=False)
    
    context = {
        'tickets': tickets,
        'total_tickets': tickets.count(),
        'active_tickets': ParkingTicket.objects.filter(exit_time__isnull=True).count(),
        'completed_tickets': ParkingTicket.objects.filter(exit_time__isnull=False).count(),
        'current_status': status,
    }
    return render(request, 'admin/tickets.html', context)

@login_required
def admin_ticket_edit(request, ticket_id):
    """Edit parking ticket"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.shortcuts import get_object_or_404
    from decimal import Decimal
    
    ticket = get_object_or_404(ParkingTicket, ticket_id=ticket_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'complete':
            if not ticket.exit_time:
                from django.utils import timezone
                ticket.exit_time = timezone.now()
                ticket.fee = Decimal(request.POST.get('fee', '0'))
                ticket.save()
                messages.success(request, 'Ticket completed successfully!')
        elif action == 'delete':
            ticket.delete()
            messages.success(request, 'Ticket deleted successfully!')
            return redirect('admin_tickets')
        else:
            if request.POST.get('fee'):
                ticket.fee = Decimal(request.POST.get('fee'))
                ticket.save()
                messages.success(request, 'Ticket updated successfully!')
        
        return redirect('admin_tickets')
    
    context = {
        'ticket': ticket,
        'has_payment': hasattr(ticket, 'payment'),
    }
    return render(request, 'admin/ticket_detail.html', context)

# User Management
@login_required
def admin_users_management(request):
    """Enhanced user management"""
    if not request.user.is_staff:
        return redirect('userin')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Filter options
    user_type = request.GET.get('type', 'all')
    if user_type == 'staff':
        users = users.filter(is_staff=True)
    elif user_type == 'regular':
        users = users.filter(is_staff=False)
    
    context = {
        'users': users,
        'total_users': User.objects.count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'regular_count': User.objects.filter(is_staff=False).count(),
        'current_type': user_type,
    }
    return render(request, 'admin/users_management.html', context)

@login_required
def admin_user_edit(request, user_id):
    """Edit user permissions and details"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save()
            messages.success(request, f'User {"promoted to" if user.is_staff else "demoted from"} staff successfully!')
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f'User {"activated" if user.is_active else "deactivated"} successfully!')
        elif action == 'delete' and user != request.user:
            user.delete()
            messages.success(request, 'User deleted successfully!')
            return redirect('admin_users_management')
        
        return redirect('admin_users_management')
    
    # Get user's vehicles and tickets
    user_vehicles = Vehicle.objects.filter(owner_name__icontains=user.get_full_name() or user.username)
    user_tickets = ParkingTicket.objects.filter(vehicle__in=user_vehicles)
    
    context = {
        'user_profile': user,
        'user_vehicles': user_vehicles,
        'user_tickets': user_tickets,
        'is_current_user': user == request.user,
    }
    return render(request, 'admin/user_detail.html', context)

# Reports and Analytics
@login_required
def admin_reports(request):
    """Admin reports and analytics"""
    if not request.user.is_staff:
        return redirect('userin')
    
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Date range for reports
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    # Revenue reports
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    weekly_revenue = Payment.objects.filter(date__gte=last_7_days).aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_revenue = Payment.objects.filter(date__gte=last_30_days).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Usage statistics
    popular_lots = ParkingLot.objects.annotate(
        usage_count=Count('spaces__tickets')
    ).order_by('-usage_count')[:10]
    
    # Vehicle statistics
    vehicle_types = Vehicle.objects.values('vehicle_type').annotate(
        count=Count('vehicle_type')
    ).order_by('-count')
    
    # Payment method statistics
    payment_methods = Payment.objects.values('payment_method').annotate(
        count=Count('payment_method'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    context = {
        'total_revenue': total_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'popular_lots': popular_lots,
        'vehicle_types': vehicle_types,
        'payment_methods': payment_methods,
        'total_transactions': Payment.objects.count(),
        'avg_ticket_value': Payment.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
    }
    
    return render(request, 'admin/reports.html', context)

