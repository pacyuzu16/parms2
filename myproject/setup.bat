@echo off
echo ===============================================
echo Parking Management System - PostgreSQL Setup
echo ===============================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking PostgreSQL connection...
python manage.py check

if %ERRORLEVEL% EQU 0 (
    echo.
    echo PostgreSQL connection successful!
    echo.
    echo Creating and applying migrations...
    python manage.py makemigrations
    python manage.py migrate
    
    echo.
    echo Setup completed! You can now:
    echo 1. Create a superuser: python manage.py createsuperuser
    echo 2. Start the server: python manage.py runserver
) else (
    echo.
    echo PostgreSQL connection failed!
    echo Please check your .env file and ensure PostgreSQL is running.
    echo.
    echo Make sure you have:
    echo 1. PostgreSQL installed and running
    echo 2. Created the database 'parking_db'
    echo 3. Updated .env file with correct credentials
)

echo.
pause
