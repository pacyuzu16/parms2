#!/usr/bin/env python
"""
Switch between SQLite (testing) and PostgreSQL (production)
Usage: python switch_database.py [sqlite|postgresql]
"""

import sys
import os

def update_env_file(use_postgresql=True):
    """Update .env file to use PostgreSQL or SQLite"""
    
    if use_postgresql:
        env_content = """# Django Configuration
SECRET_KEY=django-insecure--2=%yzl50=$hgzm=c-&4pep!6%qkaz1637@th5q@35+&u=9mpb
DEBUG=True
ALLOWED_HOSTS=parms2.onrender.com,params-v2.onrender.com,127.0.0.1,localhost

# PostgreSQL Database Configuration
DB_NAME=parking_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432

# Set to False to use PostgreSQL
USE_SQLITE_FOR_TESTING=False

# Production Database URL (for deployment platforms like Render/Heroku)
# DATABASE_URL=postgresql://username:password@hostname:port/database_name
"""
    else:
        env_content = """# Django Configuration
SECRET_KEY=django-insecure--2=%yzl50=$hgzm=c-&4pep!6%qkaz1637@th5q@35+&u=9mpb
DEBUG=True
ALLOWED_HOSTS=parms2.onrender.com,params-v2.onrender.com,127.0.0.1,localhost

# PostgreSQL Database Configuration  
DB_NAME=parking_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432

# Set to True to use SQLite for testing
USE_SQLITE_FOR_TESTING=True

# Production Database URL (for deployment platforms like Render/Heroku)
# DATABASE_URL=postgresql://username:password@hostname:port/database_name
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    db_type = "PostgreSQL" if use_postgresql else "SQLite"
    print(f"✓ Updated .env to use {db_type}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python switch_database.py [sqlite|postgresql]")
        sys.exit(1)
    
    db_choice = sys.argv[1].lower()
    
    if db_choice == 'postgresql':
        update_env_file(use_postgresql=True)
        print("\n🔄 Switched to PostgreSQL")
        print("\nNext steps:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Create database: CREATE DATABASE parking_db;")
        print("3. Update DB_PASSWORD in .env file")
        print("4. Run: python manage.py migrate")
        print("5. Run: python manage.py populate_sample_data")
        
    elif db_choice == 'sqlite':
        update_env_file(use_postgresql=False)
        print("\n🔄 Switched to SQLite")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate")
        print("2. Run: python manage.py populate_sample_data")
        
    else:
        print("Invalid choice. Use 'sqlite' or 'postgresql'")
        sys.exit(1)

if __name__ == "__main__":
    main()
