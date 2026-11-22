import os
from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.db.utils import OperationalError
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.arizalar.models import Ariza, Sharh
from apps.ustalar.models import Usta

from .testing import foydalanuvchi_yarat


class DemoDataTest(TestCase):
    @override_settings(DEBUG=True)
    def test_demo_malumotlar_yaratiladi(self):
        call_command('demo_data', stdout=StringIO())
        self.assertEqual(Usta.objects.count(), 10)
        self.assertEqual(User.objects.count(), 15)
        self.assertEqual(Ariza.objects.count(), 30)

    @override_settings(DEBUG=True)
    def test_qayta_ishga_tushirganda_dublikat_qilmaydi(self):
        call_command('demo_data', stdout=StringIO())
        sonlar = (User.objects.count(), Usta.objects.count(), Ariza.objects.count(), Sharh.objects.count())
        call_command('demo_data', stdout=StringIO())
        self.assertEqual(
            sonlar,
            (User.objects.count(), Usta.objects.count(), Ariza.objects.count(), Sharh.objects.count()),
        )

    @override_settings(DEBUG=False)
    def test_productionda_ishlamaydi(self):
        with self.assertRaises(CommandError):
            call_command('demo_data', stdout=StringIO())
        self.assertEqual(User.objects.count(), 0)

class HealthTest(TestCase):
    def test_hammasi_joyida(self):
        javob = self.client.get('/health/')
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.json(), {'status': 'ok', 'database': 'ok'})

    def test_baza_ishlamasa_503(self):
        with patch('apps.core.views.connection.cursor', side_effect=OperationalError):
            javob = self.client.get('/health/')
        self.assertEqual(javob.status_code, 503)


class EnsureSuperuserTest(TestCase):
    MUHIT = {'DJANGO_SUPERUSER_TELEFON': '+998 90 115 40 55', 'DJANGO_SUPERUSER_PASSWORD': 'Admin-Parol-2026'}

    def ishga_tushir(self, muhit=None):
        with patch.dict(os.environ, muhit if muhit is not None else self.MUHIT, clear=False):
            call_command('ensure_superuser', stdout=StringIO(), stderr=StringIO())

    def test_yangi_superuser_yaratiladi(self):
        self.ishga_tushir()
        user = User.objects.get(telefon='+998901154055')
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertTrue(user.check_password('Admin-Parol-2026'))

    def test_oddiy_foydalanuvchi_superuser_qilinadi(self):
        foydalanuvchi_yarat('+998901154055')
        self.ishga_tushir()
        user = User.objects.get(telefon='+998901154055')
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertTrue(user.check_password('Admin-Parol-2026'))

    def test_mavjud_superuser_paroli_ozgarmaydi(self):
        User.objects.create_superuser('+998901154055', 'Admin-Panelda-Ozgargan-1')
        self.ishga_tushir()
        self.assertTrue(User.objects.get().check_password('Admin-Panelda-Ozgargan-1'))

    def test_ozgaruvchilarsiz_hech_narsa_qilmaydi(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DJANGO_SUPERUSER_TELEFON', None)
            os.environ.pop('DJANGO_SUPERUSER_PASSWORD', None)
            call_command('ensure_superuser', stdout=StringIO())
        self.assertFalse(User.objects.exists())

    def test_notogri_telefon_xato_bermaydi(self):
        self.ishga_tushir({'DJANGO_SUPERUSER_TELEFON': '12345', 'DJANGO_SUPERUSER_PASSWORD': 'x'})
        self.assertFalse(User.objects.exists())
