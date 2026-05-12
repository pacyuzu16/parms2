from django.db import models
from django.contrib.auth.models import User as AuthUser


# -- Parking Lot ---------------------------------------------------------------
class ParkingLot(models.Model):
    lot_id          = models.AutoField(primary_key=True)
    location        = models.CharField(max_length=255)
    total_spaces    = models.IntegerField()
    available_spaces = models.IntegerField()

    # NEW: location & pricing
    latitude        = models.FloatField(null=True, blank=True)
    longitude       = models.FloatField(null=True, blank=True)
    hourly_rate     = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    description     = models.TextField(blank=True, default='')
    features        = models.CharField(max_length=500, blank=True, default='')  # comma-separated: CCTV,Covered,EV Charging
    is_active       = models.BooleanField(default=True)

    def occupancy_rate(self):
        if self.total_spaces == 0:
            return 0
        occupied = self.total_spaces - self.available_spaces
        return round(occupied / self.total_spaces * 100)

    def status(self):
        rate = self.occupancy_rate()
        if rate >= 90:
            return "full"
        elif rate >= 60:
            return "busy"
        elif rate >= 30:
            return "moderate"
        return "available"

    def __str__(self):
        return f"Parking Lot {self.lot_id} - {self.location}"


# -- Vehicle -------------------------------------------------------------------
class Vehicle(models.Model):
    vehicle_id   = models.AutoField(primary_key=True)
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50, choices=[
        ("Car", "Car"), ("Motorcycle", "Motorcycle"), ("Truck", "Truck")
    ])
    owner_name   = models.CharField(max_length=255)
    # Direct link to auth user — enables plate-based login and quick lookup
    user         = models.ForeignKey(
        AuthUser, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='vehicles'
    )

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type})"


# -- Parking Space -------------------------------------------------------------
class ParkingSpace(models.Model):
    space_id   = models.AutoField(primary_key=True)
    space_type = models.CharField(max_length=50, choices=[
        ("Compact", "Compact"),
        ("Large", "Large"),
        ("Electric Vehicle", "Electric Vehicle"),
    ])
    is_occupied      = models.BooleanField(default=False)
    occupied_by_plate = models.CharField(max_length=20, blank=True, default='')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name="spaces")

    def __str__(self):
        return f"Space {self.space_id} in Lot {self.parking_lot}"


# -- Parking Ticket ------------------------------------------------------------
class ParkingTicket(models.Model):
    ticket_id    = models.AutoField(primary_key=True)
    entry_time   = models.DateTimeField(auto_now_add=True)
    exit_time    = models.DateTimeField(null=True, blank=True)
    fee          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vehicle      = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="tickets")
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE, related_name="tickets")
    user         = models.ForeignKey(
        AuthUser, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tickets"
    )

    def duration_hours(self):
        from django.utils import timezone
        end = self.exit_time or timezone.now()
        delta = end - self.entry_time
        return round(delta.total_seconds() / 3600, 2)

    def calculated_fee(self):
        if self.fee:
            return self.fee
        rate = self.parking_space.parking_lot.hourly_rate
        return round(self.duration_hours() * float(rate), 2)

    def __str__(self):
        return f"Ticket {self.ticket_id} for Vehicle {self.vehicle}"


# -- Payment -------------------------------------------------------------------
class Payment(models.Model):
    payment_id     = models.AutoField(primary_key=True)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ("Cash", "Cash"), ("Credit Card", "Credit Card"), ("Digital Wallet", "Digital Wallet"),
        ("MTN MoMo", "MTN MoMo"), ("PayPal", "PayPal"),
    ])
    date   = models.DateTimeField(auto_now_add=True)
    ticket = models.OneToOneField(ParkingTicket, on_delete=models.CASCADE, related_name="payment")

    def __str__(self):
        return f"Payment {self.payment_id} for Ticket {self.ticket}"


# -- User Profile (avatar photo) -----------------------------------------------
class UserProfile(models.Model):
    user  = models.OneToOneField(AuthUser, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def photo_url(self):
        """Return the photo URL, handling both local filesystem and cloud storage.

        - Cloudinary (production): .path raises NotImplementedError, so we skip
          the existence check and trust the URL — Cloudinary URLs are permanent.
        - Local filesystem (dev): check the file actually exists so a stale DB
          path after a manual deletion doesn't return a broken URL.
        """
        if not self.photo:
            return None
        try:
            import os
            if not os.path.exists(self.photo.path):
                return None          # file was deleted locally
        except (NotImplementedError, ValueError):
            pass                     # cloud storage — URL is always valid
        try:
            return self.photo.url
        except Exception:
            return None


# -- Contact Message -----------------------------------------------------------
class ContactMessage(models.Model):
    full_name    = models.CharField(max_length=100)
    email        = models.EmailField()
    message      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


# -- Detection Event -----------------------------------------------------------
# Records entry/exit events from cameras, sensors, or manual input.
class ParkingDetectionEvent(models.Model):
    EVENT_TYPES = [("entry", "Entry"), ("exit", "Exit")]
    SOURCES     = [("camera", "Camera"), ("sensor", "Sensor"), ("manual", "Manual"), ("api", "API")]

    lot         = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name="detection_events")
    space       = models.ForeignKey(ParkingSpace, null=True, blank=True, on_delete=models.SET_NULL)
    event_type  = models.CharField(max_length=10, choices=EVENT_TYPES)
    plate_number = models.CharField(max_length=20, blank=True, default="")
    detected_at = models.DateTimeField(auto_now_add=True)
    confidence  = models.FloatField(default=1.0)
    source      = models.CharField(max_length=20, choices=SOURCES, default="manual")
    processed   = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_type} @ {self.lot.location} [{self.source}] {self.detected_at:%Y-%m-%d %H:%M}"


# -- User Notification ---------------------------------------------------------
class UserNotification(models.Model):
    NOTIF_TYPES = [
        ("space_available", "Space Available"),
        ("nearly_full",     "Nearly Full"),
        ("expiry_warning",  "Expiry Warning"),
        ("session_ended",   "Session Ended"),
        ("booking",         "Booking Confirmed"),
        ("system",          "System"),
    ]

    user    = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="parking_notifications")
    title   = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default="system")
    lot     = models.ForeignKey(ParkingLot, null=True, blank=True, on_delete=models.SET_NULL)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notif_type}] {self.title} -> {self.user.username}"
