from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.arizalar.models import Ariza, Sharh
from apps.ustalar.models import Usta


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
