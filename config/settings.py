import os
from pathlib import Path
from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = Path(__file__).resolve().parent.parent

_is_render = bool(os.getenv('RENDER')) or bool(os.getenv('RENDER_SERVICE_ID'))
if not _is_render:
    load_dotenv(BASE_DIR / '.env')

# ---------------------------------------------------------------------
# Compatibility patch: Django 4.2 + Python 3.14 template context copying
# ---------------------------------------------------------------------
try:
    from django.template.context import BaseContext

    def _basecontext_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        if hasattr(self, "__dict__"):
            duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _basecontext_copy  # type: ignore[attr-defined]
except Exception:
    pass

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-temp-key')

DEBUG = str(os.getenv('DEBUG', 'False')).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

ALLOWED_HOSTS = [
    'priyankasuperbazaar.com',
    'www.priyankasuperbazaar.com',
    'priyanka-superbazaar.onrender.com',
    'localhost',
    '127.0.0.1',
]

_allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if _allowed_hosts_env:
    ALLOWED_HOSTS += [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    'store.apps.StoreConfig',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'cloudinary',
    'cloudinary_storage',
    
    # API and Real-time
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'channels',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.catalog',
                'store.context_processors.seo_defaults',
            ],
        },
    },
]

import dj_database_url

# -----------------------------------------
# DATABASE CONFIG (Render-safe version)
# -----------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# Local dev convenience:
# If you have DATABASE_URL set globally (e.g. Render Postgres), Django will try to use it.
# Default to sqlite locally unless explicitly opting into remote DB.
USE_REMOTE_DB = str(os.getenv('USE_REMOTE_DB', 'False')).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}
FORCE_SQLITE = str(os.getenv('FORCE_SQLITE', 'False')).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

# If running on Render, NEVER fall back to sqlite
if os.getenv("RENDER"):
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is missing in Render environment!")

_db_url = DATABASE_URL
if not os.getenv("RENDER"):
    # Local machine only (developer fallback)
    if FORCE_SQLITE or (not _db_url) or (not USE_REMOTE_DB):
        _db_url = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"

DATABASES = {
    "default": dj_database_url.parse(
        _db_url,
        conn_max_age=60,
        ssl_require=str(_db_url).startswith("postgresql"),
    )
}

# Ensure Postgres always uses sslmode=require (especially on Render managed Postgres)
try:
    if DATABASES['default']['ENGINE'].endswith('postgresql'):
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default'].setdefault('CONN_HEALTH_CHECKS', True)
        DATABASES['default']['OPTIONS'].setdefault('sslmode', 'require')
        DATABASES['default']['OPTIONS'].setdefault('connect_timeout', 10)
        DATABASES['default']['OPTIONS'].setdefault('keepalives', 1)
        DATABASES['default']['OPTIONS'].setdefault('keepalives_idle', 30)
        DATABASES['default']['OPTIONS'].setdefault('keepalives_interval', 10)
        DATABASES['default']['OPTIONS'].setdefault('keepalives_count', 5)
except Exception:
    pass

AUTHENTICATION_BACKENDS = [
    'store.utils.EmailOrUsernameModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

SITE_ID = 1

# ---------------------------------------------------------------------
# SEO Configuration
# ---------------------------------------------------------------------
SITE_NAME = 'Priyanka Super Bazaar'
# Full canonical base URL – used by sitemaps, canonical tags, and JSON-LD.
# Sitemap hostname is derived from this (must not be example.com).
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'https://priyankasuperbazaar.com').rstrip('/')

# Google Analytics 4 – set GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX in environment
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')

# Google Search Console – set GOOGLE_SITE_VERIFICATION to the meta tag content value
GOOGLE_SITE_VERIFICATION = os.getenv('GOOGLE_SITE_VERIFICATION', '')

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
if not CLOUDINARY_URL:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if cloud_name and api_key and api_secret:
        CLOUDINARY_URL = f"cloudinary://{api_key}:{api_secret}@{cloud_name}"

cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_URL:
    os.environ["CLOUDINARY_URL"] = CLOUDINARY_URL

if cloud_name and api_key and api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
else:
    cloudinary.config(secure=True)

CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': CLOUDINARY_URL,
}

# -------------------------------
# Cloudinary Storage Setup
# -------------------------------
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

if CLOUDINARY_URL:
    STORAGES = {
        'default': {
            'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }

LOGIN_REDIRECT_URL = '/account/profile/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CSRF_TRUSTED_ORIGINS = [
    "https://priyanka-superbazaar.onrender.com",
    "https://priyankasuperbazaar.com",
    "https://www.priyankasuperbazaar.com",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings for Flutter app
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://priyanka-superbazaar.onrender.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]

CORS_ALLOW_CREDENTIALS = True

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# Channels configuration for real-time features
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.getenv('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

