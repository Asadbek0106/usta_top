from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .managers import UserManager

telefon_validator = RegexValidator(
    regex=r'^\+998\d{9}$',
    message="Telefon +998XXXXXXXXX formatida bo'lishi kerak",
)


class User(AbstractUser):
    username = None
    telefon = models.CharField(
        "Telefon raqam",
        max_length=13,
        unique=True,
        validators=[telefon_validator],
    )

    USERNAME_FIELD = 'telefon'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.get_full_name() or self.telefon


class TelefonTasdiq(models.Model):
    """Telegram bot bergan bir martalik kod: foydalanuvchi raqam haqiqatan uniki ekanini shu bilan isbotlaydi.

    Bot foydalanuvchidan Telegram kontaktini oladi (Telegram raqamni o'zi tasdiqlagan bo'ladi),
    shu raqam uchun kod yaratadi. Saytda ro'yxatdan o'tishda kod tekshiriladi.
    """

    telefon = models.CharField("Telefon raqam", max_length=13, db_index=True)
    kod = models.CharField("Kod", max_length=6)
    chat_id = models.BigIntegerField("Telegram chat ID")
    urinishlar = models.PositiveSmallIntegerField("Noto'g'ri urinishlar", default=0)
    ishlatilgan = models.BooleanField("Ishlatilgan", default=False)
    yaratilgan = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Telefon tasdiqlash kodi"
        verbose_name_plural = "Telefon tasdiqlash kodlari"
        ordering = ('-yaratilgan',)

    def __str__(self):
        return f'{self.telefon} ({self.yaratilgan:%d.%m %H:%M})'
