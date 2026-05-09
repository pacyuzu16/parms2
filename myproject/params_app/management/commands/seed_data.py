from django.core.management.base import BaseCommand
from params_app.models import ParkingLot, ParkingSpace


LOTS = [
    {
        "location": "Makuza Peace Plaza Underground",
        "lat": -1.9500, "lng": 30.0619, "total": 20, "rate": 5.00,
        "description": "Underground parking beneath Makuza Peace Plaza. Central Kigali.",
        "features": "CCTV,Covered,Security Guard,24/7",
    },
    {
        "location": "Kigali City Tower Parking",
        "lat": -1.9480, "lng": 30.0590, "total": 20, "rate": 4.00,
        "description": "Multi-level parking at City Tower. Walking distance to CBD.",
        "features": "CCTV,Covered,Elevator",
    },
    {
        "location": "Union Trade Centre (UTC)",
        "lat": -1.9456, "lng": 30.0612, "total": 20, "rate": 3.50,
        "description": "Surface parking at UTC shopping mall.",
        "features": "CCTV,Open Air,Security Guard",
    },
    {
        "location": "Kigali Heights Parking",
        "lat": -1.9523, "lng": 30.0887, "total": 20, "rate": 6.00,
        "description": "Modern parking at Kigali Heights complex, Kacyiru.",
        "features": "CCTV,Covered,EV Charging,Elevator,24/7",
    },
    {
        "location": "Nyamirambo Stadium Parking",
        "lat": -1.9763, "lng": 30.0454, "total": 20, "rate": 2.00,
        "description": "Open-air parking near Nyamirambo Stadium.",
        "features": "Open Air,Security Guard",
    },
    {
        "location": "Remera Taxi Park Parking",
        "lat": -1.9386, "lng": 30.0991, "total": 20, "rate": 2.50,
        "description": "Convenient parking near Remera bus terminal.",
        "features": "Open Air,CCTV",
    },
]

SPACE_TYPES = [
    "Compact", "Compact", "Large", "Compact", "Electric Vehicle",
    "Large", "Compact", "Compact", "Large", "Compact",
]


class Command(BaseCommand):
    help = "Seed initial parking lot data for PARMS"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true",
                            help="Clear existing lots before seeding")

    def handle(self, *args, **options):
        if options["clear"]:
            ParkingLot.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all parking lots."))

        created = 0
        for data in LOTS:
            lot, new = ParkingLot.objects.get_or_create(
                location=data["location"],
                defaults={
                    "total_spaces":     data["total"],
                    "available_spaces": data["total"],
                    "latitude":         data["lat"],
                    "longitude":        data["lng"],
                    "hourly_rate":      data["rate"],
                    "description":      data["description"],
                    "features":         data["features"],
                    "is_active":        True,
                },
            )
            if new:
                for i in range(data["total"]):
                    ParkingSpace.objects.create(
                        parking_lot=lot,
                        space_type=SPACE_TYPES[i % len(SPACE_TYPES)],
                        is_occupied=False,
                    )
                created += 1
                self.stdout.write(self.style.SUCCESS(
                    "  Created: " + lot.location + " (" + str(data["total"]) + " spaces)"
                ))
            else:
                self.stdout.write("  Skipped (exists): " + lot.location)

        self.stdout.write(self.style.SUCCESS(
            "Done. " + str(created) + " new lot(s) added."
        ))