import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from params_app.models import ParkingTicket, UserNotification

created = 0
qs = ParkingTicket.objects.select_related(
    'user', 'vehicle', 'parking_space__parking_lot'
).filter(user__isnull=False)

for t in qs:
    lot = t.parking_space.parking_lot if t.parking_space else None
    loc = lot.location if lot else 'the parking lot'
    space_num = str(t.parking_space.space_id) if t.parking_space else '?'

    # Booking notification
    exists = UserNotification.objects.filter(
        user=t.user, notif_type='booking',
        message__icontains='Ticket #' + str(t.ticket_id)
    ).exists()
    if not exists:
        UserNotification.objects.create(
            user=t.user,
            title='Parking booked - Space #' + space_num,
            message='Your spot at ' + loc + ' is confirmed. Ticket #' + str(t.ticket_id) + '.',
            notif_type='booking',
            lot=lot,
        )
        created += 1

    # Session ended notification
    if t.exit_time:
        exists2 = UserNotification.objects.filter(
            user=t.user, notif_type='session_ended',
            message__icontains=t.vehicle.plate_number
        ).exists()
        if not exists2:
            fee_str = ' Fee: $' + str(t.fee) + '.' if t.fee else ''
            UserNotification.objects.create(
                user=t.user,
                title='Session ended - ' + t.vehicle.plate_number,
                message='Your parking session at ' + loc + ' has been completed.' + fee_str,
                notif_type='session_ended',
                lot=lot,
            )
            created += 1

print('Created ' + str(created) + ' retroactive notifications')
