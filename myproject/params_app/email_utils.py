"""
PARMS email helpers
===================
Call send_session_email() whenever a parking session ends.
Falls back silently if email is not configured (EMAIL_BACKEND = console).
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


def send_session_email(ticket, payment_method='Cash'):
    """
    Send a session-ended receipt email to the ticket owner.
    Silent no-op when no recipient email is available or email is mis-configured.
    """
    if not ticket.user or not ticket.user.email:
        return

    try:
        lot  = ticket.parking_space.parking_lot if ticket.parking_space else None
        ctx  = {
            'ticket':         ticket,
            'lot':            lot,
            'payment_method': payment_method,
            'user':           ticket.user,
            'fee':            ticket.fee or 0,
            'duration':       round(ticket.duration_hours(), 2),
            'site_name':      'PARMS Smart Parking',
        }

        subject    = f'[PARMS] Parking session ended — {ticket.vehicle.plate_number}'
        text_body  = (
            f"Hello {ticket.user.get_full_name() or ticket.user.username},\n\n"
            f"Your parking session has ended.\n\n"
            f"Plate:    {ticket.vehicle.plate_number}\n"
            f"Location: {lot.location if lot else '—'}\n"
            f"Entry:    {timezone.localtime(ticket.entry_time).strftime('%d %b %Y %H:%M')}\n"
            f"Exit:     {timezone.localtime(ticket.exit_time).strftime('%d %b %Y %H:%M') if ticket.exit_time else '—'}\n"
            f"Duration: {round(ticket.duration_hours(), 2)} hrs\n"
            f"Fee:      ${ticket.fee or 0}\n"
            f"Payment:  {payment_method}\n\n"
            f"Thank you for using PARMS Smart Parking System!\n"
            f"Have a safe journey.\n\n"
            f"— The PARMS Team"
        )
        html_body  = render_to_string('email/session_ended.html', ctx)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ticket.user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(f'Failed to send session email for ticket {ticket.id}: {str(e)}', exc_info=True)
