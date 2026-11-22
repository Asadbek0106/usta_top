import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.telegram import bot_api, update_ni_qayta_ishla

# Telegram yangi xabar bo'lmasa javobni shuncha soniya ushlab turadi (long polling)
POLLING_VAQTI = 25

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Botni lokal kompyuterda ishga tushiradi (polling): webhook va ochiq HTTPS manzil kerak emas. "
        "Serverda (Render) bot webhook orqali ishlaydi, bu buyruq faqat ishlab chiqish uchun."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhookni-ochir', action='store_true',
            help="Bot serverga ulangan bo'lsa ham webhook'ni o'chirib, lokalda ishlatish",
        )

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError(".env faylida TELEGRAM_BOT_TOKEN berilmagan")

        malumot = bot_api('getWebhookInfo')
        if malumot is None or not malumot.get('ok'):
            raise CommandError("Telegram'ga ulanib bo'lmadi: token va internetni tekshiring")

        # Telegram bitta bot uchun yo webhook, yo polling'ga ruxsat beradi — ikkalasiga bir vaqtda emas
        webhook = malumot['result'].get('url')
        if webhook:
            if not options['webhookni_ochir']:
                raise CommandError(
                    f"Bu bot serverga ulangan ({webhook}).\n"
                    "Lokal ishlash uchun BotFather'da alohida test bot yarating va uning tokenini .env'ga yozing.\n"
                    "Yoki --webhookni-ochir bilan ishga tushiring (keyin server botni qayta ulashi uchun "
                    "Render'da Manual Deploy qilish kerak bo'ladi)."
                )
            bot_api('deleteWebhook')
            self.stdout.write(self.style.WARNING(f"Webhook o'chirildi: {webhook}"))

        self.stdout.write(self.style.SUCCESS("Bot ishga tushdi. To'xtatish uchun Ctrl+C."))
        offset = None
        try:
            while True:
                javob = bot_api(
                    'getUpdates', kutish=POLLING_VAQTI + 10,
                    offset=offset, timeout=POLLING_VAQTI, allowed_updates=['message'],
                )
                if not javob or not javob.get('ok'):
                    time.sleep(3)  # internet uzilgan bo'lsa, birozdan keyin qayta urinadi
                    continue
                for update in javob['result']:
                    offset = update['update_id'] + 1
                    try:
                        update_ni_qayta_ishla(update)
                    except Exception:  # bitta xato xabar botni to'xtatib qo'ymasin
                        logger.exception('Update %s qayta ishlanmadi', update['update_id'])
        except KeyboardInterrupt:
            self.stdout.write("\nBot to'xtatildi.")
