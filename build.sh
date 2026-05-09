#!/usr/bin/env bash
# Render build script for PARMS Django application
set -o errexit

echo "==> [1/4] Installing Python dependencies..."
pip install -r requirements.txt

cd myproject

echo "==> [2/4] Collecting static files..."
python manage.py collectstatic --no-input

echo "==> [3/4] Applying database migrations..."
python manage.py migrate --no-input

echo "==> [4/5] Creating superuser (skips if already exists)..."
python create_superuser.py

echo "==> [5/5] Seeding parking lot data (skips existing)..."
python manage.py seed_data

echo "==> Build complete."
