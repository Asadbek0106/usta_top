from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.core.testing import PAROL, foydalanuvchi_yarat

from .forms import UserCreateForm
from .models import TelefonTasdiq, User
from .telegram import update_ni_qayta_ishla, webhook_maxfiy_kalit

REGISTER = '/api/v1/auth/register/'
LOGIN = '/api/v1/auth/login/'
REFRESH = '/api/v1/auth/refresh/'
LOGOUT = '/api/v1/auth/logout/'
ME = '/api/v1/auth/me/'
TELEGRAM = '/api/v1/auth/telegram/'
TIKLASH = '/api/v1/auth/parol-tiklash/'
WEBHOOK = '/api/v1/auth/telegram/webhook/'


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

    def test_admin_formasida_ism_familiya_saqlanadi(self):
        form = UserCreateForm(data={
            'telefon': '+998901234567',
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'usable_password': 'true',
            'password1': PAROL,
            'password2': PAROL,
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual((user.first_name, user.last_name), ('Ali', 'Valiyev'))
        self.assertTrue(user.check_password(PAROL))


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


def kontakt_update(telefon, *, user_id=111, from_id=111, chat_id=111):
    return {
        'update_id': 1,
        'message': {
            'message_id': 1,
            'chat': {'id': chat_id, 'type': 'private'},
            'from': {'id': from_id, 'is_bot': False, 'first_name': 'Ali'},
            'contact': {'phone_number': telefon, 'first_name': 'Ali', 'user_id': user_id},
        },
    }


@override_settings(TELEFON_TASDIQLASH=True, TELEGRAM_BOT_TOKEN='test-token', TELEGRAM_BOT_USERNAME='usta_test_bot')
@patch('apps.accounts.telegram.xabar_yubor')
class TelegramTasdiqlashTest(APITestCase):
    def setUp(self):
        cache.clear()

    def webhook(self, update, kalit=None):
        return self.client.post(
            WEBHOOK, update, format='json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=webhook_maxfiy_kalit() if kalit is None else kalit,
        )

    def royxat(self, kod, telefon='+998901234567'):
        data = {'telefon': telefon, 'first_name': 'Ali', 'password': PAROL, 'password2': PAROL, 'kod': kod}
        return self.client.post(REGISTER, data, format='json')

    def test_sozlama_frontendga_bot_havolasini_beradi(self, xabar_yubor):
        javob = self.client.get(TELEGRAM)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data, {
            'tasdiqlash_kerak': True, 'bot': 'usta_test_bot', 'havola': 'https://t.me/usta_test_bot',
        })

    def test_start_bosilganda_kontakt_tugmasi_yuboriladi(self, xabar_yubor):
        update = {'update_id': 1, 'message': {'chat': {'id': 5}, 'from': {'id': 5}, 'text': '/start'}}
        self.assertEqual(self.webhook(update).status_code, 200)
        klaviatura = xabar_yubor.call_args.args[2]
        self.assertTrue(klaviatura['keyboard'][0][0]['request_contact'])
        self.assertFalse(TelefonTasdiq.objects.exists())

    def test_kontakt_yuborilsa_kod_yaratiladi_va_yuboriladi(self, xabar_yubor):
        self.assertEqual(self.webhook(kontakt_update('998901234567')).status_code, 200)
        tasdiq = TelefonTasdiq.objects.get()
        self.assertEqual(tasdiq.telefon, '+998901234567')
        self.assertRegex(tasdiq.kod, r'^\d{6}$')
        self.assertIn(tasdiq.kod, xabar_yubor.call_args.args[1])

    def test_kod_bilan_royxatdan_otish(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        tasdiq = TelefonTasdiq.objects.get()
        javob = self.royxat(tasdiq.kod)
        self.assertEqual(javob.status_code, 201, javob.data)
        tasdiq.refresh_from_db()
        self.assertTrue(tasdiq.ishlatilgan)

    def test_kodsiz_royxatdan_otib_bolmaydi(self, xabar_yubor):
        javob = self.royxat('')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kod', javob.data)
        self.assertFalse(User.objects.exists())

    def test_notogri_kod(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        tasdiq = TelefonTasdiq.objects.get()
        notogri = '000000' if tasdiq.kod != '000000' else '111111'
        javob = self.royxat(notogri)
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kod', javob.data)
        tasdiq.refresh_from_db()
        self.assertEqual(tasdiq.urinishlar, 1)

    def test_boshqa_raqamning_kodi_ishlamaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        kod = TelefonTasdiq.objects.get().kod
        javob = self.royxat(kod, telefon='+998907654321')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kod', javob.data)

    def test_eskirgan_kod_ishlamaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        tasdiq = TelefonTasdiq.objects.get()
        TelefonTasdiq.objects.filter(pk=tasdiq.pk).update(yaratilgan=timezone.now() - timedelta(minutes=11))
        self.assertEqual(self.royxat(tasdiq.kod).status_code, 400)

    def test_urinishlar_tugasa_togri_kod_ham_ishlamaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        tasdiq = TelefonTasdiq.objects.get()
        TelefonTasdiq.objects.filter(pk=tasdiq.pk).update(urinishlar=5)
        self.assertEqual(self.royxat(tasdiq.kod).status_code, 400)

    def test_kod_ikki_marta_ishlatilmaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        kod = TelefonTasdiq.objects.get().kod
        self.assertEqual(self.royxat(kod).status_code, 201)
        User.objects.all().delete()
        self.assertEqual(self.royxat(kod).status_code, 400)

    def test_yangi_kod_eskisini_bekor_qiladi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567'))
        eski = TelefonTasdiq.objects.get().kod
        self.webhook(kontakt_update('+998901234567'))
        yangi = TelefonTasdiq.objects.filter(ishlatilgan=False).get().kod
        if eski != yangi:
            self.assertEqual(self.royxat(eski).status_code, 400)
        self.assertEqual(self.royxat(yangi).status_code, 201)

    def test_begona_kontakt_uchun_kod_berilmaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+998901234567', user_id=999, from_id=111))
        self.assertFalse(TelefonTasdiq.objects.exists())

    def test_chet_el_raqami_qabul_qilinmaydi(self, xabar_yubor):
        self.webhook(kontakt_update('+79161234567'))
        self.assertFalse(TelefonTasdiq.objects.exists())

    def test_royxatdan_otgan_raqamga_tiklash_kodi_beriladi(self, xabar_yubor):
        foydalanuvchi_yarat('+998901234567')
        self.webhook(kontakt_update('+998901234567'))
        tasdiq = TelefonTasdiq.objects.get()
        self.assertEqual(tasdiq.maqsad, TelefonTasdiq.Maqsad.TIKLASH)
        self.assertIn('Parolni tiklash', xabar_yubor.call_args.args[1])
        # Tiklash kodi bilan shu raqamga ikkinchi akkaunt ochib bo'lmaydi
        User.objects.all().delete()
        self.assertEqual(self.royxat(tasdiq.kod).status_code, 400)

    def test_bitta_chatdan_kod_soni_cheklangan(self, xabar_yubor):
        for i in range(5):
            self.webhook(kontakt_update(f'+99890123456{i}'))
        self.assertEqual(TelefonTasdiq.objects.count(), 3)

    def test_maxfiy_kalitsiz_webhook_rad_etiladi(self, xabar_yubor):
        javob = self.webhook(kontakt_update('+998901234567'), kalit='soxta')
        self.assertEqual(javob.status_code, 403)
        self.assertFalse(TelefonTasdiq.objects.exists())

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_bot_sozlanmagan_bolsa_webhook_ishlamaydi(self, xabar_yubor):
        self.assertEqual(self.webhook(kontakt_update('+998901234567')).status_code, 404)


class TasdiqlashOchiqTest(APITestCase):
    """Bot sozlanmagan bo'lsa (lokal ishlab chiqish) ro'yxatdan o'tish avvalgidek kodsiz ishlaydi."""

    def test_sozlama(self):
        javob = self.client.get(TELEGRAM)
        self.assertEqual(javob.data, {'tasdiqlash_kerak': False, 'bot': None, 'havola': None})


@override_settings(TELEFON_TASDIQLASH=True, TELEGRAM_BOT_TOKEN='test-token')
class TelegramPollingTest(TestCase):
    """Lokal ishlab chiqish uchun polling buyrug'i."""

    def test_polling_xabarni_qayta_ishlaydi(self):
        javoblar = {
            'getWebhookInfo': [{'ok': True, 'result': {'url': ''}}],
            'getUpdates': [{'ok': True, 'result': [kontakt_update('+998901234567')]}],
        }

        def soxta_api(metod, kutish=10, **parametrlar):
            if metod == 'sendMessage':
                return {'ok': True}
            if not javoblar[metod]:
                raise KeyboardInterrupt  # ikkinchi getUpdates'da Ctrl+C bosilgandek to'xtaymiz
            return javoblar[metod].pop(0)

        with patch('apps.accounts.management.commands.telegram_polling.bot_api', soxta_api), \
                patch('apps.accounts.telegram.bot_api', soxta_api):
            call_command('telegram_polling')
        self.assertEqual(TelefonTasdiq.objects.get().telefon, '+998901234567')

    def test_serverga_ulangan_botni_tasodifan_uzib_qoymaydi(self):
        javob = {'ok': True, 'result': {'url': 'https://usta-api.onrender.com/api/v1/auth/telegram/webhook/'}}
        with patch('apps.accounts.management.commands.telegram_polling.bot_api', return_value=javob) as api:
            with self.assertRaises(CommandError):
                call_command('telegram_polling')
        metodlar = [chaqiruv.args[0] for chaqiruv in api.call_args_list]
        self.assertNotIn('deleteWebhook', metodlar)


YANGI_PAROL = 'Yangi-Parol-2026'


@override_settings(TELEGRAM_BOT_TOKEN='test-token', TELEGRAM_BOT_USERNAME='usta_test_bot')
@patch('apps.accounts.telegram.xabar_yubor')
class ParolTiklashTest(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = foydalanuvchi_yarat('+998901234567')

    def kod_ol(self, telefon='+998901234567'):
        update_ni_qayta_ishla(kontakt_update(telefon))
        return TelefonTasdiq.objects.filter(telefon=telefon, ishlatilgan=False).latest('yaratilgan').kod

    def tikla(self, kod, telefon='+998901234567', parol=YANGI_PAROL, parol2=None):
        data = {'telefon': telefon, 'kod': kod, 'password': parol, 'password2': parol2 or parol}
        return self.client.post(TIKLASH, data, format='json')

    def test_kod_bilan_parol_yangilanadi(self, xabar_yubor):
        javob = self.tikla(self.kod_ol(), telefon='+998 90 123-45-67')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(YANGI_PAROL))
        self.assertFalse(self.user.check_password(PAROL))
        self.assertTrue(TelefonTasdiq.objects.get().ishlatilgan)

    def test_eski_sessiyalar_yopiladi(self, xabar_yubor):
        kirish = self.client.post(LOGIN, {'telefon': '+998901234567', 'password': PAROL}, format='json')
        refresh = kirish.data['refresh']
        self.assertEqual(self.tikla(self.kod_ol()).status_code, 200)
        self.assertEqual(self.client.post(REFRESH, {'refresh': refresh}, format='json').status_code, 401)

    def test_notogri_kod(self, xabar_yubor):
        kod = self.kod_ol()
        javob = self.tikla('000000' if kod != '000000' else '111111')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kod', javob.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PAROL))

    def test_royxatdan_otish_kodi_bilan_parol_tiklanmaydi(self, xabar_yubor):
        # Kod yangi raqamga (ro'yxat uchun) berilgan, keyin shu raqam bilan akkaunt paydo bo'lgan
        kod = self.kod_ol('+998907777777')
        foydalanuvchi_yarat('+998907777777')
        self.assertEqual(self.tikla(kod, telefon='+998907777777').status_code, 400)

    def test_kod_ikki_marta_ishlatilmaydi(self, xabar_yubor):
        kod = self.kod_ol()
        self.assertEqual(self.tikla(kod).status_code, 200)
        self.assertEqual(self.tikla(kod, parol='Boshqa-Parol-99').status_code, 400)

    def test_kuchsiz_parol_va_mos_kelmagan_parollar(self, xabar_yubor):
        kod = self.kod_ol()
        self.assertIn('password', self.tikla(kod, parol='12345678').data)
        self.assertIn('password2', self.tikla(kod, parol2='Boshqa-Parol-99').data)

    def test_royxatdan_otmagan_raqam(self, xabar_yubor):
        javob = self.tikla('123456', telefon='+998909999999')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kod', javob.data)

    def test_bloklangan_foydalanuvchiga_tiklash_kodi_berilmaydi(self, xabar_yubor):
        self.user.is_active = False
        self.user.save()
        update_ni_qayta_ishla(kontakt_update('+998901234567'))
        self.assertEqual(TelefonTasdiq.objects.get().maqsad, TelefonTasdiq.Maqsad.ROYXAT)

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_bot_sozlanmagan_bolsa_ishlamaydi(self, xabar_yubor):
        self.assertEqual(self.tikla('123456').status_code, 503)
