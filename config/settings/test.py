"""Testlar uchun sozlamalar: tez va tashqi muhitga bog'liq emas."""
import os

# CI serverida (GitHub Actions va h.k.) .env fayli bo'lmaydi. base.py esa SECRET_KEY'ni majburiy talab qiladi,
# shuning uchun testlar uchun vaqtinchalik kalit beriladi (SECRET_KEY muhitda berilgan bo'lsa, o'shasi olinadi).
os.environ.setdefault('SECRET_KEY', 'faqat-testlar-uchun-maxfiy-kalit-0123456789abcdef')

from .base import *  # noqa: E402,F403

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

# Testlar haqiqiy Telegram'ga murojaat qilmasligi kerak (.env'da token bo'lsa ham).
# Bot bilan bog'liq testlar bu sozlamalarni override_settings orqali o'zi yoqadi.
TELEGRAM_BOT_TOKEN = ''
TELEGRAM_BOT_USERNAME = ''
TELEFON_TASDIQLASH = False
