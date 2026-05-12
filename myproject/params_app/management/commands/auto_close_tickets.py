"""
Management command: auto_close_tickets
======================================
Finds parking tickets that have been active for more than
PARKING_SESSION_MAX_HOURS (default 24) and closes them automatically.

Run manually:
    python manage.py auto_close_tickets

Add to Render cron (Dashboard → Cron Jobs → New Cron Job):
    Command : python manage.py auto_close_tickets
    Schedule: 0 * * * *   (every hour)
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from params_app.models import ParkingTicket, Payment, UserNotification


class Command(BaseCommand):
    help = 'Auto-close parking sessions older than PARKING_SESSION_MAX_HOURS hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Print what would be closed without actually closing anything.',
        )
        parser.add_argument(
            '--hours', type=int, default=None,
            help='Override the max hours threshold from settings.',
        )

    def handle(self, *args, **options):
        max_hours = options['hours'] or getattr(settings, 'PARKING_SESSION_MAX_HOURS', 24)
        dry_run   = options['dry_run']
        cutoff    = timezone.now() - timedelta(hours=max_hours)

        expired = (
            ParkingTicket.objects
            .filter(exit_time__isnull=True, entry_time__lt=cutoff)
            .select_related('vehicle', 'parking_space__parking_lot', 'user')
            .order_by('entry_time')
        )

        if not expired.exists():
            self.stdout.write(self.style.SUCCESS('No expired sessions found.'))
            return

        self.stdout.write(f'Found {expired.count()} session(s) older than {max_hours}h.')

        closed = 0
        for ticket in expired:
            plate    = ticket.vehicle.plate_number if ticket.vehicle else '—'
            lot_name = (ticket.parking_space.parking_lot.location
                        if ticket.parking_space and ticket.parking_space.parking_lot else '—')

            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Would close ticket #{ticket.ticket_id} — {plate} @ {lot_name}')
                continue

            # Cap exit time at entry + max_hours (fair billing)
            ticket.exit_time = ticket.entry_time + timedelta(hours=max_hours)
            rate = (ticket.parking_space.parking_lot.hourly_rate
                    if ticket.parking_space and ticket.parking_space.parking_lot else 0)
            ticket.fee = Decimal(str(round(float(rate) * max_hours, 2)))
            ticket.save()

            # Free the space
            lot = None
            if ticket.parking_space:
                ticket.parking_space.is_occupied       = False
                ticket.parking_space.occupied_by_plate = ''
                ticket.parking_space.save(update_fields=['is_occupied', 'occupied_by_plate'])
                lot = ticket.parking_space.parking_lot
                lot.available_spaces = lot.spaces.filter(is_occupied=False).count()
                lot.save(update_fields=['available_spaces'])

            # Auto-create a payment record (zero / no-charge) so reports stay clean
            if not hasattr(ticket, 'payment'):
                try:
                    Payment.objects.create(
                        amount=ticket.fee or Decimal('0'),
                        payment_method='Auto-closed',
                        ticket=ticket,
                    )
                except Exception:
                    pass  # payment might already exist

            # Notify the user
            if ticket.user:
                fee_str = f'${ticket.fee}' if ticket.fee else '$0.00'
                UserNotification.objects.create(
                    user=ticket.user,
                    title=f'Session auto-closed — {plate}',
                    message=(
                        f'Your parking session at {lot_name} was automatically '
                        f'closed after {max_hours} hours. '
                        f'Fee: {fee_str}. Please visit the office if you have questions.'
                    ),
                    notif_type='session_ended',
                    lot=lot,
                )

                # Send email notification
                try:
                    from params_app.email_utils import send_session_email
                    send_session_email(ticket, 'Auto-closed (24h limit)')
                except Exception:
                    pass

            closed += 1
            self.stdout.write(f'  ✓ Closed ticket #{ticket.ticket_id} — {plate} @ {lot_name}  fee={ticket.fee}')

        self.stdout.write(self.style.SUCCESS(f'Done. {closed} session(s) auto-closed.'))
