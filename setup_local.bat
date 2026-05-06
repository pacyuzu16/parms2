@echo off
REM Local Development Setup Script for PARMS
REM This script helps set up the project for local development with PostgreSQL

echo ========================================
echo PARMS Local Development Setup
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy ".env.example" ".env"
    echo ⚠ Please edit .env file with your database credentials
    echo.
)

REM Navigate to project directory
cd myproject

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
echo.

REM Setup PostgreSQL database
echo Setting up PostgreSQL database...
python setup_database.py
echo.

REM Create superuser (optional)
echo.
set /p create_superuser="Do you want to create a Django superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo To start the development server:
echo   cd myproject
echo   python manage.py runserver
echo.
echo Your Django app is now configured to use PostgreSQL!
echo.

pause
