"""
Django settings for myproject (PARMS).
Production-ready configuration for Render + PostgreSQL.
"""

from pathlib import Path
import os
import dj_database_url
from decouple import config, Csv

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,172.20.10.4',
    cast=Csv(),
)


# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',          # required by allauth
    'params_app',
    'cloudinary',
    'cloudinary_storage',
    # ── Google OAuth (django-allauth) ──────────────────────────
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1


# ── Middleware ─────────────────────────────────────────────────────────────────
# WhiteNoise MUST be second — right after SecurityMiddleware — to serve static
# files before any other middleware touches the request.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',       # i18n — must be after SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',   # required by allauth ≥ 0.56
]


# ── URLs / WSGI ────────────────────────────────────────────────────────────────
ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'


# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ── Database ──────────────────────────────────────────────────────────────────
# Priority order:
#   1. DATABASE_URL env var  →  production (Render sets this automatically)
#   2. USE_SQLITE_FOR_TESTING=True  →  quick local dev without PostgreSQL
#   3. Individual DB_* vars  →  local PostgreSQL dev environment

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif config('USE_SQLITE_FOR_TESTING', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='parking_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }


# ── Password validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Auth ──────────────────────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
LOGIN_URL = '/login/'

# ── django-allauth ─────────────────────────────────────────────────────────────
ACCOUNT_LOGIN_METHODS         = {'email'}                         # allauth ≥ 0.60
ACCOUNT_SIGNUP_FIELDS         = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION    = 'none'    # skip email confirm (set 'mandatory' in prod)
LOGIN_REDIRECT_URL            = '/google-welcome/'   # custom post-OAuth handler
ACCOUNT_LOGOUT_REDIRECT_URL   = '/'
SOCIALACCOUNT_AUTO_SIGNUP     = True     # create account automatically on first Google login
SOCIALACCOUNT_LOGIN_ON_GET    = True     # skip the allauth "confirm" page

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id':     config('GOOGLE_CLIENT_ID',     default=''),
            'secret':        config('GOOGLE_CLIENT_SECRET', default=''),
            'key':           '',
        },
    }
}


# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en'
TIME_ZONE     = 'Africa/Kigali'   # UTC+2 — all template dates display in Kigali local time
USE_I18N      = True
USE_TZ        = True

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
    ('rw', 'Kinyarwanda'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']


# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Include the project-level static/ folder if it exists
_project_static = BASE_DIR / 'static'
if _project_static.exists():
    STATICFILES_DIRS = [_project_static]

# Development: plain storage (no hashing — instant CSS changes, no collectstatic needed)
# Production : compressed + hashed storage (cache-busting, Brotli/gzip compression)
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Media files (user uploads) ────────────────────────────────────────────────
# On Render the filesystem is ephemeral — uploads vanish on every deploy/restart.
# When CLOUDINARY_URL is set (Render env var), route all ImageField uploads to
# Cloudinary so photos survive redeploys.  Locally the env var is absent, so
# Django falls back to the normal MEDIA_ROOT filesystem (no Cloudinary account needed).
CLOUDINARY_URL = config('CLOUDINARY_URL', default='')

if CLOUDINARY_URL:
    import cloudinary
    _parts = CLOUDINARY_URL.replace('cloudinary://', '').split('@')
    _creds, _cloud = _parts[0].split(':'), _parts[1]
    cloudinary.config(
        cloud_name=_cloud,
        api_key=_creds[0],
        api_secret=_creds[1],
        secure=True,
    )
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'   # kept for URL compatibility
else:
    MEDIA_URL  = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


# ── Security (production only) ────────────────────────────────────────────────
# Render sits behind an HTTPS reverse proxy. These settings are required for
# HTTPS to work correctly without causing redirect loops.
if not DEBUG:
    # Tell Django the request came in over HTTPS via Render's proxy header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Redirect all HTTP → HTTPS
    SECURE_SSL_REDIRECT = True

    # Cookies only sent over HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS: tell browsers to always use HTTPS for 1 year
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CSRF: Django 4.0+ requires trusted origins for cross-origin POST requests.
# Add your Render URL here — comma-separated if you have multiple domains.
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv(),
)


# ── Misc ──────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── Email (SMTP) ───────────────────────────────────────────────────────────────
# For Gmail: enable 2-Step Verification, then create an App Password at
# myaccount.google.com/apppasswords and set EMAIL_HOST_PASSWORD in .env
EMAIL_BACKEND   = config('EMAIL_BACKEND',   default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST      = config('EMAIL_HOST',      default='smtp.gmail.com')
EMAIL_PORT      = config('EMAIL_PORT',      default=587, cast=int)
EMAIL_USE_TLS   = config('EMAIL_USE_TLS',   default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='PARMS Smart Parking <noreply@parms.rw>')

# ── Session auto-close ─────────────────────────────────────────────────────────
PARKING_SESSION_MAX_HOURS = 24   # tickets older than this are auto-closed
