import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

if not username or not password:
    print('DJANGO_SUPERUSER_USERNAME / PASSWORD not set — skipping.')
elif User.objects.filter(username=username).exists():
    print('Superuser already exists: ' + username + ' — skipping.')
else:
    User.objects.create_superuser(username, email, password)
    print('Superuser created: ' + username)
