from .base import *  # noqa
from .base import BASE_DIR, env

DEBUG = False

STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- Xavfsizlik ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# --- Email (SMTP) ---
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': env('EMAIL_HOST', default='localhost'),
            'port': env.int('EMAIL_PORT', default=587),
            'username': env('EMAIL_HOST_USER', default=''),
            'password': env('EMAIL_HOST_PASSWORD', default=''),
            'use_tls': env.bool('EMAIL_USE_TLS', default=True),
        },
    },
}
