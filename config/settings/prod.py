from .base import *  # noqa
from .base import MIDDLEWARE, env

DEBUG = False

# --- Statik fayllar (WhiteNoise) ---
# Development'da statik fayllarni runserver o'zi beradi. Production'da esa gunicorn buni qilmaydi,
# shuning uchun WhiteNoise middleware'i qo'shiladi (SecurityMiddleware'dan keyin turishi shart).
MIDDLEWARE.insert(MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
                  'whitenoise.middleware.WhiteNoiseMiddleware')

# Fayl nomiga hash qo'shiladi (style.css → style.4f2a1b.css) va gzip/brotli bilan siqiladi.
# Shunda brauzer faylni uzoq muddat keshlaydi, fayl o'zgarsa nomi ham o'zgaradi.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# --- Xavfsizlik ---
# Serverda HTTPS odatda reverse proxy'da (nginx, Traefik) tugaydi va Django'ga oddiy HTTP keladi.
# Proxy "asl so'rov HTTPS edi" degan sarlavhani qo'shadi, Django unga ishonadi.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Docker'da lokal sinov uchun HTTPS=False qilinadi, haqiqiy serverda True qoladi.
HTTPS = env.bool('HTTPS', default=True)
SECURE_SSL_REDIRECT = HTTPS
# Docker healthcheck container ichidan oddiy HTTP orqali so'raydi, uni HTTPS'ga yo'naltirmaymiz
SECURE_REDIRECT_EXEMPT = [r'^health/$']
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30 if HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = HTTPS
SECURE_CONTENT_TYPE_NOSNIFF = True

# --- Loglar ---
# Container'da loglar faylga emas, stdout'ga yoziladi: `docker compose logs` ularni ko'rsatadi.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'oddiy': {'format': '{asctime} {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'oddiy'},
    },
    'root': {'handlers': ['console'], 'level': env('LOG_LEVEL', default='INFO')},
}

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
