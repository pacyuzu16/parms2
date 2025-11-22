#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r myproject/requirements.txt

# Navigate to myproject directory
cd myproject

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
