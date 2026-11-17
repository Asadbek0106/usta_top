"""Testlar uchun sozlamalar: tez va tashqi muhitga bog'liq emas."""
from .base import *  # noqa

DEBUG = False

# Parolni hash qilish ataylab sekin (brute force'dan himoya). Testlarda bu kerak emas:
# MD5 bilan testlar bir necha barobar tezroq ishlaydi.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    },
}
