#!/usr/bin/env python3
"""
Debug script to test database connection and environment variables
Run this to diagnose database connection issues
"""

import os
import sys
from pathlib import Path

# Add the Django project to Python path
project_root = Path(__file__).resolve().parent / 'myproject'
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection
from decouple import config

print("=== Database Connection Debug ===")
print(f"Django Version: {django.get_version()}")
print(f"Python Version: {sys.version}")
print()

print("=== Environment Variables ===")
print(f"DATABASE_URL: {'SET' if config('DATABASE_URL', default=None) else 'NOT SET'}")
print(f"DEBUG: {config('DEBUG', default=True, cast=bool)}")
print(f"SECRET_KEY: {'SET' if config('SECRET_KEY', default=None) else 'NOT SET'}")
print()

print("=== Database Configuration ===")
db_config = settings.DATABASES['default']
print(f"Engine: {db_config.get('ENGINE', 'Not set')}")
print(f"Name: {db_config.get('NAME', 'Not set')}")
print(f"Host: {db_config.get('HOST', 'Not set')}")
print(f"Port: {db_config.get('PORT', 'Not set')}")
print(f"User: {db_config.get('USER', 'Not set')}")
print()

print("=== Testing Database Connection ===")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("✅ Database connection successful!")
    print(f"Result: {result}")
except Exception as e:
    print("❌ Database connection failed!")
    print(f"Error: {e}")
    print()
    print("Possible solutions:")
    print("1. Check if PostgreSQL is running (local development)")
    print("2. Verify DATABASE_URL is set correctly (production)")
    print("3. Check database credentials")
    print("4. Ensure database exists")
