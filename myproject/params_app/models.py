
# Create your models here.

from django.db import models

# Parking Lot Model
class ParkingLot(models.Model):
    lot_id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255)
    total_spaces = models.IntegerField()
    available_spaces = models.IntegerField()

    def __str__(self):
        return f"Parking Lot {self.lot_id} - {self.location}"


# Vehicle Model
class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50, choices=[
        ('Car', 'Car'),
        ('Motorcycle', 'Motorcycle'),
        ('Truck', 'Truck')
    ])
    owner_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type})"


# Parking Space Model
class ParkingSpace(models.Model):
    space_id = models.AutoField(primary_key=True)
    space_type = models.CharField(
        max_length=50,
        choices=[
            ('Compact', 'Compact'),
            ('Large', 'Large'),
            ('Electric Vehicle', 'Electric Vehicle')
        ]
    )
    is_occupied = models.BooleanField(default=False)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spaces')

    def __str__(self):
        return f"Space {self.space_id} in Lot {self.parking_lot}"



# Parking Ticket Model
class ParkingTicket(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='tickets')
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE, related_name='tickets')

    def __str__(self):
        return f"Ticket {self.ticket_id} for Vehicle {self.vehicle}"


# User (Admin/Staff) Model
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=[
        ('Admin', 'Admin'),
        ('Staff', 'Staff')
    ])
    contact_info = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.role})"


# Payment Model
class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Digital Wallet', 'Digital Wallet')
    ])
    date = models.DateTimeField(auto_now_add=True)
    ticket = models.OneToOneField(ParkingTicket, on_delete=models.CASCADE, related_name='payment')

    def __str__(self):
        return f"Payment {self.payment_id} for Ticket {self.ticket}"
from django.db import models

class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

