import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "DJANGO_SUPERUSER_TELEFON va DJANGO_SUPERUSER_PASSWORD berilgan bo'lsa, superuser yaratadi. "
        "Bunday foydalanuvchi allaqachon bo'lsa, hech narsa qilmaydi. "
        "Shell'siz serverlarda (Render bepul tarifi) admin akkaunt ochish uchun ishlatiladi."
    )

    def handle(self, *args, **options):
        telefon = os.environ.get('DJANGO_SUPERUSER_TELEFON', '').strip()
        parol = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not telefon or not parol:
            self.stdout.write("ensure_superuser: o'zgaruvchilar berilmagan, o'tkazib yuborildi")
            return

        User = get_user_model()
        if User.objects.filter(telefon=User.objects.normalize_telefon(telefon)).exists():
            self.stdout.write(f'ensure_superuser: {telefon} allaqachon mavjud')
            return

        try:
            User.objects.create_superuser(telefon, parol)
        except (ValidationError, ValueError) as xato:
            # Noto'g'ri telefon formati butun saytni ishdan chiqarmasligi kerak — faqat logga yozamiz
            self.stderr.write(f'ensure_superuser: yaratib bo\'lmadi — {xato}')
            return
        self.stdout.write(self.style.SUCCESS(f'ensure_superuser: {telefon} superuser yaratildi'))
