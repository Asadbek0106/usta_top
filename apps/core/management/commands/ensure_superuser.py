import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "DJANGO_SUPERUSER_TELEFON va DJANGO_SUPERUSER_PASSWORD berilgan bo'lsa, admin akkauntni tayyorlaydi. "
        "Shell'siz serverlarda (Render bepul tarifi) admin akkaunt ochish uchun ishlatiladi."
    )

    def handle(self, *args, **options):
        telefon = os.environ.get('DJANGO_SUPERUSER_TELEFON', '').strip()
        parol = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not telefon or not parol:
            self.stdout.write("ensure_superuser: o'zgaruvchilar berilmagan, o'tkazib yuborildi")
            return

        User = get_user_model()
        telefon = User.objects.normalize_telefon(telefon)
        user = User.objects.filter(telefon=telefon).first()

        if user is None:
            try:
                User.objects.create_superuser(telefon, parol)
            except (ValidationError, ValueError) as xato:
                # Noto'g'ri telefon formati butun saytni ishdan chiqarmasligi kerak — faqat logga yozamiz
                self.stderr.write(f"ensure_superuser: yaratib bo'lmadi — {xato}")
                return
            self.stdout.write(self.style.SUCCESS(f'ensure_superuser: {telefon} superuser yaratildi'))
            return

        if user.is_superuser and user.is_staff:
            # Allaqachon admin: parolga tegmaymiz (admin panelda almashtirilgan bo'lishi mumkin)
            self.stdout.write(f'ensure_superuser: {telefon} allaqachon superuser')
            return

        # Raqam saytda oddiy foydalanuvchi sifatida ro'yxatdan o'tgan: unga admin huquqi beramiz.
        # Parol Environment'dagiga almashtiriladi — admin panelga shu ma'lumot bilan kiriladi.
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(parol)
        user.save(update_fields=['is_staff', 'is_superuser', 'is_active', 'password'])
        self.stdout.write(self.style.SUCCESS(f'ensure_superuser: {telefon} superuser qilindi (mavjud akkaunt)'))
