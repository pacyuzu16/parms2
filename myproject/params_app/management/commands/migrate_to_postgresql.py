"""
Django management command to set up PostgreSQL database.
Usage: python manage.py setup_postgresql
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Set up PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all migrations and create fresh ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up PostgreSQL database...')
        )
        
        # Check if we're using PostgreSQL
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.ERROR(
                    'Error: Database is not configured for PostgreSQL. '
                    'Please update your settings.py and .env file.'
                )
            )
            return
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS('✓ PostgreSQL connection successful!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Database connection failed: {e}')
            )
            self.stdout.write(
                self.style.WARNING(
                    'Please ensure:\n'
                    '1. PostgreSQL is running\n'
                    '2. Database exists\n'
                    '3. Credentials in .env are correct'
                )
            )
            return

        if options['reset']:
            self.stdout.write('Resetting migrations...')
            
            # Remove migration files (except __init__.py)
            migrations_dir = os.path.join('params_app', 'migrations')
            if os.path.exists(migrations_dir):
                for filename in os.listdir(migrations_dir):
                    if filename.startswith('0') and filename.endswith('.py'):
                        file_path = os.path.join(migrations_dir, filename)
                        os.remove(file_path)
                        self.stdout.write(f'Removed {filename}')

        # Create migrations
        self.stdout.write('Creating migrations...')
        call_command('makemigrations', 'params_app', verbosity=1)
        
        # Apply migrations
        self.stdout.write('Applying migrations...')
        call_command('migrate', verbosity=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ PostgreSQL setup completed successfully!\n'
                'Next steps:\n'
                '1. Create a superuser: python manage.py createsuperuser\n'
                '2. Start the server: python manage.py runserver'
            )
        )
