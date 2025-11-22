#!/usr/bin/env python
"""
PostgreSQL setup script for the Parking Management System
"""

import os
import sys
import subprocess

def run_command(command, description="Running command"):
    """Run a shell command and return success status."""
    print(f"{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("Parking Management System - PostgreSQL Setup")
    print("=" * 60)
    print()
    
    if not os.path.exists('manage.py'):
        print("✗ Error: This script must be run from the Django project root directory")
        print("  (The directory containing manage.py)")
        sys.exit(1)
    
    print("PostgreSQL Setup Checklist:")
    print("1. PostgreSQL is installed and running")
    print("2. Database 'parking_db' is created")
    print("3. Database credentials are set in .env file")
    print()
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("✗ Failed to install dependencies. Please check your pip installation.")
        sys.exit(1)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("✗ .env file not found!")
        print("Please create .env file with your database credentials.")
        print("Use .env.example as a template.")
        sys.exit(1)
    
    # Check Django configuration
    if not run_command("python manage.py check", "Checking Django configuration"):
        print("✗ Django configuration check failed.")
        print("Please check your .env file and PostgreSQL connection.")
        sys.exit(1)
    
    # Create and run migrations
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        print("✗ Failed to create migrations.")
        sys.exit(1)
    
    if not run_command("python manage.py migrate", "Applying migrations"):
        print("✗ Failed to apply migrations.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🎉 POSTGRESQL SETUP COMPLETED!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Start the development server: python manage.py runserver")
    print("3. Open your browser to: http://127.0.0.1:8000")
    print()
    
    create_superuser = input("Would you like to create a superuser now? (y/n): ").lower() == 'y'
    if create_superuser:
        run_command("python manage.py createsuperuser", "Creating superuser")
    
    print()
    print("Setup complete! You can now run: python manage.py runserver")

if __name__ == "__main__":
    main()
