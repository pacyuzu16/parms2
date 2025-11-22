# Parking Management System

A Django-based parking management system with PostgreSQL database.

## Features

- User authentication (login/register)
- Parking lot management
- Vehicle registration
- Parking ticket generation with QR codes
- Payment processing
- Contact/feedback system
- PDF ticket downloads

## Quick Setup

### 1. Install PostgreSQL
Download from https://www.postgresql.org/download/

### 2. Create Database
```sql
psql -U postgres
CREATE DATABASE parking_db;
\q
```

### 3. Configure Environment
Update `.env` file with your PostgreSQL credentials:
```
DB_NAME=parking_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 4. Install and Run
```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Production Deployment

Use `DATABASE_URL` for production platforms:
```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

## Troubleshooting

- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database `parking_db` exists
- Run `python manage.py check` to test configuration
