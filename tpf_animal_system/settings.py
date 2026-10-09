import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration comes from environment variables so the same code runs locally and in production.
# Local development needs nothing set. For production set at least:
#   TPF_DEBUG=0   TPF_SECRET_KEY=<long random string>   TPF_ALLOWED_HOSTS=animals.example.go.tz
def _env_bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


DEBUG = _env_bool('TPF_DEBUG', True)

_DEV_SECRET_KEY = 'django-insecure-71)*!4ndu$!+3f4#i%55fnr$t)6e@cl0f@-pteo=o8w+qr$=a9'
SECRET_KEY = os.environ.get('TPF_SECRET_KEY') or (_DEV_SECRET_KEY if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError('Set TPF_SECRET_KEY when TPF_DEBUG is off (generate one with '
                       '`python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`).')

_hosts = [h.strip() for h in os.environ.get('TPF_ALLOWED_HOSTS', '').split(',') if h.strip()]
ALLOWED_HOSTS = _hosts or (['*'] if DEBUG else [])
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('TPF_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

if not DEBUG:
    # Behind HTTPS: cookies only over TLS, HSTS, and trust the proxy's X-Forwarded-Proto header if one is used.
    SECURE_SSL_REDIRECT = _env_bool('TPF_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('TPF_HSTS_SECONDS', 31536000))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    if _env_bool('TPF_BEHIND_PROXY', False):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',


    # Tailwind CSS
    'tailwind',
    'theme',
    'widget_tweaks',

    # Custom apps
    'accounts',
    'core',
    'admin_dashboard',
    'veterinarian_dashboard',
    'user_dashboard',
    'superadmin_dashboard',
    'staff_dashboard',
    'task_management',
]

# Tailwind config
TAILWIND_APP_NAME = 'theme'

INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MIDDLEWARE += [
    'horse.middleware.message_handling.MessageErrorMiddleware',
]

ROOT_URLCONF = 'tpf_animal_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.unread_notifications',
                'core.context_processors.role_base',
            ],
        },
    },
]

WSGI_APPLICATION = 'tpf_animal_system.wsgi.application'


# Database (using SQLite for now)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Dar_es_Salaam'  # EAT (UTC+3); data is stored in UTC (USE_TZ)

USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # `manage.py collectstatic` target; serve via the web server

# and your static files are collected into STATICFILES_DIRS or STATIC_ROOT


STATICFILES_DIRS = [
    # This matches your actual directory structure: horse/horse/core/static/
    os.path.join(BASE_DIR, 'horse', 'core', 'static'),
    # Add theme static files if they exist
    os.path.join(BASE_DIR, 'theme', 'static'),
]

# Default primary key type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = '/login/'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# <-- this is your image folder

# Message configuration
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'