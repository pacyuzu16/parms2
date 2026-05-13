from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.db.models import Sum, Count, Avg
from django.db.models.functions import ExtractHour
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import logging
import qrcode, datetime, random

from .models import (
    ContactMessage, ParkingLot, Vehicle, ParkingSpace,
    ParkingTicket, Payment, ParkingDetectionEvent, UserNotification, UserProfile
)
from .forms import ContactMessageForm

logger = logging.getLogger(__name__)

# -- helpers -------------------------------------------------------------------

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


def _compute_ml_insights():
    """Derives actionable insights from real ticket data using statistical analysis."""
    now = timezone.now()
    current_hour = now.hour
    last_30 = now - timedelta(days=30)

    hourly_qs = (
        ParkingTicket.objects
        .filter(entry_time__gte=last_30)
        .annotate(hour=ExtractHour('entry_time'))
        .values('hour')
        .annotate(count=Count('ticket_id'))
        .order_by('hour')
    )
    hour_data = [0] * 24
    for row in hourly_qs:
        hour_data[int(row['hour'])] = row['count']

    max_count = max(hour_data) if any(hour_data) else 1
    peak_hour = hour_data.index(max(hour_data))

    total_spaces = ParkingSpace.objects.count()
    occupied     = ParkingSpace.objects.filter(is_occupied=True).count()
    current_rate = round((occupied / total_spaces * 100) if total_spaces else 0)

    next_hour     = (current_hour + 1) % 24
    predicted_rate = round(min(100, (hour_data[next_hour] / max_count) * 90)) if max_count else 50

    expected = round((hour_data[current_hour] / max_count) * 90) if max_count else 50
    diff     = current_rate - expected
    if diff > 15:
        anomaly = {'type': 'high', 'msg': f'Occupancy {diff}% above expected for {current_hour:02d}:00'}
    elif diff < -15:
        anomaly = {'type': 'low',  'msg': f'Occupancy {abs(diff)}% below expected for {current_hour:02d}:00'}
    else:
        anomaly = None

    hour_pcts = [round(c / max_count * 100) for c in hour_data]
    hour_bars = [(f'{h:02d}', hour_pcts[h]) for h in range(24)]

    return {
        'hour_data':      hour_data,
        'hour_pcts':      hour_pcts,
        'hour_bars':      hour_bars,
        'peak_hour':      peak_hour,
        'peak_label':     f'{peak_hour:02d}:00 - {(peak_hour + 1) % 24:02d}:00',
        'current_hour':   current_hour,
        'current_rate':   current_rate,
        'predicted_rate': predicted_rate,
        'pred_direction': 'up' if predicted_rate > current_rate else 'down',
        'anomaly':        anomaly,
        'has_data':       any(hour_data),
        'next_hour_label': f'{next_hour:02d}:00',
    }


# -- Public views --------------------------------------------------------------

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


# -- Auth views ----------------------------------------------------------------

def signup(request):
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        email            = request.POST.get('email', '').strip()
        password         = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        plate_number     = request.POST.get('plate_number', '').strip().upper()
        vehicle_type     = request.POST.get('vehicle_type', 'Car')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('signup')
        if not plate_number:
            messages.error(request, "A vehicle license plate number is required.")
            return redirect('signup')
        if Vehicle.objects.filter(plate_number=plate_number).exists():
            messages.error(request, f"Plate {plate_number} is already registered to another account.")
            return redirect('signup')

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            Vehicle.objects.create(
                plate_number=plate_number,
                vehicle_type=vehicle_type,
                owner_name=username,
                user=user,
            )

        messages.success(request, "Account created! You can now log in.")
        return redirect('login')

    return render(request, 'signup.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if request.user.is_staff else 'map')

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
            return redirect('dashboard' if user.is_staff else 'map')

        messages.error(request, "Incorrect password.")
        return redirect('login')

    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    return redirect('home')


@login_required
def google_welcome(request):
    """
    Landing page after Google OAuth sign-in.
    - First-time users (no vehicle registered) → show plate-registration prompt.
    - Returning users who already have a vehicle → go straight to the dashboard.
    """
    has_vehicle = Vehicle.objects.filter(user=request.user).exists()
    if has_vehicle:
        # Already set up — send to the normal landing page
        return redirect('dashboard' if request.user.is_staff else 'map')
    # New Google user — they need to register a vehicle before parking
    return render(request, 'google_welcome.html')


# -- API -----------------------------------------------------------------------

def dashboard_data(request):
    data = {
        "users":          User.objects.count(),
        "parkings":       ParkingLot.objects.count(),
        "cars":           Vehicle.objects.count(),
        "tickets":        ParkingTicket.objects.count(),
        "active_tickets": ParkingTicket.objects.filter(exit_time__isnull=True).count(),
    }
    return JsonResponse(data)


# -- Admin dashboard (SPA) -----------------------------------------------------

@_admin_required
def dashboard(request):
    today = timezone.now().date()

    all_tickets       = ParkingTicket.objects.select_related('vehicle', 'parking_space__parking_lot').order_by('-entry_time')
    active_tickets    = all_tickets.filter(exit_time__isnull=True)
    completed_tickets = all_tickets.filter(exit_time__isnull=False)

    all_spaces       = ParkingSpace.objects.select_related('parking_lot')
    occupied_spaces  = all_spaces.filter(is_occupied=True)
    available_spaces = all_spaces.filter(is_occupied=False)

    all_vehicles = Vehicle.objects.all().order_by('-vehicle_id')
    all_lots     = ParkingLot.objects.annotate(ticket_count=Count('spaces__tickets')).order_by('-lot_id')
    all_users    = User.objects.all().order_by('-date_joined')
    all_messages = ContactMessage.objects.all().order_by('-submitted_at')

    vehicle_type_stats  = Vehicle.objects.values('vehicle_type').annotate(count=Count('vehicle_type')).order_by('-count')
    popular_lots = ParkingLot.objects.annotate(usage_count=Count('spaces__tickets')).order_by('-usage_count')[:8]

    context = {
        'active_tab': request.GET.get('tab', 'overview'),
        'total_users':             all_users.count(),
        'staff_users':             all_users.filter(is_staff=True).count(),
        'regular_users':           all_users.filter(is_staff=False).count(),
        'total_parking_lots':      all_lots.count(),
        'total_vehicles':          all_vehicles.count(),
        'total_tickets':           ParkingTicket.objects.count(),
        'active_tickets':          active_tickets.count(),
        'completed_tickets_count': completed_tickets.count(),
        'total_messages':          all_messages.count(),
        'total_spaces':            all_spaces.count(),
        'occupied_spaces':         occupied_spaces.count(),
        'available_spaces':        available_spaces.count(),
        'recent_tickets':  all_tickets[:8],
        'recent_messages': all_messages[:5],
        'recent_users':    all_users[:5],
        'all_tickets':  all_tickets[:200],
        'all_vehicles': all_vehicles[:200],
        'all_lots':     all_lots,
        'all_users':    all_users,
        'all_messages': all_messages,
        'active_ticket_list': active_tickets,
        'vehicle_types': ['Car', 'Motorcycle', 'Truck'],
        'popular_lots':          popular_lots,
        'vehicle_type_stats':    vehicle_type_stats,
        'ml': _compute_ml_insights(),
        'lots_occupancy': [
            {
                'id':        lot.lot_id,
                'location':  lot.location,
                'total':     lot.total_spaces,
                'available': lot.available_spaces,
                'occupied':  lot.total_spaces - lot.available_spaces,
                'rate':      round(((lot.total_spaces - lot.available_spaces) / lot.total_spaces * 100)
                             if lot.total_spaces else 0),
            }
            for lot in all_lots
        ],
        'recent_detection_events': ParkingDetectionEvent.objects.select_related('lot', 'space').order_by('-detected_at')[:20],
        'detection_event_count':   ParkingDetectionEvent.objects.count(),
        'entry_events_today':      ParkingDetectionEvent.objects.filter(
                                       event_type='entry',
                                       detected_at__date=today
                                   ).count(),
        'exit_events_today':       ParkingDetectionEvent.objects.filter(
                                       event_type='exit',
                                       detected_at__date=today
                                   ).count(),
    }
    return render(request, 'dashboard.html', context)


@_admin_required
def update_settings(request):
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


def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('/dashboard/?tab=settings')
    return redirect('profile')


# -- Regular user views --------------------------------------------------------

@login_required
def userin(request):
    owner_name    = request.user.get_full_name() or request.user.username
    user_vehicles = Vehicle.objects.filter(owner_name__iexact=owner_name)
    user_tickets  = ParkingTicket.objects.filter(vehicle__in=user_vehicles).order_by('-entry_time')
    active        = user_tickets.filter(exit_time__isnull=True)

    now      = timezone.now()
    last_30  = now - timedelta(days=30)
    hourly_qs = (
        ParkingTicket.objects
        .filter(entry_time__gte=last_30)
        .annotate(hour=ExtractHour('entry_time'))
        .values('hour')
        .annotate(count=Count('ticket_id'))
    )
    hour_map  = {int(r['hour']): r['count'] for r in hourly_qs}
    max_h     = max(hour_map.values()) if hour_map else 1
    next_hour = (now.hour + 1) % 24
    next_pct  = round((hour_map.get(next_hour, 0) / max_h) * 100) if max_h else 50

    lots_data = []
    for lot in ParkingLot.objects.prefetch_related('spaces').all():
        total = lot.spaces.count()
        occ   = lot.spaces.filter(is_occupied=True).count()
        avail = total - occ
        rate  = round(occ / total * 100) if total else 0
        pred = min(100, round(rate * 0.7 + next_pct * 0.3))

        if rate < 40:
            rec_label, rec_color = 'Best Choice', 'green'
        elif rate < 70:
            rec_label, rec_color = 'Available', 'amber'
        else:
            rec_label, rec_color = 'Filling Up', 'red'

        lots_data.append({
            'lot':       lot,
            'total':     total,
            'occupied':  occ,
            'available': avail,
            'rate':      rate,
            'pred':      pred,
            'rec_label': rec_label,
            'rec_color': rec_color,
        })

    lots_data.sort(key=lambda x: x['rate'])

    context = {
        'user_vehicles':        user_vehicles,
        'user_tickets':         user_tickets[:10],
        'active_tickets':       active,
        'total_vehicles':       user_vehicles.count(),
        'total_tickets':        user_tickets.count(),
        'active_tickets_count': active.count(),
        'lots_data':            lots_data,
        'recommended_lots':     lots_data[:2],
        'next_hour_label':      f'{next_hour:02d}:00',
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
    all_lots = ParkingLot.objects.order_by('location')

    # Parse lot_id from GET param safely
    active_lot = None
    raw = request.GET.get('lot_id', '').strip()
    if raw:
        try:
            active_lot = ParkingLot.objects.get(lot_id=int(raw))
        except (ValueError, ParkingLot.DoesNotExist):
            active_lot = None

    # Fall back to first lot with available spaces
    if active_lot is None:
        active_lot = all_lots.filter(available_spaces__gt=0).first() or all_lots.first()

    spaces = (
        ParkingSpace.objects.select_related('parking_lot').filter(parking_lot=active_lot)
        if active_lot else ParkingSpace.objects.none()
    )

    bookings = ParkingTicket.objects.select_related('parking_space', 'vehicle').order_by('-entry_time')[:10]
    context = {
        'all_lots':        all_lots,
        'active_lot':      active_lot,
        'active_lot_id':   active_lot.lot_id if active_lot else None,
        'parking_spaces':  spaces,
        'recent_bookings': bookings,
        'total_spaces':    spaces.count(),
        'occupied_spaces': spaces.filter(is_occupied=True).count(),
        'available_spaces': spaces.filter(is_occupied=False).count(),
    }
    return render(request, 'slots.html', context)


@login_required
def book_space(request):
    """POST: confirm a space booking → create ParkingTicket, mark space occupied."""
    if request.method != 'POST':
        return redirect('slots')

    space_id = request.POST.get('space_id', '').strip()
    if not space_id:
        messages.error(request, 'No space selected.')
        return redirect('slots')

    try:
        space_id_int = int(space_id)
    except ValueError:
        messages.error(request, 'That space is not available. Please choose another.')
        return redirect('slots')

    with transaction.atomic():
        try:
            space = (ParkingSpace.objects
                     .select_for_update()
                     .select_related('parking_lot')
                     .get(space_id=space_id_int, is_occupied=False))
        except ParkingSpace.DoesNotExist:
            messages.error(request, 'That space is not available. Please choose another.')
            return redirect('slots')

        # Prefer vehicle linked directly via FK, fall back to owner_name matching
        vehicle = (
            Vehicle.objects.filter(user=request.user).first()
            or Vehicle.objects.filter(owner_name__iexact=request.user.get_full_name() or request.user.username).first()
        )
        if not vehicle:
            vehicle = Vehicle.objects.create(
                plate_number='PENDING-' + str(request.user.pk),
                vehicle_type='Car',
                owner_name=request.user.get_full_name() or request.user.username,
                user=request.user,
            )

        # Create the ticket and mark the space occupied
        ticket = ParkingTicket.objects.create(
            vehicle=vehicle,
            parking_space=space,
            user=request.user,
        )
        space.is_occupied = True
        space.occupied_by_plate = vehicle.plate_number
        space.save(update_fields=['is_occupied', 'occupied_by_plate'])

        lot = space.parking_lot
        lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
        lot.save(update_fields=['available_spaces'])

        # Create booking notification
        UserNotification.objects.create(
            user=request.user,
            title=f'Parking booked — Space #{space.space_id}',
            message=f'Your spot at {lot.location} is confirmed. '
                    f'Space #{space.space_id} ({space.space_type}). '
                    f'Ticket #{ticket.ticket_id}.',
            notif_type='booking',
            lot=lot,
        )

    messages.success(request, f'Space #{space.space_id} booked! Ticket #{ticket.ticket_id}')
    return redirect('ticket')


@login_required
def ticket(request):
    """Show the user's active ticket and history — lookup by user FK first, fall back to owner_name."""
    qs = ParkingTicket.objects.select_related(
        'vehicle', 'parking_space__parking_lot'
    )
    # Primary: tickets linked directly to this user
    user_tickets = qs.filter(user=request.user).order_by('-entry_time')

    # Fallback: tickets whose vehicle owner_name matches (for legacy/seeded data)
    if not user_tickets.exists():
        owner = request.user.get_full_name() or request.user.username
        vehicles = Vehicle.objects.filter(owner_name__iexact=owner)
        user_tickets = qs.filter(vehicle__in=vehicles).order_by('-entry_time')

    active_tickets = user_tickets.filter(exit_time__isnull=True)
    context = {
        'user_tickets':   user_tickets[:20],
        'active_tickets': active_tickets,
    }
    return render(request, 'ticket.html', context)


@login_required
def exit_parking(request):
    """
    GET  → Show the exit page (upload/capture plate or type manually).
    POST → Process exit confirmation: close ticket, free space, record payment.
    """
    if request.method == 'POST':
        ticket_id      = request.POST.get('ticket_id', '').strip()
        payment_method = request.POST.get('payment_method', 'Cash')

        try:
            t = ParkingTicket.objects.select_related(
                'vehicle', 'parking_space__parking_lot'
            ).get(ticket_id=ticket_id, exit_time__isnull=True)
        except ParkingTicket.DoesNotExist:
            messages.error(request, "Session not found or already closed.")
            return redirect('exit_parking')

        with transaction.atomic():
            t.exit_time = timezone.now()
            rate = t.parking_space.parking_lot.hourly_rate if t.parking_space else 0
            t.fee = Decimal(str(round(t.duration_hours() * float(rate), 2)))
            t.save()

            if t.parking_space:
                t.parking_space.is_occupied = False
                t.parking_space.occupied_by_plate = ''
                t.parking_space.save(update_fields=['is_occupied', 'occupied_by_plate'])

                lot = t.parking_space.parking_lot
                lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
                lot.save(update_fields=['available_spaces'])
            else:
                lot = None

            # Record payment
            Payment.objects.create(
                amount=t.fee or Decimal('0'),
                payment_method=payment_method,
                ticket=t,
            )

            # Notify user
            if t.user:
                fee_str = f'${t.fee}' if t.fee else '$0.00'
                UserNotification.objects.create(
                    user=t.user,
                    title=f'Session ended — {t.vehicle.plate_number}',
                    message=(f'Your parking session at '
                             f'{lot.location if lot else "the lot"} is complete. '
                             f'Duration: {t.duration_hours():.1f}h · Fee: {fee_str}. '
                             f'Payment: {payment_method}. Thank you!'),
                    notif_type='session_ended',
                    lot=lot,
                )

            if lot and lot.available_spaces == 1:
                _notify_space_available(lot)

            # Email receipt
            try:
                from .email_utils import send_session_email
                send_session_email(t, payment_method)
            except Exception as e:
                logger.error(f'Failed to send session email: {str(e)}', exc_info=True)

        return render(request, 'exit_success.html', {
            'ticket': t,
            'lot': lot if t.parking_space else None,
            'payment_method': payment_method,
        })

    # GET — check if user already has an active session
    active = (
        ParkingTicket.objects
        .filter(user=request.user, exit_time__isnull=True)
        .select_related('vehicle', 'parking_space__parking_lot')
        .order_by('-entry_time')
        .first()
    )
    return render(request, 'exit.html', {'active_ticket': active})


@login_required
def api_lookup_plate(request):
    """
    POST /api/lookup-plate/
    Accepts either:
      - multipart: image file  → runs LPR, reads plate from image
      - JSON/POST:  plate_number → direct text lookup
    Returns active session details + calculated fee.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    plate = request.POST.get('plate_number', '').strip().upper()

    # If an image was uploaded, run LPR to extract the plate
    if not plate and request.FILES.get('image'):
        img_file = request.FILES['image']
        if img_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Image too large (max 10 MB).'})
        try:
            from .license_plate import detect_plate
            result = detect_plate(img_file.read())
            if result.get('success') and result.get('plates'):
                plate = result['plates'][0].get('text', '') or ''
                plate = plate.strip().upper()
            if not plate:
                return JsonResponse({
                    'success': False,
                    'error': 'Could not read plate from image. Try typing it manually.',
                    'lpr_result': result,
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'LPR error: {e}'})

    if not plate:
        return JsonResponse({'success': False, 'error': 'Provide a plate number or image.'})

    # Find vehicle with this plate
    try:
        vehicle = Vehicle.objects.get(plate_number__iexact=plate)
    except Vehicle.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'No vehicle registered with plate {plate}.'})

    # Find the active parking ticket for this vehicle
    active_ticket = (
        ParkingTicket.objects
        .filter(vehicle=vehicle, exit_time__isnull=True)
        .select_related('vehicle', 'parking_space__parking_lot', 'user')
        .order_by('-entry_time')
        .first()
    )

    if not active_ticket:
        return JsonResponse({
            'success': False,
            'error': f'No active parking session found for plate {plate}.',
        })

    # Check this ticket belongs to the requesting user (security)
    if active_ticket.user and active_ticket.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'This parking session belongs to a different account.',
        })

    lot = active_ticket.parking_space.parking_lot if active_ticket.parking_space else None
    fee = active_ticket.calculated_fee()
    duration = active_ticket.duration_hours()

    # Format entry time in local timezone
    from django.utils import timezone as tz
    entry_local = tz.localtime(active_ticket.entry_time)

    return JsonResponse({
        'success':      True,
        'ticket_id':    active_ticket.ticket_id,
        'plate':        vehicle.plate_number,
        'vehicle_type': vehicle.vehicle_type,
        'location':     lot.location if lot else '—',
        'space_id':     active_ticket.parking_space.space_id if active_ticket.parking_space else None,
        'entry_time':   entry_local.strftime('%d %b %Y %H:%M'),
        'duration_h':   round(duration, 2),
        'fee':          str(fee),
        'hourly_rate':  str(lot.hourly_rate) if lot else '0',
    })


@login_required
def destination(request):
    """Navigation page — shows route from user location to their active parking lot."""
    # Find the active ticket — prefer user FK, fall back to owner_name
    active_ticket = (
        ParkingTicket.objects
        .filter(user=request.user, exit_time__isnull=True)
        .select_related('vehicle', 'parking_space__parking_lot')
        .order_by('-entry_time')
        .first()
    )
    if not active_ticket:
        owner_name    = request.user.get_full_name() or request.user.username
        user_vehicles = Vehicle.objects.filter(owner_name__iexact=owner_name)
        active_ticket = (
            ParkingTicket.objects
            .filter(vehicle__in=user_vehicles, exit_time__isnull=True)
            .select_related('vehicle', 'parking_space__parking_lot')
            .order_by('-entry_time')
            .first()
        )

    # Allow manually passing a lot_id via ?lot_id=X
    lot_id = request.GET.get('lot_id')
    target_lot = None
    if lot_id:
        try:
            target_lot = ParkingLot.objects.get(lot_id=lot_id)
        except ParkingLot.DoesNotExist:
            pass
    elif active_ticket and active_ticket.parking_space:
        target_lot = active_ticket.parking_space.parking_lot

    # Recent activity for the sidebar — use user FK (fast), no need for vehicle lookup
    recent_tickets = (
        ParkingTicket.objects
        .filter(user=request.user)
        .select_related('vehicle', 'parking_space__parking_lot')
        .order_by('-entry_time')[:5]
    )

    # Use lot GPS if set; fall back to Kigali city centre so the map always loads
    KIGALI_LAT, KIGALI_LNG = -1.9441, 30.0619
    target_lat  = (target_lot.latitude  if target_lot and target_lot.latitude  else KIGALI_LAT)
    target_lng  = (target_lot.longitude if target_lot and target_lot.longitude else KIGALI_LNG)
    show_map    = target_lot is not None  # show map whenever we have a destination lot

    context = {
        'active_ticket': active_ticket,
        'target_lot':    target_lot,
        'recent_tickets': recent_tickets,
        'target_lat':    target_lat  if show_map else None,
        'target_lng':    target_lng  if show_map else None,
        'target_name':   target_lot.location if target_lot else 'Your Parking Lot',
        'has_gps':       bool(target_lot and target_lot.latitude and target_lot.longitude),
    }
    return render(request, 'destination.html', context)


@login_required
def user_list(request):
    if not request.user.is_staff:
        return redirect('userin')
    return redirect('/dashboard/?tab=users')


# -- Driver Profile ------------------------------------------------------------

@login_required
def profile(request):
    owner_name    = request.user.get_full_name() or request.user.username
    user_vehicles = Vehicle.objects.filter(owner_name__iexact=owner_name).order_by("vehicle_id")
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "update_profile":
            fname        = request.POST.get("first_name", "").strip()
            lname        = request.POST.get("last_name",  "").strip()
            new_email    = request.POST.get("email",      "").strip()
            new_password = request.POST.get("password",   "").strip()
            request.user.first_name = fname
            request.user.last_name  = lname
            if new_email and new_email != request.user.email:
                if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                    messages.error(request, "That email is already in use.")
                    return redirect("profile")
                request.user.email = new_email
            if new_password:
                if len(new_password) < 8:
                    messages.error(request, "Password must be at least 8 characters.")
                    return redirect("profile")
                request.user.set_password(new_password)
                messages.success(request, "Password updated. Please sign in again.")
                request.user.save()
                return redirect("login")
            request.user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")

        elif action == "update_photo":
            photo = request.FILES.get("photo")
            if photo:
                # Validate: image only, max 5 MB
                allowed = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
                if photo.content_type not in allowed:
                    messages.error(request, "Please upload a JPEG, PNG, WebP or GIF image.")
                    return redirect("profile")
                if photo.size > 5 * 1024 * 1024:
                    messages.error(request, "Photo must be under 5 MB.")
                    return redirect("profile")
                # Delete old photo file to save disk space
                if user_profile.photo:
                    user_profile.photo.delete(save=False)
                user_profile.photo = photo
                user_profile.save()
                messages.success(request, "Profile photo updated!")
            else:
                messages.error(request, "No photo was selected.")
            return redirect("profile")

        elif action == "remove_photo":
            if user_profile.photo:
                user_profile.photo.delete(save=False)
                user_profile.photo = None
                user_profile.save()
                messages.success(request, "Profile photo removed.")
            return redirect("profile")

        elif action == "add_vehicle":
            plate = request.POST.get("plate_number", "").strip().upper()
            vtype = request.POST.get("vehicle_type", "Car")
            if not plate:
                messages.error(request, "Plate number is required.")
            elif Vehicle.objects.filter(plate_number=plate).exists():
                messages.error(request, "Vehicle " + plate + " is already registered.")
            else:
                Vehicle.objects.create(
                    plate_number=plate, vehicle_type=vtype,
                    owner_name=request.user.get_full_name() or request.user.username,
                )
                messages.success(request, "Vehicle " + plate + " added.")
            return redirect("profile")

        elif action == "remove_vehicle":
            vid = request.POST.get("vehicle_id")
            try:
                v = Vehicle.objects.get(vehicle_id=vid, owner_name__iexact=owner_name)
                plate = v.plate_number
                v.delete()
                messages.success(request, "Vehicle " + plate + " removed.")
            except Vehicle.DoesNotExist:
                messages.error(request, "Vehicle not found.")
            return redirect("profile")

    all_tickets  = ParkingTicket.objects.filter(user=request.user).order_by("-entry_time")
    active_now   = all_tickets.filter(exit_time__isnull=True)

    context = {
        "user_profile":    user_profile,
        "user_vehicles":   user_vehicles,
        "total_tickets":   all_tickets.count(),
        "active_sessions": active_now.count(),
        "vehicle_types":   ["Car", "Motorcycle", "Truck"],
    }
    return render(request, "profile.html", context)


# -- Driver Notifications ------------------------------------------------------

@login_required
def notifications(request):
    tickets = (ParkingTicket.objects
               .filter(user=request.user)
               .select_related("vehicle", "parking_space__parking_lot")
               .order_by("-entry_time")[:30])

    notifs = []
    for t in tickets:
        loc = (t.parking_space.parking_lot.location
               if t.parking_space and t.parking_space.parking_lot else "Unknown")
        notifs.append({"icon": "sign-in-alt", "color": "green",
                       "title": "Session started - " + t.vehicle.plate_number,
                       "detail": loc, "time": t.entry_time, "type": "entry"})
        if t.exit_time:
            fee_s = " - $" + str(t.fee) if t.fee else ""
            notifs.append({"icon": "check-circle", "color": "blue",
                           "title": "Session completed - " + t.vehicle.plate_number,
                           "detail": loc + fee_s, "time": t.exit_time, "type": "exit"})

    notifs.sort(key=lambda x: x["time"], reverse=True)
    context = {"notifs": notifs[:25], "total_count": len(notifs)}
    return render(request, "notifications.html", context)


# -- QR / Ticket generation ----------------------------------------------------

def generate_qr_code(request):
    ticket_url = request.build_absolute_uri(reverse('ticket'))
    img = qrcode.make(ticket_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf, content_type="image/png")


@login_required
def generate_ticket(request):
    # ── Fetch the most recent ticket (active first, then latest completed) ──
    t = (
        ParkingTicket.objects
        .filter(user=request.user)
        .select_related('vehicle', 'parking_space__parking_lot')
        .order_by('exit_time', '-entry_time')
        .first()
    )

    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader

    # ── Colours ─────────────────────────────────────────────────────────────
    GREEN  = (0.17, 0.37, 0.28)
    MINT   = (0.77, 0.91, 0.84)
    WHITE  = (1, 1, 1)
    INK    = (0.086, 0.106, 0.098)
    MUTED  = (0.31, 0.35, 0.33)
    LIGHT  = (0.96, 0.99, 0.97)
    BORDER = (0.87, 0.89, 0.88)

    W, H = A4  # 595 × 842 pt
    PAD = 40   # horizontal padding

    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    def rgb(col):  c.setFillColorRGB(*col)
    def srgb(col): c.setStrokeColorRGB(*col)

    def truncate(text, font, size, max_w):
        s = str(text)
        while c.stringWidth(s, font, size) > max_w and len(s) > 2:
            s = s[:-1]
        return s if s == str(text) else s + '…'

    # ══════════════════════════════════════════════════════════════════════
    # 1. HEADER  y = 752–842  (90 pt)
    # ══════════════════════════════════════════════════════════════════════
    rgb(GREEN)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 24)
    rgb(WHITE)
    c.drawString(PAD, H - 36, "PARMS")

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*MINT)
    c.drawString(PAD, H - 52, "Smart Parking Management System")

    c.setFont("Helvetica-Bold", 13)
    rgb(WHITE)
    c.drawRightString(W - PAD, H - 36, "PARKING TICKET")

    # Status badge
    is_active   = t and not t.exit_time
    badge_txt   = "ACTIVE" if is_active else ("COMPLETED" if t else "NO SESSION")
    badge_color = (0.10, 0.65, 0.32) if is_active else ((0.20, 0.46, 0.80) if t else (0.65, 0.18, 0.18))
    c.setFillColorRGB(*badge_color)
    bw = 80
    c.roundRect(W - PAD - bw, H - 70, bw, 18, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7)
    rgb(WHITE)
    c.drawCentredString(W - PAD - bw / 2, H - 64, badge_txt)

    # ══════════════════════════════════════════════════════════════════════
    # 2. TICKET-ID BAR  y = 722–752  (30 pt)
    # ══════════════════════════════════════════════════════════════════════
    rgb(MINT)
    c.rect(0, H - 122, W, 30, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11)
    rgb(GREEN)
    tid = "Ticket  #" + str(t.ticket_id) if t else "No Active Ticket"
    c.drawCentredString(W / 2, H - 112, tid)

    # ══════════════════════════════════════════════════════════════════════
    # 3. MAIN CARD  y = 390–710  (320 pt tall)
    # ══════════════════════════════════════════════════════════════════════
    card_x, card_y, card_w, card_h = PAD, 388, W - 2 * PAD, 320
    srgb(BORDER); rgb(WHITE)
    c.setLineWidth(0.8)
    c.roundRect(card_x, card_y, card_w, card_h, 8, fill=1, stroke=1)

    # ── QR block (left side of card) ──
    qr_size = 150
    qr_x    = card_x + 18
    qr_y    = card_y + (card_h - qr_size) // 2 + 10   # vertically centred +10 for label

    ticket_url = request.build_absolute_uri(reverse('ticket'))
    qr_img = qrcode.make(ticket_url)
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size, preserveAspectRatio=True)

    # Label below QR
    c.setFont("Helvetica", 7.5)
    rgb(MUTED)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 12, "Scan at the entrance")

    # Vertical divider
    div_x = card_x + qr_size + 40
    srgb(BORDER)
    c.setLineWidth(0.5)
    c.line(div_x, card_y + 16, div_x, card_y + card_h - 16)

    # ── Details grid (right side of card) ──
    if t:
        lot  = t.parking_space.parking_lot if t.parking_space else None
        rows = [
            ("CUSTOMER",    request.user.get_full_name() or request.user.username),
            ("EMAIL",       request.user.email or "—"),
            ("VEHICLE",     t.vehicle.plate_number),
            ("TYPE",        t.vehicle.vehicle_type),
            ("LOCATION",    lot.location if lot else "—"),
            ("SPACE",       "#" + str(t.parking_space.space_id) + "  " + t.parking_space.space_type if t.parking_space else "—"),
            ("ENTRY",       t.entry_time.strftime("%d %b %Y  %H:%M")),
            ("EXIT",        t.exit_time.strftime("%d %b %Y  %H:%M") if t.exit_time else "Still active"),
            ("FEE",         "$" + str(t.fee) if t.fee else "Calculated on exit"),
        ]
    else:
        rows = [("STATUS", "No parking session found")]

    grid_x  = div_x + 14
    grid_w  = card_x + card_w - grid_x - 14
    row_h   = card_h / (len(rows) + 0.5)
    row_top = card_y + card_h - 10

    for i, (label, value) in enumerate(rows):
        ry = row_top - (i + 1) * row_h
        # Alternate shade
        if i % 2 == 0:
            rgb(LIGHT)
            c.rect(grid_x - 4, ry, grid_w + 4, row_h - 2, fill=1, stroke=0)
        # Label
        c.setFont("Helvetica-Bold", 7)
        rgb(MUTED)
        c.drawString(grid_x, ry + row_h - 10, label)
        # Value
        bold = label in ("VEHICLE", "FEE", "LOCATION")
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, 9.5)
        rgb(INK)
        c.drawString(grid_x, ry + 4, truncate(value, font, 9.5, grid_w))

    # ══════════════════════════════════════════════════════════════════════
    # 4. TEAR LINE  y = 378
    # ══════════════════════════════════════════════════════════════════════
    dash_y = 378
    c.setFont("Helvetica", 9)
    rgb(MUTED)
    c.drawString(PAD, dash_y + 2, "✂")
    srgb(BORDER)
    c.setLineWidth(0.7)
    c.setDash(5, 5)
    c.line(PAD + 14, dash_y + 5, W - PAD, dash_y + 5)
    c.setDash()

    # ══════════════════════════════════════════════════════════════════════
    # 5. INSTRUCTIONS  y = 100–368
    # ══════════════════════════════════════════════════════════════════════
    c.setFont("Helvetica-Bold", 9)
    rgb(INK)
    c.drawString(PAD, 355, "Instructions")

    lines = [
        "1.  Show this QR code at the parking entrance barrier.",
        "2.  Keep this ticket until your session has ended.",
        "3.  Fees are calculated based on actual time parked.",
        "4.  Lost ticket? Log in at parms.rw to view your active session.",
        "5.  For support, contact your parking attendant on site.",
    ]
    c.setFont("Helvetica", 8.5)
    rgb(MUTED)
    for j, line in enumerate(lines):
        c.drawString(PAD, 337 - j * 18, line)

    # Fine print
    c.setFont("Helvetica", 7)
    rgb(BORDER)
    c.drawString(PAD, 106, "This ticket is valid only for the session and space shown above. Do not share your QR code.")

    # ══════════════════════════════════════════════════════════════════════
    # 6. FOOTER  y = 0–50
    # ══════════════════════════════════════════════════════════════════════
    rgb(GREEN)
    c.rect(0, 0, W, 50, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 9)
    rgb(WHITE)
    c.drawString(PAD, 32, "PARMS")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MINT)
    c.drawString(PAD, 18, "Smart Parking Management System")

    generated_at = datetime.datetime.now().strftime("%d %b %Y  %H:%M")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MINT)
    c.drawRightString(W - PAD, 32, "Generated: " + generated_at)
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(0.60, 0.80, 0.70)
    c.drawRightString(W - PAD, 18, "parms.rw")

    # ── Finalise ─────────────────────────────────────────────────────────
    c.save()
    buf.seek(0)
    fname = "parms_ticket_" + str(t.ticket_id) + ".pdf" if t else "parms_ticket.pdf"
    return FileResponse(buf, as_attachment=True, filename=fname)


# -- Admin CRUD - Contacts -----------------------------------------------------

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


# -- Admin CRUD - Vehicles -----------------------------------------------------

@_admin_required
def admin_vehicles(request):
    return redirect('/dashboard/?tab=vehicles')


@_admin_required
def admin_vehicle_create(request):
    if request.method == 'POST':
        plate = request.POST.get('plate_number', '').strip().upper()
        vtype = request.POST.get('vehicle_type', 'Car')
        owner = request.POST.get('owner_name', '').strip()

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


# -- Admin CRUD - Parking Lots -------------------------------------------------

@_admin_required
def admin_parking_lots(request):
    return redirect('/dashboard/?tab=parking')


@_admin_required
def admin_parking_lot_create(request):
    if request.method == 'POST':
        location = request.POST.get('location', '').strip()
        try:
            total_spaces     = int(request.POST.get('total_spaces', 0))
            available_spaces = int(request.POST.get('available_spaces', total_spaces))
        except ValueError:
            messages.error(request, "Total spaces must be a valid number.")
            return redirect('/dashboard/?tab=parking')

        if not location or total_spaces <= 0:
            messages.error(request, "Location and total spaces are required.")
        else:
            lat_str  = request.POST.get('latitude', '').strip()
            lng_str  = request.POST.get('longitude', '').strip()
            lot = ParkingLot.objects.create(
                location=location,
                total_spaces=total_spaces,
                available_spaces=available_spaces,
                latitude=float(lat_str)  if lat_str  else None,
                longitude=float(lng_str) if lng_str  else None,
                hourly_rate=float(request.POST.get('hourly_rate', 5.00) or 5.00),
                description=request.POST.get('description', '').strip(),
                features=request.POST.get('features', '').strip(),
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
            try:
                new_total = int(request.POST.get('total_spaces', lot.total_spaces))
            except ValueError:
                messages.error(request, "Total spaces must be a valid number.")
                return redirect('/dashboard/?tab=parking')
            lot.location    = request.POST.get('location', lot.location).strip()
            lot.total_spaces = new_total
            lat_str = request.POST.get('latitude', '').strip()
            lng_str = request.POST.get('longitude', '').strip()
            lot.latitude    = float(lat_str) if lat_str else lot.latitude
            lot.longitude   = float(lng_str) if lng_str else lot.longitude
            lot.hourly_rate = float(request.POST.get('hourly_rate', lot.hourly_rate) or lot.hourly_rate)
            lot.description = request.POST.get('description', lot.description).strip()
            lot.features    = request.POST.get('features', lot.features).strip()

            # ── Sync actual ParkingSpace records to match new total ──────────
            current_count = lot.spaces.count()
            space_types   = ['Compact', 'Compact', 'Large', 'Compact', 'Electric Vehicle',
                             'Large', 'Compact', 'Compact', 'Large', 'Compact']

            if new_total > current_count:
                # Add missing spaces
                for i in range(new_total - current_count):
                    ParkingSpace.objects.create(
                        parking_lot=lot,
                        space_type=space_types[(current_count + i) % len(space_types)],
                        is_occupied=False,
                    )
            elif new_total < current_count:
                # Remove excess spaces — free ones first, occupied last
                to_remove = current_count - new_total
                free = list(lot.spaces.filter(is_occupied=False)[:to_remove])
                for s in free:
                    s.delete()
                    to_remove -= 1
                if to_remove > 0:
                    # If still need to remove, take occupied ones too
                    for s in lot.spaces.all()[:to_remove]:
                        s.delete()

            # ── Recalculate available_spaces from actual records ─────────────
            lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
            lot.save()
            messages.success(request, f"Parking lot updated — {lot.available_spaces} of {new_total} spaces available.")
    return redirect('/dashboard/?tab=parking')


# -- Admin CRUD - Tickets ------------------------------------------------------

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
            if t.parking_space:
                t.parking_space.is_occupied = False
                t.parking_space.occupied_by_plate = ''
                t.parking_space.save(update_fields=['is_occupied', 'occupied_by_plate'])
            lot = None
            if t.parking_space and t.parking_space.parking_lot:
                lot = t.parking_space.parking_lot
                lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
                lot.save()
            # Notify the driver their session ended
            if t.user:
                fee_str = f' Fee: ${t.fee}.' if t.fee else ''
                UserNotification.objects.create(
                    user=t.user,
                    title=f'Session ended — {t.vehicle.plate_number}',
                    message=f'Your parking session at {lot.location if lot else "the lot"} has been completed.{fee_str}',
                    notif_type='session_ended',
                    lot=lot,
                )
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


# -- Admin CRUD - Users --------------------------------------------------------

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


# -- Admin Reports -------------------------------------------------------------

@_admin_required
def admin_reports(request):
    return redirect('/dashboard/?tab=reports')


@_admin_required
def admin_export_csv(request, report_type):
    """GET /manage/export/<type>/ — download a CSV of tickets, vehicles, users, or payments."""
    import csv
    from django.http import HttpResponse

    now_str = timezone.now().strftime('%Y-%m-%d_%H%M')
    response = HttpResponse(content_type='text/csv')

    if report_type == 'tickets':
        response['Content-Disposition'] = f'attachment; filename="parms_tickets_{now_str}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ticket ID', 'Plate', 'Owner', 'Location', 'Space',
                         'Entry Time', 'Exit Time', 'Duration (hrs)', 'Fee ($)', 'Status'])
        qs = (ParkingTicket.objects
              .select_related('vehicle', 'parking_space__parking_lot', 'user')
              .order_by('-entry_time')[:5000])
        for t in qs:
            lot  = t.parking_space.parking_lot.location if t.parking_space else '—'
            space = f'#{t.parking_space.space_id}' if t.parking_space else '—'
            owner = t.user.get_full_name() or t.user.username if t.user else t.vehicle.owner_name
            entry = timezone.localtime(t.entry_time).strftime('%Y-%m-%d %H:%M')
            exit_ = timezone.localtime(t.exit_time).strftime('%Y-%m-%d %H:%M') if t.exit_time else 'Active'
            status = 'Completed' if t.exit_time else 'Active'
            writer.writerow([t.ticket_id, t.vehicle.plate_number, owner, lot, space,
                             entry, exit_, round(t.duration_hours(), 2), t.fee or 0, status])

    elif report_type == 'vehicles':
        response['Content-Disposition'] = f'attachment; filename="parms_vehicles_{now_str}.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Plate Number', 'Type', 'Owner', 'Linked User', 'Total Sessions'])
        for v in Vehicle.objects.select_related('user').annotate(sessions=Count('tickets')).order_by('-vehicle_id'):
            linked = v.user.email if v.user else '—'
            writer.writerow([v.vehicle_id, v.plate_number, v.vehicle_type,
                             v.owner_name, linked, v.sessions])

    elif report_type == 'users':
        response['Content-Disposition'] = f'attachment; filename="parms_users_{now_str}.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Role',
                         'Date Joined', 'Last Login', 'Total Tickets'])
        for u in (User.objects
                  .annotate(ticket_count=Count('tickets'))
                  .order_by('-date_joined')):
            role = 'Admin' if u.is_staff else 'User'
            joined = u.date_joined.strftime('%Y-%m-%d')
            last   = u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else '—'
            writer.writerow([u.id, u.username, u.email,
                             u.get_full_name(), role, joined, last, u.ticket_count])

    elif report_type == 'payments':
        response['Content-Disposition'] = f'attachment; filename="parms_payments_{now_str}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Payment ID', 'Ticket ID', 'Plate', 'Amount ($)',
                         'Method', 'Date', 'Location'])
        for p in (Payment.objects
                  .select_related('ticket__vehicle', 'ticket__parking_space__parking_lot')
                  .order_by('-date')[:5000]):
            lot  = (p.ticket.parking_space.parking_lot.location
                    if p.ticket.parking_space else '—')
            date = timezone.localtime(p.date).strftime('%Y-%m-%d %H:%M')
            writer.writerow([p.payment_id, p.ticket.ticket_id,
                             p.ticket.vehicle.plate_number, p.amount,
                             p.payment_method, date, lot])

    elif report_type == 'occupancy':
        response['Content-Disposition'] = f'attachment; filename="parms_occupancy_{now_str}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Lot ID', 'Location', 'Total Spaces', 'Occupied',
                         'Available', 'Occupancy %', 'Status'])
        for lot in ParkingLot.objects.prefetch_related('spaces').order_by('lot_id'):
            total = lot.spaces.count()
            occ   = lot.spaces.filter(is_occupied=True).count()
            avail = total - occ
            rate  = round(occ / total * 100) if total else 0
            writer.writerow([lot.lot_id, lot.location, total, occ,
                             avail, f'{rate}%', lot.status()])
    else:
        return redirect('/dashboard/?tab=reports')

    return response


# -- Map View ------------------------------------------------------------------

@login_required
def map_view(request):
    """Interactive Leaflet map showing all parking lots with live occupancy."""
    lots = ParkingLot.objects.filter(is_active=True).prefetch_related('spaces')
    lots_data = []
    for lot in lots:
        total = lot.spaces.count()
        occ   = lot.spaces.filter(is_occupied=True).count()
        avail = total - occ
        rate  = round(occ / total * 100) if total else 0
        lots_data.append({
            'id':        lot.lot_id,
            'location':  lot.location,
            'lat':       lot.latitude or -1.9441,
            'lng':       lot.longitude or 30.0619,
            'total':     total,
            'occupied':  occ,
            'available': avail,
            'rate':      rate,
            'status':    lot.status(),
            'hourly_rate': float(lot.hourly_rate),
            'features':  lot.features,
        })
    context = {
        'lots_data':      lots_data,
        'total_lots':     len(lots_data),
        'total_available': sum(d['available'] for d in lots_data),
    }
    return render(request, 'map.html', context)


# -- Smart Recommendations API -------------------------------------------------

@login_required
def api_recommendations(request):
    """GET /api/recommendations/ - lots sorted by score (availability+price+distance)."""
    import math

    user_lat  = float(request.GET.get('lat',  -1.9441))
    user_lng  = float(request.GET.get('lng',   30.0619))
    max_price = float(request.GET.get('max_price', 9999))
    min_slots = int(request.GET.get('min_slots', 1))

    def haversine(lat1, lng1, lat2, lng2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    lots = ParkingLot.objects.filter(is_active=True).prefetch_related('spaces')
    results = []
    for lot in lots:
        total = lot.spaces.count()
        occ   = lot.spaces.filter(is_occupied=True).count()
        avail = total - occ
        rate  = round(occ / total * 100) if total else 0

        if avail < min_slots:
            continue
        if float(lot.hourly_rate) > max_price:
            continue

        dist = haversine(user_lat, user_lng,
                         lot.latitude  or -1.9441,
                         lot.longitude or 30.0619)

        avail_score = (avail / total * 100) if total else 0
        price_score = max(0, 100 - float(lot.hourly_rate) * 5)
        dist_score  = max(0, 100 - dist * 20)
        score       = avail_score * 0.5 + price_score * 0.3 + dist_score * 0.2

        if   score >= 70: rec = 'Best Choice'
        elif score >= 45: rec = 'Good Option'
        else:             rec = 'Available'

        results.append({
            'id':          lot.lot_id,
            'location':    lot.location,
            'lat':         lot.latitude  or -1.9441,
            'lng':         lot.longitude or 30.0619,
            'total':       total,
            'available':   avail,
            'occupied':    occ,
            'rate':        rate,
            'hourly_rate': float(lot.hourly_rate),
            'features':    lot.features,
            'distance_km': round(dist, 2),
            'score':       round(score, 1),
            'recommendation': rec,
            'status':      lot.status(),
        })

    results.sort(key=lambda x: -x['score'])
    return JsonResponse({'success': True, 'data': results, 'count': len(results)})


# -- Availability Prediction API -----------------------------------------------

@login_required
def api_predictions(request, lot_id=None):
    """GET /api/predictions/<lot_id>/ - 24-hour occupancy prediction."""
    now      = timezone.now()
    last_30  = now - timedelta(days=30)

    if lot_id:
        try:
            lot = ParkingLot.objects.get(lot_id=lot_id)
        except ParkingLot.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Lot not found'}, status=404)
        tickets = ParkingTicket.objects.filter(
            parking_space__parking_lot=lot,
            entry_time__gte=last_30
        )
    else:
        lot     = None
        tickets = ParkingTicket.objects.filter(entry_time__gte=last_30)

    hour_counts = [0] * 24
    for t in tickets:
        hour_counts[t.entry_time.hour] += 1

    max_count = max(hour_counts) if any(hour_counts) else 1
    total_spaces = (lot.total_spaces if lot else ParkingSpace.objects.count()) or 1

    predictions = []
    for h in range(24):
        predicted_pct = round(min(100, hour_counts[h] / max_count * 85)) if max_count > 0 else 0
        if h == now.hour:
            actual = lot.occupancy_rate() if lot else round(
                ParkingSpace.objects.filter(is_occupied=True).count() / total_spaces * 100
            )
            predicted_pct = round(predicted_pct * 0.4 + actual * 0.6)
        predictions.append({
            'hour':  h,
            'label': f'{h:02d}:00',
            'predicted_occupancy': predicted_pct,
            'ticket_count': hour_counts[h],
            'is_peak': hour_counts[h] == max(hour_counts) and hour_counts[h] > 0,
            'is_current': h == now.hour,
        })

    peak_hour = hour_counts.index(max(hour_counts)) if any(hour_counts) else 0
    return JsonResponse({
        'success': True,
        'lot_id': lot_id,
        'lot_location': lot.location if lot else 'All Lots',
        'peak_hour': peak_hour,
        'peak_label': f'{peak_hour:02d}:00',
        'predictions': predictions,
        'has_data': any(hour_counts),
    })


# -- Detection Event APIs ------------------------------------------------------

def _find_free_space(lot):
    return lot.spaces.filter(is_occupied=False).first()


def api_detect_entry(request):
    """POST /api/detect-entry/ - Called by entrance camera/sensor."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    lot_id     = data.get('lot_id')
    plate      = data.get('plate_number', '')
    confidence = float(data.get('confidence', 1.0))
    source     = data.get('source', 'api')

    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
    except ParkingLot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Lot not found'}, status=404)

    space = _find_free_space(lot)
    if not space:
        return JsonResponse({'success': False, 'error': 'Lot is full'}, status=409)

    space.is_occupied = True
    space.save()
    lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
    lot.save()

    event = ParkingDetectionEvent.objects.create(
        lot=lot, space=space, event_type='entry',
        plate_number=plate, confidence=confidence, source=source, processed=True,
    )

    rate = lot.occupancy_rate()
    if rate >= 80:
        _notify_nearly_full(lot, rate)

    return JsonResponse({
        'success':   True,
        'event_id':  event.id,
        'space_id':  space.space_id,
        'lot':       lot.location,
        'occupancy': rate,
        'message':   f'Entry recorded. Space {space.space_id} marked occupied.',
    })


def api_detect_exit(request):
    """POST /api/detect-exit/ - Called by exit camera/sensor."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    lot_id     = data.get('lot_id')
    plate      = data.get('plate_number', '')
    space_id   = data.get('space_id')
    confidence = float(data.get('confidence', 1.0))
    source     = data.get('source', 'api')

    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
    except ParkingLot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Lot not found'}, status=404)

    if space_id:
        try:
            space = ParkingSpace.objects.get(space_id=space_id, parking_lot=lot)
        except ParkingSpace.DoesNotExist:
            space = lot.spaces.filter(is_occupied=True).first()
    else:
        space = lot.spaces.filter(is_occupied=True).first()

    if not space:
        return JsonResponse({'success': False, 'error': 'No occupied spaces found'}, status=409)

    open_ticket = ParkingTicket.objects.filter(
        parking_space=space, exit_time__isnull=True
    ).first()
    if open_ticket:
        open_ticket.exit_time = timezone.now()
        open_ticket.fee = round(open_ticket.duration_hours() * float(lot.hourly_rate), 2)
        open_ticket.save()

    space.is_occupied = False
    space.save()
    lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
    lot.save()

    event = ParkingDetectionEvent.objects.create(
        lot=lot, space=space, event_type='exit',
        plate_number=plate, confidence=confidence, source=source, processed=True,
    )

    if lot.available_spaces == 1:
        _notify_space_available(lot)

    return JsonResponse({
        'success':    True,
        'event_id':   event.id,
        'space_id':   space.space_id,
        'lot':        lot.location,
        'occupancy':  lot.occupancy_rate(),
        'ticket_closed': open_ticket is not None,
        'message': f'Exit recorded. Space {space.space_id} is now free.',
    })


# -- Notification helpers ------------------------------------------------------

def _notify_nearly_full(lot, rate):
    from django.contrib.auth.models import User as AuthUser
    active_tickets = ParkingTicket.objects.filter(
        parking_space__parking_lot=lot, exit_time__isnull=True
    ).select_related('vehicle', 'user')
    users_notified = set()
    for t in active_tickets:
        try:
            # Use the direct user FK first; fall back to name matching for legacy data
            owner = t.user
            if owner is None:
                owner = AuthUser.objects.filter(
                    username__iexact=t.vehicle.owner_name
                ).first() or AuthUser.objects.filter(
                    first_name__iexact=t.vehicle.owner_name.split()[0] if t.vehicle.owner_name else ''
                ).first()
            if owner and owner.id not in users_notified:
                UserNotification.objects.create(
                    user=owner,
                    title=f'{lot.location} is nearly full',
                    message=f'The parking lot is at {rate}% capacity. Consider leaving soon if your session is ending.',
                    notif_type='nearly_full',
                    lot=lot,
                )
                users_notified.add(owner.id)
        except Exception:
            pass


def _notify_space_available(lot):
    last_30 = timezone.now() - timedelta(days=30)
    # Notify users who parked here recently but don't have an active session there now
    recent_user_ids = (
        ParkingTicket.objects
        .filter(
            parking_space__parking_lot=lot,
            entry_time__gte=last_30,
            user__isnull=False,
            exit_time__isnull=False,  # completed sessions only
        )
        .exclude(
            # exclude anyone currently parked here
            user__in=ParkingTicket.objects.filter(
                parking_space__parking_lot=lot, exit_time__isnull=True
            ).values('user')
        )
        .values_list('user_id', flat=True)
        .distinct()
    )
    for uid in recent_user_ids:
        UserNotification.objects.create(
            user_id=uid,
            title=f'Space available at {lot.location}',
            message=f'A parking space just opened up at {lot.location}. Book now before it fills up!',
            notif_type='space_available',
            lot=lot,
        )


# -- User Notification APIs ----------------------------------------------------

@login_required
def api_user_notifications(request):
    """GET /api/notifications/data/"""
    base_qs = UserNotification.objects.filter(user=request.user)
    unread  = base_qs.filter(is_read=False).count()
    notifs  = base_qs.order_by('-created_at')[:30]
    data = [{
        'id':         n.id,
        'title':      n.title,
        'message':    n.message,
        'type':       n.notif_type,
        'is_read':    n.is_read,
        'lot':        n.lot.location if n.lot else None,
        'created_at': n.created_at.isoformat(),
        'time_ago':   _time_ago(n.created_at),
    } for n in notifs]
    return JsonResponse({'success': True, 'notifications': data, 'unread': unread})


@login_required
def api_mark_notification_read(request, notif_id):
    """POST /api/notifications/<id>/read/"""
    if request.method == 'POST':
        UserNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required
def api_mark_all_read(request):
    """POST /api/notifications/mark-all-read/"""
    if request.method == 'POST':
        UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


def _time_ago(dt):
    from django.utils import timezone as tz
    diff = tz.now() - dt
    s = diff.total_seconds()
    if s < 60:    return 'Just now'
    if s < 3600:  return f'{int(s/60)}m ago'
    if s < 86400: return f'{int(s/3600)}h ago'
    return f'{int(s/86400)}d ago'


# -- Lot Detail API ------------------------------------------------------------

@login_required
def api_lot_detail(request, lot_id):
    """GET /api/lot/<lot_id>/"""
    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
    except ParkingLot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)

    total = lot.spaces.count()
    occ   = lot.spaces.filter(is_occupied=True).count()
    avail = total - occ
    rate  = round(occ / total * 100) if total else 0

    recent = ParkingTicket.objects.filter(
        parking_space__parking_lot=lot
    ).select_related('vehicle').order_by('-entry_time')[:5]

    return JsonResponse({
        'success': True,
        'lot': {
            'id':          lot.lot_id,
            'location':    lot.location,
            'description': lot.description,
            'lat':         lot.latitude,
            'lng':         lot.longitude,
            'total':       total,
            'available':   avail,
            'occupied':    occ,
            'rate':        rate,
            'status':      lot.status(),
            'hourly_rate': float(lot.hourly_rate),
            'features':    [f.strip() for f in lot.features.split(',') if f.strip()],
        },
        'recent': [{
            'plate': t.vehicle.plate_number,
            'entry': t.entry_time.isoformat(),
            'active': t.exit_time is None,
        } for t in recent],
    })


# -- Map data ------------------------------------------------------------------

@login_required
def api_map_data(request):
    """GET /api/map-data/"""
    lots = ParkingLot.objects.filter(is_active=True).prefetch_related('spaces')
    data = []
    for lot in lots:
        total = lot.spaces.count()
        occ   = lot.spaces.filter(is_occupied=True).count()
        avail = total - occ
        data.append({
            'id':        lot.lot_id,
            'location':  lot.location,
            'lat':       lot.latitude  or -1.9441,
            'lng':       lot.longitude or 30.0619,
            'total':     total,
            'available': avail,
            'rate':      round(occ/total*100) if total else 0,
            'status':    lot.status(),
            'hourly_rate': float(lot.hourly_rate),
        })
    return JsonResponse({'success': True, 'lots': data, 'count': len(data)})


# -- Admin: ML Insights API ---------------------------------------------------

@_admin_required
def api_ml_insights(request):
    from .ml_engine import get_ml_insights
    data = get_ml_insights()
    return JsonResponse({'success': True, 'data': data})


# -- Admin: plate lookup (no user restriction — admin sees all sessions) ------

@_admin_required
def api_admin_lookup_plate(request):
    """
    POST /api/admin-lookup-plate/
    Accept plate_number text OR an image file.
    Returns full session + owner info for any active ticket matching that plate.
    Unlike the user-facing api_lookup_plate, this is not restricted to the
    requesting user's own vehicles.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    plate = request.POST.get('plate_number', '').strip().upper()

    # LPR from image if no text supplied
    if not plate and request.FILES.get('image'):
        img_file = request.FILES['image']
        if img_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Image too large (max 10 MB).'})
        try:
            from .license_plate import detect_plate
            lpr = detect_plate(img_file.read())
            if lpr.get('success') and lpr.get('plates'):
                plate = (lpr['plates'][0].get('text') or '').strip().upper()
            if not plate:
                return JsonResponse({'success': False, 'error': 'Could not read plate from image.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'LPR error: {e}'})

    if not plate:
        return JsonResponse({'success': False, 'error': 'Provide a plate number or image.'})

    # --- Find vehicle. Try exact match first, then case-insensitive fuzzy ---
    vehicle = (
        Vehicle.objects.filter(plate_number__iexact=plate).first()
    )
    if not vehicle:
        # Try partial match so minor OCR errors (space/dash) still resolve
        clean = plate.replace(' ', '').replace('-', '')
        vehicle = Vehicle.objects.filter(
            plate_number__iregex=r'^' + ''.join(f'{c}[-\\s]?' for c in clean) + '$'
        ).first()

    if not vehicle:
        return JsonResponse({
            'success': False,
            'error': f'No vehicle registered with plate "{plate}". '
                     f'Check the plate or register the vehicle first.',
        })

    active_ticket = (
        ParkingTicket.objects
        .filter(vehicle=vehicle, exit_time__isnull=True)
        .select_related('vehicle', 'parking_space__parking_lot', 'user')
        .order_by('-entry_time')
        .first()
    )

    if not active_ticket:
        return JsonResponse({
            'success': False,
            'error': f'Plate {vehicle.plate_number} is registered but has no active parking session.',
        })

    lot      = active_ticket.parking_space.parking_lot if active_ticket.parking_space else None
    fee      = active_ticket.calculated_fee()
    duration = active_ticket.duration_hours()

    # Owner display name
    if active_ticket.user:
        owner = active_ticket.user.get_full_name() or active_ticket.user.username
        owner_email = active_ticket.user.email or '—'
    else:
        owner = vehicle.owner_name or '—'
        owner_email = '—'

    entry_local = timezone.localtime(active_ticket.entry_time)

    return JsonResponse({
        'success':      True,
        'ticket_id':    active_ticket.ticket_id,
        'plate':        vehicle.plate_number,
        'vehicle_type': vehicle.vehicle_type,
        'owner':        owner,
        'owner_email':  owner_email,
        'location':     lot.location if lot else '—',
        'space_id':     active_ticket.parking_space.space_id if active_ticket.parking_space else '—',
        'entry_time':   entry_local.strftime('%d %b %Y %H:%M'),
        'duration_h':   round(duration, 2),
        'fee':          str(fee),
        'hourly_rate':  str(lot.hourly_rate) if lot else '0',
    })


@_admin_required
def api_admin_close_session(request):
    """
    POST /api/admin-close-session/
    Close an active parking ticket identified by ticket_id.
    Frees the space, records payment, notifies the user.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    ticket_id      = request.POST.get('ticket_id', '').strip()
    payment_method = request.POST.get('payment_method', 'Cash')

    try:
        t = ParkingTicket.objects.select_related(
            'vehicle', 'parking_space__parking_lot', 'user'
        ).get(ticket_id=ticket_id, exit_time__isnull=True)
    except ParkingTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found or already closed.'})

    with transaction.atomic():
        t.exit_time = timezone.now()
        rate = t.parking_space.parking_lot.hourly_rate if t.parking_space else 0
        t.fee = Decimal(str(round(t.duration_hours() * float(rate), 2)))
        t.save()

        space_id = None
        lot      = None
        if t.parking_space:
            space_id = t.parking_space.space_id
            t.parking_space.is_occupied       = False
            t.parking_space.occupied_by_plate = ''
            t.parking_space.save(update_fields=['is_occupied', 'occupied_by_plate'])
            lot = t.parking_space.parking_lot
            lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
            lot.save(update_fields=['available_spaces'])

        Payment.objects.create(
            amount=t.fee or Decimal('0'),
            payment_method=payment_method,
            ticket=t,
        )

        if t.user:
            fee_str = f'${t.fee}' if t.fee else '$0.00'
            UserNotification.objects.create(
                user=t.user,
                title=f'Session ended — {t.vehicle.plate_number}',
                message=(
                    f'Your parking session at {lot.location if lot else "the lot"} '
                    f'has ended. Duration: {t.duration_hours():.1f}h · '
                    f'Fee: {fee_str} · Payment: {payment_method}. '
                    f'Thank you for using PARMS!'
                ),
                notif_type='session_ended',
                lot=lot,
            )

        if lot and lot.available_spaces == 1:
            _notify_space_available(lot)

        # Email receipt
        try:
            from .email_utils import send_session_email
            send_session_email(t, payment_method)
        except Exception:
            pass

    return JsonResponse({
        'success':        True,
        'ticket_id':      t.ticket_id,
        'plate':          t.vehicle.plate_number,
        'fee':            str(t.fee),
        'payment_method': payment_method,
        'space_id':       space_id,
        'duration_h':     round(t.duration_hours(), 2),
    })


# -- Admin: License Plate Detection -------------------------------------------

@_admin_required
def admin_detect_plate(request):
    """POST /api/detect-plate/ — run Haar Cascade LP detection on uploaded image."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    img_file = request.FILES.get('image')
    if not img_file:
        return JsonResponse({'success': False, 'error': 'No image file received.'}, status=400)

    # 10 MB guard
    if img_file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Image too large (max 10 MB).'}, status=400)

    try:
        from .license_plate import detect_plate
        result = detect_plate(img_file.read())
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Detection error: {e}'}, status=500)


# -- Admin: Detection Event management ----------------------------------------

@_admin_required
def admin_detection_events(request):
    events = ParkingDetectionEvent.objects.select_related('lot', 'space').order_by('-detected_at')[:100]
    context = {'events': events, 'total': events.count(), 'active_tab': 'detection'}
    return render(request, 'dashboard.html', context)


# -- Chatbot API ---------------------------------------------------------------

def chatbot_message(request):
    """Handle chatbot messages using Anthropic Claude API."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'success': False, 'error': 'Empty message'}, status=400)
        
        # Get Anthropic API key from settings
        from decouple import config
        api_key = config('ANTHROPIC_API_KEY', default='')
        
        if not api_key:
            return JsonResponse({'success': False, 'error': 'Chatbot not configured'}, status=500)
        
        # Call Anthropic API
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        system_prompt = """You are a helpful assistant for PARMS - a Smart Parking Management System.
        
PARMS is an innovative platform that helps drivers find, book, and pay for parking spaces in real-time.

Key features to mention:
- Real-time parking availability across multiple locations
- Instant QR-coded tickets (no paper needed)
- Smart payment system (MTN Mobile Money, PayPal, cards, cash)
- Automatic fee calculation based on actual time parked
- Analytics dashboard for parking lot managers
- Mobile-first design for easy use on phones
- 24/7 support available

When users ask questions about parking, PARMS features, payment, bookings, or how the system works, provide clear, helpful explanations.

Be friendly, professional, and concise. Always encourage users to try PARMS and offer to help them get started.
If the user seems interested in using PARMS or has other needs, ask for their contact information (name, email, phone) at the end so we can follow up with them."""
        
        message = client.messages.create(
            model="claude-opus-4-1",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        bot_response = message.content[0].text
        
        return JsonResponse({
            'success': True,
            'message': bot_response
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except ImportError:
        return JsonResponse({'success': False, 'error': 'Anthropic library not installed'}, status=500)
    except Exception as e:
        logger.error(f'Chatbot error: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error processing message'}, status=500)


def chatbot_contact_submit(request):
    """Handle contact submission from chatbot."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        
        # Validate
        if not all([name, email, message]):
            return JsonResponse({'success': False, 'error': 'Name, email, and message required'}, status=400)
        
        # Save to ContactMessage model
        ContactMessage.objects.create(
            full_name=name,
            email=email,
            phone=phone or None,
            message=message,
            subject='Chatbot Inquiry'
        )
        
        return JsonResponse({'success': True, 'message': 'Contact info saved! We will reach out soon.'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f'Chatbot contact submit error: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error saving contact'}, status=500)


# -- Error handlers ------------------------------------------------------------

def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)
