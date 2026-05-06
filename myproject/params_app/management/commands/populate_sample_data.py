"""
Django management command to populate database with sample data
Usage: python manage.py populate_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from params_app.models import ParkingLot, Vehicle, ParkingSpace, ParkingTicket, Payment, ContactMessage
from decimal import Decimal
import random
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample parking lots
        parking_lots = []
        lot_names = ['Downtown Plaza', 'Shopping Mall', 'Airport Terminal', 'University Campus', 'City Center']
        
        for i, name in enumerate(lot_names, 1):
            lot, created = ParkingLot.objects.get_or_create(
                location=name,
                defaults={
                    'total_spaces': random.randint(50, 200),
                    'available_spaces': random.randint(10, 50)
                }
            )
            parking_lots.append(lot)
            if created:
                self.stdout.write(f'✓ Created parking lot: {name}')
        
        # Create sample parking spaces
        space_types = ['Compact', 'Large', 'Electric Vehicle']
        for lot in parking_lots:
            for i in range(lot.total_spaces):
                space, created = ParkingSpace.objects.get_or_create(
                    parking_lot=lot,
                    space_type=random.choice(space_types),
                    defaults={
                        'is_occupied': random.choice([True, False])
                    }
                )
                if created and i < 5:  # Only show first 5 for each lot
                    self.stdout.write(f'✓ Created parking space in {lot.location}')
        
        # Create sample vehicles
        plate_numbers = ['RAB123A', 'RCA456B', 'RWA789C', 'RUD321D', 'RBF654E', 'RBC987F']
        vehicle_types = ['Car', 'Motorcycle', 'Truck']
        owner_names = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson', 'Diana Prince']
        
        vehicles = []
        for i, plate in enumerate(plate_numbers):
            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=plate,
                defaults={
                    'vehicle_type': random.choice(vehicle_types),
                    'owner_name': owner_names[i % len(owner_names)]
                }
            )
            vehicles.append(vehicle)
            if created:
                self.stdout.write(f'✓ Created vehicle: {plate}')
        
        # Create sample parking tickets
        spaces = list(ParkingSpace.objects.all()[:20])  # Get first 20 spaces
        for i in range(15):  # Create 15 sample tickets
            vehicle = random.choice(vehicles)
            space = random.choice(spaces)
            
            # Create entry time (last 30 days)
            entry_time = timezone.now() - timedelta(days=random.randint(0, 30))
            
            # Some tickets have exit time, some don't (active)
            exit_time = None
            if random.choice([True, False]):
                exit_time = entry_time + timedelta(hours=random.randint(1, 8))
            
            fee = Decimal(str(random.uniform(5.0, 50.0))).quantize(Decimal('0.01'))
            
            ticket, created = ParkingTicket.objects.get_or_create(
                vehicle=vehicle,
                parking_space=space,
                entry_time=entry_time,
                defaults={
                    'exit_time': exit_time,
                    'fee': fee
                }
            )
            
            if created:
                # Create payment for some tickets
                if exit_time and random.choice([True, False]):
                    payment_methods = ['Cash', 'Credit Card', 'Digital Wallet']
                    Payment.objects.get_or_create(
                        ticket=ticket,
                        defaults={
                            'amount': fee,
                            'payment_method': random.choice(payment_methods),
                            'date': exit_time
                        }
                    )
                
                self.stdout.write(f'✓ Created parking ticket for {vehicle.plate_number}')
        
        # Create sample contact messages
        sample_messages = [
            {
                'full_name': 'Customer One',
                'email': 'customer1@example.com',
                'message': 'Great parking system! Very easy to use.'
            },
            {
                'full_name': 'Customer Two', 
                'email': 'customer2@example.com',
                'message': 'Had some issues with payment. Please help.'
            },
            {
                'full_name': 'Customer Three',
                'email': 'customer3@example.com', 
                'message': 'Suggestion: Add mobile app for easier access.'
            },
            {
                'full_name': 'Customer Four',
                'email': 'customer4@example.com',
                'message': 'Parking lot location is perfect. Thank you!'
            }
        ]
        
        for msg_data in sample_messages:
            message, created = ContactMessage.objects.get_or_create(
                email=msg_data['email'],
                defaults=msg_data
            )
            if created:
                self.stdout.write(f'✓ Created contact message from {msg_data["full_name"]}')
        
        # Create sample regular users
        sample_users = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_johnson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
        ]
        
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': False
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'✓ Created user: {user_data["username"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Sample data created successfully!\n'
                'You can now:\n'
                '1. Login as admin (if superuser exists)\n'
                '2. Login as regular users (username: john_doe, password: password123)\n'
                '3. View dashboards with real data\n'
                '4. Test all functionality'
            )
        )
