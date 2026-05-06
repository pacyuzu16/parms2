#!/usr/bin/env bash
# Render build script for PARMS Django application
# Runs during every deploy: install → static → migrate
set -o errexit

echo "==> [1/3] Installing Python dependencies..."
pip install -r requirements.txt

# Move into the Django project directory
cd myproject

echo "==> [2/3] Collecting static files..."
python manage.py collectstatic --no-input

echo "==> [3/3] Applying database migrations..."
python manage.py migrate --no-input

echo "==> Build complete."
