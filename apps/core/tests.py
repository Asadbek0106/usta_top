
from apps.accounts.models import User
from apps.arizalar.models import Ariza, Sharh
from apps.ustalar.models import Usta

from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.db.utils import OperationalError
from django.test import TestCase, override_settings


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