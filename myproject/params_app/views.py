from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import qrcode, datetime, random

from .models import ContactMessage, ParkingLot, Vehicle, ParkingSpace, ParkingTicket, Payment
from .forms import ContactMessageForm


# ── helpers ────────────────────────────────────────────────────────────────────

def _admin_required(view_func):
    """Decorator: login required + staff only, else redirect to userin."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to access that page.")
            return redirect('userin')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Public views ───────────────────────────────────────────────────────────────

def home(request):
    return render(request, "index.html")


def about(request):
    return render(request, 'aboutus.html')


def contact_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('name') or request.POST.get('full_name', '')
        email     = request.POST.get('email', '')
        subject   = request.POST.get('subject', '')
        message   = request.POST.get('message', '')

        if not full_name or not email or not message:
            messages.error(request, "Please fill in all required fields.")
        else:
            ContactMessage.objects.create(
                full_name=full_name,
                email=email,
                message=f"[{subject}] {message}" if subject else message,
            )
            messages.success(request, "Your message has been sent! We'll get back to you within 24 hours.")
            return redirect('contact')

    return render(request, 'contact.html')


# ── Auth views ─────────────────────────────────────────────────────────────────

def signup(request):
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        email            = request.POST.get('email', '').strip()
        password         = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('signup')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created! You can now log in.")
        return redirect('login')

    return render(request, 'signup.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if request.user.is_staff else 'userin')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with that email address.")
            return redirect('login')

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard' if user.is_staff else 'userin')

        messages.error(request, "Incorrect password.")
        return redirect('login')

    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    return redirect('home')


# ── API ────────────────────────────────────────────────────────────────────────

def dashboard_data(request):
    data = {
        "users":          User.objects.count(),
        "parkings":       ParkingLot.objects.count(),
        "cars":           Vehicle.objects.count(),
        "tickets":        ParkingTicket.objects.count(),
        "active_tickets": ParkingTicket.objects.filter(exit_time__isnull=True).count(),
    }
    return JsonResponse(data)


# ── Admin dashboard (SPA) ──────────────────────────────────────────────────────

@_admin_required
def dashboard(request):
    today        = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days  = today - timedelta(days=7)

    # Revenue
    total_revenue   = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_revenue = Payment.objects.filter(date__gte=last_30_days).aggregate(Sum('amount'))['amount__sum'] or 0
    weekly_revenue  = Payment.objects.filter(date__gte=last_7_days).aggregate(Sum('amount'))['amount__sum'] or 0

    # Tickets
    all_tickets       = ParkingTicket.objects.select_related('vehicle', 'parking_space__parking_lot').order_by('-entry_time')
    active_tickets    = all_tickets.filter(exit_time__isnull=True)
    completed_tickets = all_tickets.filter(exit_time__isnull=False)

    # Spaces
    all_spaces       = ParkingSpace.objects.select_related('parking_lot')
    occupied_spaces  = all_spaces.filter(is_occupied=True)
    available_spaces = all_spaces.filter(is_occupied=False)

    # Lists
    all_vehicles = Vehicle.objects.all().order_by('-vehicle_id')
    all_lots     = ParkingLot.objects.annotate(ticket_count=Count('spaces__tickets')).order_by('-lot_id')
    all_users    = User.objects.all().order_by('-date_joined')
    all_messages = ContactMessage.objects.all().order_by('-submitted_at')

    # Reports
    vehicle_type_stats  = Vehicle.objects.values('vehicle_type').annotate(count=Count('vehicle_type')).order_by('-count')
    payment_method_stats = Payment.objects.values('payment_method').annotate(
        count=Count('payment_method'), total_amount=Sum('amount')
    ).order_by('-total_amount')
    popular_lots = ParkingLot.objects.annotate(usage_count=Count('spaces__tickets')).order_by('-usage_count')[:8]

    context = {
        'active_tab': request.GET.get('tab', 'overview'),

        # Overview numbers
        'total_users':             all_users.count(),
        'staff_users':             all_users.filter(is_staff=True).count(),
        'regular_users':           all_users.filter(is_staff=False).count(),
        'total_parking_lots':      all_lots.count(),
        'total_vehicles':          all_vehicles.count(),
        'total_tickets':           ParkingTicket.objects.count(),
        'active_tickets':          active_tickets.count(),
        'completed_tickets_count': completed_tickets.count(),
        'total_messages':          all_messages.count(),
        'total_revenue':           total_revenue,
        'monthly_revenue':         monthly_revenue,
        'weekly_revenue':          weekly_revenue,
        'total_spaces':            all_spaces.count(),
        'occupied_spaces':         occupied_spaces.count(),
        'available_spaces':        available_spaces.count(),

        # Recent
        'recent_tickets':  all_tickets[:8],
        'recent_messages': all_messages[:5],
        'recent_users':    all_users[:5],

        # Full section lists (capped for performance)
        'all_tickets':  all_tickets[:200],
        'all_vehicles': all_vehicles[:200],
        'all_lots':     all_lots,
        'all_users':    all_users,
        'all_messages': all_messages,
        'active_ticket_list': active_tickets,

        # Form helpers
        'vehicle_types': ['Car', 'Motorcycle', 'Truck'],

        # Reports
        'popular_lots':          popular_lots,
        'vehicle_type_stats':    vehicle_type_stats,
        'payment_method_stats':  payment_method_stats,
        'avg_ticket_value':      Payment.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
        'total_transactions':    Payment.objects.count(),
    }
    return render(request, 'dashboard.html', context)


@_admin_required
def update_settings(request):
    """Handle settings form POST from the dashboard settings tab."""
    if request.method == 'POST':
        user = request.user
        new_username = request.POST.get('username', '').strip()
        new_email    = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '').strip()

        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                messages.error(request, "Username already taken.")
            else:
                user.username = new_username

        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                messages.error(request, "Email already registered.")
            else:
                user.email = new_email

        if new_password:
            user.set_password(new_password)
            messages.success(request, "Password updated. Please log in again.")

        user.save()
        if not new_password:
            messages.success(request, "Settings saved successfully.")

    return redirect('/dashboard/?tab=settings')


# ── Settings page (redirect to dashboard tab) ──────────────────────────────────

@_admin_required
def settings(request):
    return redirect('/dashboard/?tab=settings')


# ── Regular user views ─────────────────────────────────────────────────────────

@login_required
def userin(request):
    owner_name   = request.user.get_full_name() or request.user.username
    user_vehicles = Vehicle.objects.filter(owner_name__iexact=owner_name)
    user_tickets  = ParkingTicket.objects.filter(vehicle__in=user_vehicles).order_by('-entry_time')
    active        = user_tickets.filter(exit_time__isnull=True)

    context = {
        'user_vehicles':       user_vehicles,
        'user_tickets':        user_tickets[:10],
        'active_tickets':      active,
        'total_vehicles':      user_vehicles.count(),
        'total_tickets':       user_tickets.count(),
        'active_tickets_count': active.count(),
    }
    return render(request, 'userin.html', context)


@login_required
def billings(request):
    if request.user.is_staff:
        payments = Payment.objects.select_related('ticket__vehicle').order_by('-date')
    else:
        owner      = request.user.get_full_name() or request.user.username
        vehicles   = Vehicle.objects.filter(owner_name__iexact=owner)
        tickets    = ParkingTicket.objects.filter(vehicle__in=vehicles)
        payments   = Payment.objects.filter(ticket__in=tickets).select_related('ticket__vehicle').order_by('-date')

    total_revenue  = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    current_year   = timezone.now().year
    monthly_data   = payments.filter(date__year=current_year).extra(
        select={'month': 'EXTRACT(month FROM date)'}
    ).values('month').annotate(total=Sum('amount')).order_by('month')

    context = {
        'payments':        payments[:50],
        'total_revenue':   total_revenue,
        'monthly_revenue': monthly_data,
        'total_payments':  payments.count(),
        'unpaid_tickets':  ParkingTicket.objects.filter(payment__isnull=True).count(),
    }
    return render(request, 'billings.html', context)


@login_required
def locations(request):
    return render(request, 'locations.html')


@login_required
def parkings(request):
    lots   = ParkingLot.objects.all()
    spaces = ParkingSpace.objects.select_related('parking_lot').all()
    context = {
        'parking_lots':      lots,
        'parking_spaces':    spaces,
        'total_lots':        lots.count(),
        'total_spaces':      spaces.count(),
        'occupied_spaces':   spaces.filter(is_occupied=True).count(),
        'available_spaces':  spaces.filter(is_occupied=False).count(),
    }
    return render(request, 'parkings.html', context)


@login_required
def slots(request):
    spaces   = ParkingSpace.objects.select_related('parking_lot').all()
    bookings = ParkingTicket.objects.select_related('parking_space', 'vehicle').order_by('-entry_time')[:10]
    context = {
        'parking_spaces':  spaces,
        'recent_bookings': bookings,
        'total_spaces':    spaces.count(),
        'occupied_spaces': spaces.filter(is_occupied=True).count(),
        'available_spaces': spaces.filter(is_occupied=False).count(),
    }
    return render(request, 'slots.html', context)


@login_required
def ticket(request):
    return render(request, 'ticket.html')


@login_required
def destination(request):
    return render(request, 'destination.html')


@login_required
def user_list(request):
    if not request.user.is_staff:
        return redirect('userin')
    return redirect('/dashboard/?tab=users')


# ── QR / Ticket generation ─────────────────────────────────────────────────────

def generate_qr_code(request):
    img = qrcode.make("https://parms.app")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf, content_type="image/png")


def generate_ticket(request):
    ticket_data = {
        'id':            random.randint(1000, 9999),
        'name':          'PARMS User',
        'parking_area':  'Zone 01',
        'duration':      '2 hrs',
        'date':          datetime.datetime.now().strftime('%d-%m-%Y'),
        'vehicle_plate': 'RAB 0000',
        'time':          '10:00 – 12:00',
        'phone':         '+250 700 000 000',
    }

    from reportlab.pdfgen import canvas
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(250, 800, "PARMS Parking Ticket")
    c.drawString(100, 750, f"Ticket ID : {ticket_data['id']}")
    c.drawString(100, 730, f"Name      : {ticket_data['name']}")
    c.drawString(100, 710, f"Location  : {ticket_data['parking_area']}")
    c.drawString(100, 690, f"Plate     : {ticket_data['vehicle_plate']}")
    c.drawString(100, 670, f"Duration  : {ticket_data['duration']}")
    c.drawString(100, 650, f"Date      : {ticket_data['date']}")
    c.drawString(100, 630, f"Time      : {ticket_data['time']}")
    c.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="parms_ticket.pdf")


# ── Admin CRUD — Contacts ──────────────────────────────────────────────────────

@_admin_required
def admin_contacts(request):
    return redirect('/dashboard/?tab=messages')


@_admin_required
def admin_contact_detail(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        msg.delete()
        messages.success(request, 'Message deleted.')
    return redirect('/dashboard/?tab=messages')


# ── Admin CRUD — Vehicles ──────────────────────────────────────────────────────

@_admin_required
def admin_vehicles(request):
    return redirect('/dashboard/?tab=vehicles')


@_admin_required
def admin_vehicle_create(request):
    if request.method == 'POST':
        plate       = request.POST.get('plate_number', '').strip().upper()
        vtype       = request.POST.get('vehicle_type', 'Car')
        owner       = request.POST.get('owner_name', '').strip()

        if not plate or not owner:
            messages.error(request, "Plate number and owner name are required.")
        elif Vehicle.objects.filter(plate_number=plate).exists():
            messages.error(request, f"Vehicle with plate {plate} already exists.")
        else:
            Vehicle.objects.create(plate_number=plate, vehicle_type=vtype, owner_name=owner)
            messages.success(request, f"Vehicle {plate} added successfully.")

    return redirect('/dashboard/?tab=vehicles')


@_admin_required
def admin_vehicle_edit(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            vehicle.delete()
            messages.success(request, 'Vehicle deleted.')
        else:
            vehicle.plate_number = request.POST.get('plate_number', vehicle.plate_number).strip().upper()
            vehicle.vehicle_type = request.POST.get('vehicle_type', vehicle.vehicle_type)
            vehicle.owner_name   = request.POST.get('owner_name', vehicle.owner_name).strip()
            vehicle.save()
            messages.success(request, 'Vehicle updated.')
    return redirect('/dashboard/?tab=vehicles')


# ── Admin CRUD — Parking Lots ──────────────────────────────────────────────────

@_admin_required
def admin_parking_lots(request):
    return redirect('/dashboard/?tab=parking')


@_admin_required
def admin_parking_lot_create(request):
    if request.method == 'POST':
        location        = request.POST.get('location', '').strip()
        total_spaces    = int(request.POST.get('total_spaces', 0))
        available_spaces = int(request.POST.get('available_spaces', total_spaces))

        if not location or total_spaces <= 0:
            messages.error(request, "Location and total spaces are required.")
        else:
            lot = ParkingLot.objects.create(
                location=location,
                total_spaces=total_spaces,
                available_spaces=available_spaces,
            )
            space_types = ['Compact', 'Large', 'Electric Vehicle']
            for i in range(total_spaces):
                ParkingSpace.objects.create(
                    parking_lot=lot,
                    space_type=space_types[i % len(space_types)],
                    is_occupied=False,
                )
            messages.success(request, f"Parking lot '{location}' created with {total_spaces} spaces.")

    return redirect('/dashboard/?tab=parking')


@_admin_required
def admin_parking_lot_edit(request, lot_id):
    lot = get_object_or_404(ParkingLot, lot_id=lot_id)
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            lot.delete()
            messages.success(request, 'Parking lot deleted.')
        else:
            lot.location         = request.POST.get('location', lot.location).strip()
            lot.total_spaces     = int(request.POST.get('total_spaces', lot.total_spaces))
            lot.available_spaces = int(request.POST.get('available_spaces', lot.available_spaces))
            lot.save()
            messages.success(request, 'Parking lot updated.')
    return redirect('/dashboard/?tab=parking')


# ── Admin CRUD — Tickets ───────────────────────────────────────────────────────

@_admin_required
def admin_tickets(request):
    return redirect('/dashboard/?tab=tickets')


@_admin_required
def admin_ticket_edit(request, ticket_id):
    t = get_object_or_404(ParkingTicket, ticket_id=ticket_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'complete' and not t.exit_time:
            t.exit_time = timezone.now()
            t.fee = Decimal(request.POST.get('fee', '0') or '0')
            t.save()
            # Free up the parking space
            if t.parking_space:
                t.parking_space.is_occupied = False
                t.parking_space.save()
            # Update lot available count
            if t.parking_space and t.parking_space.parking_lot:
                lot = t.parking_space.parking_lot
                lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
                lot.save()
            messages.success(request, 'Ticket closed and space freed.')
        elif action == 'delete':
            t.delete()
            messages.success(request, 'Ticket deleted.')
        else:
            if request.POST.get('fee'):
                t.fee = Decimal(request.POST.get('fee'))
                t.save()
            messages.success(request, 'Ticket updated.')
    return redirect('/dashboard/?tab=tickets')


# ── Admin CRUD — Users ─────────────────────────────────────────────────────────

@_admin_required
def admin_users_management(request):
    return redirect('/dashboard/?tab=users')


@_admin_required
def admin_user_edit(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_staff':
            if target == request.user:
                messages.error(request, "You cannot change your own admin status.")
            else:
                target.is_staff = not target.is_staff
                target.save()
                role = "promoted to admin" if target.is_staff else "set to regular user"
                messages.success(request, f"{target.username} {role}.")
        elif action == 'toggle_active':
            if target == request.user:
                messages.error(request, "You cannot deactivate your own account.")
            else:
                target.is_active = not target.is_active
                target.save()
                status = "activated" if target.is_active else "deactivated"
                messages.success(request, f"{target.username} {status}.")
        elif action == 'delete':
            if target == request.user:
                messages.error(request, "You cannot delete your own account.")
            else:
                username = target.username
                target.delete()
                messages.success(request, f"User '{username}' deleted.")
    return redirect('/dashboard/?tab=users')


# ── Admin Reports ──────────────────────────────────────────────────────────────

@_admin_required
def admin_reports(request):
    return redirect('/dashboard/?tab=reports')
