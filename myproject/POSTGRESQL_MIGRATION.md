# PostgreSQL Migration Guide

This document explains how to migrate your PARMS Django application from SQLite to PostgreSQL for production deployment on Render.

## Overview

SQLite is not suitable for production environments, especially on platforms like Render where the filesystem is ephemeral. PostgreSQL is a robust, production-ready database that's recommended for Django applications.

## What Changed

### 1. Dependencies Updated

Added PostgreSQL-related packages to `requirements.txt`:
- `psycopg2-binary==2.9.11` - PostgreSQL adapter for Python
- `dj-database-url==2.1.0` - Database URL parsing for production
- `python-decouple==3.8` - Environment variable management

### 2. Database Configuration

Updated `settings.py` to:
- Use `DATABASE_URL` environment variable for production (provided by Render)
- Fall back to local PostgreSQL configuration for development
- Removed SQLite fallback to prevent production issues

### 3. Render Configuration

Updated `render.yaml` to:
- Define a PostgreSQL database service
- Automatically inject `DATABASE_URL` from the database service
- Removed the `USE_SQLITE_FOR_TESTING` environment variable

### 4. Build Process

Updated `build.sh` to:
- Install dependencies from the root `requirements.txt`
- Add better logging for the build process

## Local Development Setup

### Prerequisites

1. Install PostgreSQL on your local machine:
   - Windows: Download from https://www.postgresql.org/download/windows/
   - macOS: `brew install postgresql`
   - Ubuntu: `sudo apt-get install postgresql postgresql-contrib`

2. Ensure PostgreSQL service is running

### Setup Steps

1. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local database credentials.

2. **Run the setup script**:
   
   **Windows**:
   ```cmd
   setup_local.bat
   ```
   
   **Linux/macOS**:
   ```bash
   cd myproject
   python setup_database.py
   ```

3. **Start the development server**:
   ```bash
   cd myproject
   python manage.py runserver
   ```

## Production Deployment on Render

### Automatic Setup

When you push to your Git repository connected to Render:

1. Render will create a PostgreSQL database automatically
2. The `DATABASE_URL` will be injected into your application
3. Migrations will run automatically during the build process

### Manual Steps (if needed)

1. **Create a new Render service**:
   - Connect your Git repository
   - Use the existing `render.yaml` configuration

2. **Database will be created automatically** based on the `render.yaml` configuration

3. **Environment variables** are automatically set by Render

## Database Migration Commands

If you need to run database operations manually:

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (if you have fixtures)
python manage.py loaddata fixtures/sample_data.json
```

## Troubleshooting

### Local Development Issues

1. **Connection refused error**:
   - Ensure PostgreSQL is running: `sudo service postgresql start` (Linux) or start via Services (Windows)
   - Check your database credentials in `.env`

2. **Database doesn't exist**:
   ```bash
   createdb parking_db
   ```

3. **Permission denied**:
   - Make sure your PostgreSQL user has the right permissions
   - You might need to create a user: `createuser -s your_username`

### Production Issues

1. **Check Render logs** for database connection issues
2. **Verify environment variables** are set correctly in Render dashboard
3. **Database migrations** should run automatically, but can be run manually via Render shell

## Key Benefits of PostgreSQL

1. **Production Ready**: Designed for high-concurrency, multi-user environments
2. **Data Persistence**: Data survives application restarts and redeployments
3. **Better Performance**: Superior query optimization and indexing
4. **Advanced Features**: Support for JSON, full-text search, and complex queries
5. **Backup & Recovery**: Render provides automatic backups
6. **Scalability**: Can handle much larger datasets than SQLite

## File Structure Changes

```
myproject/
├── .env.example          # Environment variables template
├── setup_local.bat       # Windows setup script
├── setup_database.py     # PostgreSQL setup script
├── myproject/
│   └── settings.py       # Updated database configuration
├── requirements.txt      # Updated with PostgreSQL dependencies
├── render.yaml          # Updated Render configuration
└── build.sh             # Updated build script
```

## Next Steps

1. Test your application locally with PostgreSQL
2. Deploy to Render and verify the production setup
3. Consider setting up database backups (Render provides this automatically)
4. Monitor your application performance

Your PARMS application is now properly configured for production with PostgreSQL!