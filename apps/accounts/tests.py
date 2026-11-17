from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.core.testing import PAROL, foydalanuvchi_yarat

from .forms import UserCreateForm
from .models import User

REGISTER = '/api/v1/auth/register/'
LOGIN = '/api/v1/auth/login/'
REFRESH = '/api/v1/auth/refresh/'
LOGOUT = '/api/v1/auth/logout/'
ME = '/api/v1/auth/me/'


class UserManagerTest(TestCase):
    def test_telefon_tozalanadi(self):
        self.assertEqual(User.objects.normalize_telefon('+998 90 123-45-67'), '+998901234567')

    def test_telefonsiz_foydalanuvchi_yaratilmaydi(self):
        with self.assertRaises(ValueError):
            User.objects.create_user('', PAROL)

    def test_oddiy_foydalanuvchi_admin_emas(self):
        user = foydalanuvchi_yarat('+998901234567')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(PAROL))

    def test_superuser(self):
        user = User.objects.create_superuser('+998901234567', PAROL)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_str_ism_yoki_telefon(self):
        self.assertEqual(str(foydalanuvchi_yarat('+998901111111')), '+998901111111')
        self.assertEqual(str(foydalanuvchi_yarat('+998902222222', first_name='Ali')), 'Ali')


class AdminFormTest(TestCase):
    def test_admin_formasi_telefonni_tozalaydi(self):
        form = UserCreateForm(data={
            'telefon': '+998 90 123-45-67',
            'usable_password': 'true',
            'password1': PAROL,
            'password2': PAROL,
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['telefon'], '+998901234567')


class RegisterTest(APITestCase):
    def setUp(self):
        cache.clear()

    def royxat(self, **maydonlar):
        data = {'telefon': '+998901234567', 'password': PAROL, 'password2': PAROL, **maydonlar}
        return self.client.post(REGISTER, data, format='json')

    def test_muvaffaqiyatli_royxatdan_otish(self):
        javob = self.royxat(telefon='+998 90 123-45-67', first_name='Ali')
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data['user']['telefon'], '+998901234567')
        self.assertIn('access', javob.data['tokens'])
        self.assertIn('refresh', javob.data['tokens'])

    def test_notogri_telefon(self):
        javob = self.royxat(telefon='901234')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('telefon', javob.data)

    def test_takroriy_telefon(self):
        foydalanuvchi_yarat('+998901234567')
        javob = self.royxat()
        self.assertEqual(javob.status_code, 400)
        self.assertIn('telefon', javob.data)

    def test_parollar_mos_emas(self):
        javob = self.royxat(password2='Boshqa-Parol-88')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('password2', javob.data)

    def test_kuchsiz_parol(self):
        javob = self.royxat(password='12345', password2='12345')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('password', javob.data)

    def test_royxatdan_otishda_admin_bolib_bolmaydi(self):
        javob = self.royxat(is_staff=True, is_superuser=True)
        self.assertEqual(javob.status_code, 201)
        user = User.objects.get(telefon='+998901234567')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class LoginTest(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = foydalanuvchi_yarat('+998901234567')

    def test_togri_malumot_bilan_kirish(self):
        javob = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': PAROL}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertIn('access', javob.data)

    def test_boshliq_va_chiziqchali_telefon_bilan_kirish(self):
        javob = self.client.post(LOGIN, {'telefon': '+998 90 123-45-67', 'password': PAROL}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)

    def test_notogri_parol(self):
        javob = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': 'xato'}, format='json')
        self.assertEqual(javob.status_code, 401)

    def test_kop_urinishdan_keyin_bloklanadi(self):
        for _ in range(5):
            self.client.post(LOGIN, {'telefon': '+998901234567', 'password': 'xato'}, format='json')
        javob = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': PAROL}, format='json')
        self.assertEqual(javob.status_code, 429)

    def test_logoutdan_keyin_refresh_token_ishlamaydi(self):
        tokenlar = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': PAROL}, format='json').data
        javob = self.client.post(LOGOUT, {'refresh': tokenlar['refresh']}, format='json')
        self.assertEqual(javob.status_code, 200)
        javob = self.client.post(REFRESH, {'refresh': tokenlar['refresh']}, format='json')
        self.assertEqual(javob.status_code, 401)


class MeTest(APITestCase):
    def setUp(self):
        self.user = foydalanuvchi_yarat('+998901234567')

    def test_mehmon_kirolmaydi(self):
        self.assertEqual(self.client.get(ME).status_code, 401)

    def test_jwt_bilan_profilni_korish(self):
        cache.clear()
        token = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': PAROL}, format='json').data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        javob = self.client.get(ME)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data['telefon'], '+998901234567')
        self.assertFalse(javob.data['usta_mi'])

    def test_profilni_tahrirlash_telefon_ozgarmaydi(self):
        self.client.force_authenticate(self.user)
        javob = self.client.patch(ME, {'first_name': 'Vali', 'telefon': '+998999999999'}, format='json')
        self.assertEqual(javob.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Vali')
        self.assertEqual(self.user.telefon, '+998901234567')
