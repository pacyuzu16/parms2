#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Debug: Show environment variables
echo "Environment check:"
echo "DATABASE_URL is set: ${DATABASE_URL:+yes}"
echo "DATABASE_URL length: ${#DATABASE_URL}"
echo "DEBUG: $DEBUG"
echo "RENDER: ${RENDER:-not set}"
echo "RENDER_SERVICE_ID: ${RENDER_SERVICE_ID:-not set}"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Navigate to myproject directory
cd myproject

# Test database connection
echo "Testing database connection..."
python manage.py check --database default

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Apply database migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build process completed successfully!"
