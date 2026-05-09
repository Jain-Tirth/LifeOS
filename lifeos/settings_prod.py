"""
Production settings for LifeOS.
Use: export DJANGO_SETTINGS_MODULE=lifeos.settings_prod
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in production")

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database: PostgreSQL only
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'lifeos_prod'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': True,  # Each request is a transaction
        'OPTIONS': {
            'sslmode': 'require' if os.getenv('DB_SSL', 'true') == 'true' else 'prefer',
            'connect_timeout': 10,
        }
    }
}

# Read replica for scaling (optional)
if os.getenv('DB_REPLICA_HOST'):
    DATABASES['replica'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_REPLICA_USER', 'readonly'),
        'PASSWORD': os.getenv('DB_REPLICA_PASSWORD'),
        'HOST': os.getenv('DB_REPLICA_HOST'),
        'PORT': os.getenv('DB_REPLICA_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        }
    }
    DATABASE_ROUTERS = ['lifeos.routers.PrimaryReplicaRouter']

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        }
    }
}

# Session + CSRF
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security headers
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'"),
    "style-src": ("'self'", "'unsafe-inline'"),
}

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

CSRF_TRUSTED_ORIGINS = [
    os.getenv('FRONTEND_URL', 'http://localhost:5173'),
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttles.AgentMessageThrottle',
        'api.throttles.AgentSessionThrottle',
        'api.throttles.BurstThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'agent_message': '10/min',
        'agent_session': '5/hour',
        'burst': '10/s',
    },
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}


# Import from base settings
import importlib
import sys
base_settings = importlib.import_module('lifeos.settings')
for attr in dir(base_settings):
    if attr.isupper() and attr not in locals():
        locals()[attr] = getattr(base_settings, attr)

# Modify MIDDLEWARE
if 'lifeos.middleware.CorrelationIdMiddleware' not in MIDDLEWARE:
    MIDDLEWARE = ['lifeos.middleware.CorrelationIdMiddleware'] + MIDDLEWARE

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'lifeos.logging_config.JsonFormatter',
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['stdout'],
            'level': 'INFO',
        },
        'agents': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
        },
    },
}
