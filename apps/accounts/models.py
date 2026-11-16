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