"""
Django settings for blockproof_backend project.
Optimized for cost-effective blockchain integration.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Security
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG = env('DEBUG', default=False)

# Allow common dev hosts (incl. Django test client "testserver") even if ALLOWED_HOSTS
# isn't set in the environment. Keep env override for production safety.
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
if DEBUG:
    ALLOWED_HOSTS = list({
        *ALLOWED_HOSTS,
        '0.0.0.0',
        'testserver',
        'localhost',
        '127.0.0.1',
    })

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'blockchain',
    'credentials',
    'institutions',
    'zkproof',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'institutions.middleware.RequestLoggingMiddleware',  # Add request logging
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'blockproof_backend.urls'

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

WSGI_APPLICATION = 'blockproof_backend.wsgi.application'

# Database - Use PostgreSQL for production, SQLite for development
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR}/db.sqlite3'
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (for diploma uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Default to allow any, override per-view
    ],
    'URL_FORMAT_OVERRIDE': None,  # Disable format suffixes to prevent converter conflicts
}

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:8080',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
    'http://127.0.0.1:8080',
])
# Allow all origins in development (DEBUG mode)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-CSRFToken', 'Accept']

# Blockchain Configuration - COST OPTIMIZATION SETTINGS
BLOCKCHAIN_CONFIG = {
    # Use L2 or testnet to minimize costs
    'RPC_URL': env('RPC_URL', default='https://sepolia.infura.io/v3/YOUR_KEY'),
    'CONTRACT_ADDRESS': env('CONTRACT_ADDRESS', default=''),
    'PRIVATE_KEY': env('PRIVATE_KEY', default=''),  # For write operations only
    'CHAIN_ID': env.int('CHAIN_ID', default=11155111),  # Sepolia testnet
    
    # Cost optimization: Batch event indexing
    'EVENT_INDEXING_BATCH_SIZE': 1000,  # Process events in batches
    'EVENT_INDEXING_INTERVAL': 60,  # Index every 60 seconds (adjust based on usage)
    
    # Use free tier RPC providers
    'RPC_PROVIDER': env('RPC_PROVIDER', default='infura'),  # Options: infura, alchemy, public
    
    # Cache settings to minimize RPC calls
    'CACHE_BLOCKCHAIN_DATA': True,
    'CACHE_TTL': 300,  # 5 minutes cache for read operations
}

# Zero-Knowledge Proof Configuration
ZKPROOF_CONFIG = {
    'ZKPROOF_ENABLED': env.bool('ZKPROOF_ENABLED', default=True),
    'ZKPROOF_CIRCUIT_PATH': env('ZKPROOF_CIRCUIT_PATH', default=os.path.join(BASE_DIR, 'zkproof', 'circuits')),
    'ZKPROOF_ARTIFACTS_PATH': env('ZKPROOF_ARTIFACTS_PATH', default=os.path.join(BASE_DIR, 'zkproof', 'artifacts')),
    'ZKPROOF_IPFS_GATEWAY': env('ZKPROOF_IPFS_GATEWAY', default='https://ipfs.io/ipfs/'),
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'blockchain': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'zkproof': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'institutions': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'rest_framework.authentication': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.contrib.auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
