#!/usr/bin/env python3
"""
Database setup script for PARMS project
This script helps set up the PostgreSQL database for local development
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from decouple import config

# Database configuration
DB_NAME = config('DB_NAME', default='parking_db')
DB_USER = config('DB_USER', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')

def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PostgreSQL is installed: {result.stdout.strip()}")
            return True
        else:
            print("✗ PostgreSQL is not accessible via command line")
            return False
    except FileNotFoundError:
        print("✗ PostgreSQL is not installed or not in PATH")
        return False

def create_database():
    """Create the PostgreSQL database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"✓ Database '{DB_NAME}' created successfully")
        else:
            print(f"✓ Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def test_connection():
    """Test connection to the created database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print(f"✓ Successfully connected to {DB_NAME}")
        print(f"  PostgreSQL version: {version}")
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error connecting to database: {e}")
        return False

def run_django_migrations():
    """Run Django migrations"""
    try:
        print("\nRunning Django migrations...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✓ Django migrations completed successfully")
            return True
        else:
            print("✗ Django migrations failed")
            return False
            
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return False

def main():
    print("PARMS Database Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        print("⚠ Warning: No .env file found. Using default values.")
        print("  Create a .env file based on .env.example for custom configuration.")
        print()
    
    # Step 1: Check PostgreSQL installation
    print("1. Checking PostgreSQL installation...")
    if not check_postgresql_installed():
        print("\nPlease install PostgreSQL and ensure it's in your PATH")
        print("Download from: https://www.postgresql.org/download/")
        return False
    
    # Step 2: Create database
    print(f"\n2. Creating database '{DB_NAME}'...")
    if not create_database():
        return False
    
    # Step 3: Test connection
    print(f"\n3. Testing database connection...")
    if not test_connection():
        return False
    
    # Step 4: Run Django migrations
    print(f"\n4. Running Django migrations...")
    if not run_django_migrations():
        return False
    
    print("\n" + "=" * 50)
    print("✓ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python manage.py createsuperuser (if needed)")
    print("2. Run: python manage.py runserver")
    print("3. Your app should now use PostgreSQL!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)