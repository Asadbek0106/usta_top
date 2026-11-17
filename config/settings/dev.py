from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Xatlar terminalga chiqariladi, haqiqatan yuborilmaydi
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
