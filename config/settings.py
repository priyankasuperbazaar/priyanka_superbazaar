"""
Django settings for Priyanka Superbazaar project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------
# SECURITY
# ---------------------------
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-temp-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------------------------
# APPS
# ---------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'store.apps.StoreConfig',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Cloudinary
    'cloudinary',
    'cloudinary_storage',
]

# ---------------------------
# MIDDLEWARE
# ---------------------------
MIDDLEWARE = [
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

# ---------------------------
# URL & WSGI
# ---------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------
# TEMPLATES
# ---------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.catalog',
            ],
        },
    },
]

# ---------------------------
# DATABASE
# ---------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------
# AUTHENTICATION
# ---------------------------
AUTHENTICATION_BACKENDS = [
    'store.utils.EmailOrUsernameModelBackend',  # Custom backend for email/username login
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',  # Default backend as fallback
]

SITE_ID = int(os.getenv('SITE_ID', '1'))

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_AUTHENTICATION_METHOD = os.getenv('ACCOUNT_AUTHENTICATION_METHOD', 'username_email')
ACCOUNT_USERNAME_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------
# TIME + LANGUAGE
# ---------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ---------------------------
# STATIC & MEDIA (Cloudinary)
# ---------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'

# ---------------------------
# CLOUDINARY CONFIG
# ---------------------------
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_URL").split("@")[-1],
    api_key=os.getenv("CLOUDINARY_URL").split("//")[1].split(":")[0],
    api_secret=os.getenv("CLOUDINARY_URL").split(":")[2].split("@")[0],
)

# ---------------------------
# LOGIN
# ---------------------------
LOGIN_REDIRECT_URL = '/account/profile/'

# ---------------------------
# EMAIL
# ---------------------------
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@priyankasuperbazaar.com')

# ---------------------------
# SMS (Optional)
# ---------------------------
SMS_API_URL = os.getenv('SMS_API_URL', '')
SMS_API_KEY = os.getenv('SMS_API_KEY', '')

# ---------------------------
# STRIPE
# ---------------------------
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# ---------------------------
# CKEDITOR
# ---------------------------
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Outdent', 'Indent'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source']
        ]
    }
}

# ---------------------------
# SESSIONS
# ---------------------------
CART_SESSION_ID = 'cart'
WISHLIST_SESSION_ID = 'wishlist'

# ---------------------------
# SECURITY FOR PRODUCTION
# ---------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://priyanka-superbazaar.onrender.com'
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
