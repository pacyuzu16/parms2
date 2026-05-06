#!/usr/bin/env bash
# Render build script for PARMS Django application
# Runs during every deploy: install -> static -> migrate -> superuser
set -o errexit

echo "==> [1/4] Installing Python dependencies..."
pip install -r requirements.txt

# Move into the Django project directory
cd myproject

echo "==> [2/4] Collecting static files..."
python manage.py collectstatic --no-input

echo "==> [3/4] Applying database migrations..."
python manage.py migrate --no-input

echo "==> [4/4] Creating superuser (skips if already exists)..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
email    = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superuser created: {username}")
    else:
        print(f"Superuser already exists: {username} — skipping.")
else:
    print("DJANGO_SUPERUSER_USERNAME / PASSWORD not set — skipping superuser creation.")
"

echo "==> Build complete."
