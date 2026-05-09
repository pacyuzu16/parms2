from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("params_app", "0002_contactmessage"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ParkingLot new fields
        migrations.AddField(model_name="parkinglot", name="latitude",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="parkinglot", name="longitude",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="parkinglot", name="hourly_rate",
            field=models.DecimalField(decimal_places=2, default=5.0, max_digits=6)),
        migrations.AddField(model_name="parkinglot", name="description",
            field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="parkinglot", name="features",
            field=models.CharField(blank=True, default="", max_length=500)),
        migrations.AddField(model_name="parkinglot", name="is_active",
            field=models.BooleanField(default=True)),

        # ParkingDetectionEvent
        migrations.CreateModel(
            name="ParkingDetectionEvent",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("event_type", models.CharField(choices=[("entry", "Entry"), ("exit", "Exit")], max_length=10)),
                ("plate_number", models.CharField(blank=True, default="", max_length=20)),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                ("confidence", models.FloatField(default=1.0)),
                ("source", models.CharField(choices=[("camera", "Camera"), ("sensor", "Sensor"), ("manual", "Manual"), ("api", "API")], default="manual", max_length=20)),
                ("processed", models.BooleanField(default=False)),
                ("lot", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detection_events", to="params_app.parkinglot")),
                ("space", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="params_app.parkingspace")),
            ],
        ),

        # UserNotification
        migrations.CreateModel(
            name="UserNotification",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("notif_type", models.CharField(choices=[("space_available", "Space Available"), ("nearly_full", "Nearly Full"), ("expiry_warning", "Expiry Warning"), ("session_ended", "Session Ended"), ("system", "System")], default="system", max_length=30)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("lot", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="params_app.parkinglot")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parking_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
