"""Telegram Bot API bilan ishlash: xabar yuborish, webhook o'rnatish va botning javob mantig'i.

Tashqi kutubxona ishlatilmaydi: Bot API oddiy HTTPS + JSON, standart urllib yetarli.
"""
import hashlib
import json
import logging
import re
import secrets
import urllib.error
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import TelefonTasdiq, User

logger = logging.getLogger(__name__)


API = 'https://api.telegram.org/bot{token}/{metod}'
WEBHOOK_YOLI = '/api/v1/auth/telegram/webhook/'

# Bitta Telegram akkaunt 10 daqiqada shundan ortiq kod so'ray olmaydi (spamdan himoya)
CHAT_UCHUN_KOD_CHEGARASI = 3


def webhook_maxfiy_kalit():
    """Telegram har bir webhook so'roviga shu kalitni sarlavhada qo'shib yuboradi.

    Kalit SECRET_KEY'dan hosil qilinadi, shuning uchun alohida o'zgaruvchi kerak emas.
    Begona odam webhook manziliga soxta "kontakt" yuborib, kod olib qo'ya olmaydi.
    """
    return hashlib.sha256(f'telegram-webhook:{settings.SECRET_KEY}'.encode()).hexdigest()


def bot_api(metod, kutish=10, **parametrlar):
    """Bot API metodini chaqiradi. Xato bo'lsa None qaytaradi (bot xatosi saytni yiqitmasligi kerak).

    kutish — javobni necha soniya kutish (polling'da getUpdates uzoqroq kutadi).
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    url = API.format(token=settings.TELEGRAM_BOT_TOKEN, metod=metod)
    sorov = urllib.request.Request(
        url,
        data=json.dumps(parametrlar).encode(),
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(sorov, timeout=kutish) as javob:
            return json.load(javob)
    except urllib.error.HTTPError as xato:
        # Telegram xatoni ham JSON'da qaytaradi ({"ok": false, "description": "Unauthorized"})
        try:
            javob = json.load(xato)
        except ValueError:
            javob = {'ok': False, 'description': f'HTTP {xato.code}'}
        logger.warning('Telegram %s bajarilmadi: %s', metod, javob.get('description'))
        return javob
    except (urllib.error.URLError, TimeoutError, ValueError) as xato:
        # Tokenni logga yozib yubormaslik uchun faqat metod nomi va xato turi yoziladi
        logger.warning('Telegram %s bajarilmadi: %s', metod, type(xato).__name__)
        return None


def xabar_yubor(chat_id, matn, klaviatura=None):
    parametrlar = {'chat_id': chat_id, 'text': matn, 'parse_mode': 'HTML'}
    if klaviatura is not None:
        parametrlar['reply_markup'] = klaviatura
    return bot_api('sendMessage', **parametrlar)


KONTAKT_KLAVIATURASI = {
    'keyboard': [[{'text': '📱 Raqamni yuborish', 'request_contact': True}]],
    'resize_keyboard': True,
    'one_time_keyboard': True,
}
KLAVIATURANI_OLIB_TASHLA = {'remove_keyboard': True}


def telefonni_tozala(raqam):
    """Telegram raqamni '998901234567' yoki '+998901234567' ko'rinishida beradi — bitta formatga keltiramiz."""
    return '+' + re.sub(r'\D', '', raqam or '')


def yangi_kod():
    return f'{secrets.randbelow(10**6):06d}'


def update_ni_qayta_ishla(update):
    """Telegram yuborgan bitta update'ga javob beradi."""
    xabar = update.get('message')
    if not xabar:
        return
    chat_id = xabar['chat']['id']
    kontakt = xabar.get('contact')

    if not kontakt:
        xabar_yubor(
            chat_id,
            "Assalomu alaykum! Bu bot <b>Usta</b> saytida telefon raqamingizni tasdiqlaydi: ro'yxatdan "
            "o'tish yoki unutilgan parolni tiklash uchun.\n\nPastdagi <b>📱 Raqamni yuborish</b> tugmasini "
            "bosing — bot sizga 6 xonali kod beradi.",
            KONTAKT_KLAVIATURASI,
        )
        return

    # Boshqa odamning kontaktini ulashib, uning raqamiga kod olib bo'lmaydi
    if kontakt.get('user_id') != xabar.get('from', {}).get('id'):
        xabar_yubor(chat_id, "Faqat <b>o'z</b> raqamingizni yuboring: pastdagi tugmani bosing.", KONTAKT_KLAVIATURASI)
        return

    telefon = telefonni_tozala(kontakt.get('phone_number'))
    if not re.fullmatch(r'\+998\d{9}', telefon):
        xabar_yubor(chat_id, "Kechirasiz, hozircha faqat O'zbekiston raqamlari (+998) qabul qilinadi.",
                    KLAVIATURANI_OLIB_TASHLA)
        return

    # Raqam ro'yxatdan o'tgan bo'lsa, kod parolni tiklash uchun beriladi
    maqsad = (
        TelefonTasdiq.Maqsad.TIKLASH
        if User.objects.filter(telefon=telefon, is_active=True).exists()
        else TelefonTasdiq.Maqsad.ROYXAT
    )

    oxirgi_10_daqiqa = timezone.now() - timedelta(minutes=10)
    yaqindagi_kodlar = TelefonTasdiq.objects.filter(chat_id=chat_id, yaratilgan__gte=oxirgi_10_daqiqa).count()
    if yaqindagi_kodlar >= CHAT_UCHUN_KOD_CHEGARASI:
        xabar_yubor(chat_id, "Kod juda ko'p so'raldi. 10 daqiqadan keyin qaytadan urinib ko'ring.",
                    KLAVIATURANI_OLIB_TASHLA)
        return

    # Shu raqamning eski kodlari bekor bo'ladi — faqat eng oxirgisi ishlaydi
    TelefonTasdiq.objects.filter(telefon=telefon, ishlatilgan=False).update(ishlatilgan=True)
    tasdiq = TelefonTasdiq.objects.create(telefon=telefon, kod=yangi_kod(), chat_id=chat_id, maqsad=maqsad)
    daqiqa = int(settings.TASDIQ_KOD_MUDDATI.total_seconds() // 60)
    if maqsad == TelefonTasdiq.Maqsad.TIKLASH:
        matn = (
            f"{telefon} raqami saytda ro'yxatdan o'tgan.\n\n"
            f"Parolni tiklash kodi: <code>{tasdiq.kod}</code>\n\n"
            f"Uni saytdagi <b>Parolni tiklash</b> sahifasiga kiriting. Kod {daqiqa} daqiqa amal qiladi.\n"
            "Agar parolni tiklamoqchi bo'lmasangiz, bu xabarga e'tibor bermang.\n\nKodni hech kimga bermang."
        )
    else:
        matn = (
            f"Tasdiqlash kodingiz: <code>{tasdiq.kod}</code>\n\n"
            f"Uni saytdagi ro'yxatdan o'tish formasiga kiriting. Kod {daqiqa} daqiqa amal qiladi.\n"
            f"Telefon raqam: <b>{telefon}</b>\n\nKodni hech kimga bermang."
        )
    xabar_yubor(chat_id, matn, KLAVIATURANI_OLIB_TASHLA)
