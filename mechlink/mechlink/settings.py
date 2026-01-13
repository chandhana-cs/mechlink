"""
Django settings for mechlink (RoadResQ) project.
"""

import os
from pathlib import Path

# -------------------------------------------
# BASE SETTINGS
# -------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-=@i%8vdlu1lrgj9@2#ssk4j032o6t-kd!0t-7^1-l8sael#m&#'
DEBUG = True
ALLOWED_HOSTS = []

# -------------------------------------------
# INSTALLED APPS
# -------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'users',
    'mechanics',
    'services',

]

# -------------------------------------------
# MIDDLEWARE
# -------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------------------
# URLS / WSGI
# -------------------------------------------
ROOT_URLCONF = 'mechlink.urls'
WSGI_APPLICATION = 'mechlink.wsgi.application'

# -------------------------------------------
# TEMPLATES
# -------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ✅ global templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # ✅ required for media files to display in templates
                'django.template.context_processors.media',
            ],
        },
    },
]

# -------------------------------------------
# DATABASE
# -------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# -------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# -------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------------------
# STATIC FILES
# -------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # for collectstatic (optional)

# -------------------------------------------
# MEDIA FILES (✅ This enables image upload and display)
# -------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# -------------------------------------------
# AUTH & LOGIN
# -------------------------------------------
AUTH_USER_MODEL = 'users.CustomUser'

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# -------------------------------------------
# CORS (optional)
# -------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True



RAZORPAY_KEY_ID = "rzp_test_ReHFbUdp0dFWeS"

RAZORPAY_KEY_SECRET = "I02E6H0OhOfDfg6JYl7VoQ46"