from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('params_app', '0005_userprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add direct user FK to Vehicle
        migrations.AddField(
            model_name='vehicle',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehicles',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Track which plate is currently in each space
        migrations.AddField(
            model_name='parkingspace',
            name='occupied_by_plate',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
