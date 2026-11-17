"""Testlar uchun umumiy yordamchi funksiyalar (fabrikalar)."""
from decimal import Decimal

from django.core.cache import cache
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.arizalar.models import Ariza
from apps.ustalar.models import Kategoriya, Shahar, Usta, Xizmat

PAROL = 'Kuchli-Parol-77'


def foydalanuvchi_yarat(telefon, **kwargs):
    return User.objects.create_user(telefon, PAROL, **kwargs)


def usta_yarat(telefon, *, shahar, kategoriyalar, tasdiqlangan=True, narx=100000):
    user = foydalanuvchi_yarat(telefon, first_name='Usta')
    usta = Usta.objects.create(user=user, shahar=shahar, tasdiqlangan=tasdiqlangan)
    for kategoriya in kategoriyalar:
        Xizmat.objects.create(usta=usta, kategoriya=kategoriya, narx_dan=Decimal(narx))
    return usta


def ariza_yarat(*, mijoz, usta, kategoriya, status=Ariza.Status.YANGI):
    return Ariza.objects.create(
        mijoz=mijoz, usta=usta, kategoriya=kategoriya,
        tavsif='Kran oqyapti', manzil='Chilonzor', status=status,
    )


class BaseAPITestCase(APITestCase):
    """Har bir testda kerak bo'ladigan boshlang'ich ma'lumotlar."""

    def setUp(self):
        cache.clear()  # throttle hisoblagichi testlar orasida aralashmasin
        self.shahar = Shahar.objects.create(nomi='Toshkent')
        self.shahar2 = Shahar.objects.create(nomi='Samarqand')
        self.santexnik = Kategoriya.objects.create(nomi='Santexnik', slug='santexnik')
        self.elektrik = Kategoriya.objects.create(nomi='Elektrik', slug='elektrik')

        self.usta = usta_yarat('+998900000001', shahar=self.shahar, kategoriyalar=[self.santexnik])
        self.begona_usta = usta_yarat('+998900000002', shahar=self.shahar, kategoriyalar=[self.santexnik])
        self.mijoz = foydalanuvchi_yarat('+998910000001', first_name='Mijoz')
        self.begona_mijoz = foydalanuvchi_yarat('+998910000002')

    def kirish(self, user):
        self.client.force_authenticate(user)
