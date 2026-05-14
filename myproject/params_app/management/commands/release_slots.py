from django.core.management.base import BaseCommand
from params_app.models import ParkingSpace, ParkingLot
from django.utils import timezone


class Command(BaseCommand):
    help = 'Release all occupied parking spaces and close their tickets'

    def handle(self, *args, **options):
        """Release all occupied spaces and update their parking lots"""
        
        # Get all occupied spaces
        occupied_spaces = ParkingSpace.objects.filter(is_occupied=True)
        count = occupied_spaces.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No occupied spaces to release.'))
            return
        
        # Release each space
        for space in occupied_spaces:
            lot = space.parking_lot
            
            # Close any open tickets for this space
            open_tickets = space.tickets.filter(exit_time__isnull=True)
            for ticket in open_tickets:
                ticket.exit_time = timezone.now()
                ticket.fee = ticket.calculated_fee()
                ticket.save()
                self.stdout.write(
                    f'  Closed ticket {ticket.ticket_id} for {ticket.vehicle.plate_number} '
                    f'with fee ${ticket.fee}'
                )
            
            # Release the space
            space.is_occupied = False
            space.occupied_by_plate = ''
            space.save()
            
            # Update parking lot available spaces
            lot.available_spaces = ParkingSpace.objects.filter(
                parking_lot=lot, is_occupied=False
            ).count()
            lot.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully released {count} occupied parking space(s)'
            )
        )
        
        # Show summary
        self.stdout.write(self.style.SUCCESS('\nParking Lot Summary:'))
        for lot in ParkingLot.objects.all():
            occupied = lot.total_spaces - lot.available_spaces
            self.stdout.write(
                f'  {lot.location}: {lot.available_spaces}/{lot.total_spaces} available '
                f'({occupied} occupied, {lot.occupancy_rate()}% full)'
            )
