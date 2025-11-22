#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Navigate to myproject directory
cd myproject

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Apply database migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build process completed successfully!"
