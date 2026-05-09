from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('params_app', '0003_parkinglot_ml_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingticket',
            name='user',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tickets',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
