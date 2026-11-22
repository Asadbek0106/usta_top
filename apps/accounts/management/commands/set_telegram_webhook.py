from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.telegram import WEBHOOK_YOLI, bot_api, webhook_maxfiy_kalit


class Command(BaseCommand):
    help = (
        "Telegram'ga bot xabarlarini qaysi manzilga yuborishni aytadi (setWebhook). "
        "Server har ishga tushganda chaqiriladi; token yoki domen bo'lmasa, hech narsa qilmaydi."
    )

    def add_arguments(self, parser):
        parser.add_argument('--domen', help="Sayt domeni (default: RENDER_EXTERNAL_HOSTNAME)")

    def handle(self, *args, **options):
        domen = options['domen'] or getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', '')
        if not settings.TELEGRAM_BOT_TOKEN or not domen:
            self.stdout.write("set_telegram_webhook: token yoki domen berilmagan, o'tkazib yuborildi")
            return

        url = f'https://{domen}{WEBHOOK_YOLI}'
        javob = bot_api(
            'setWebhook',
            url=url,
            secret_token=webhook_maxfiy_kalit(),
            allowed_updates=['message'],
        )
        if javob and javob.get('ok'):
            self.stdout.write(self.style.SUCCESS(f'set_telegram_webhook: {url}'))
        else:
            # Server baribir ishga tushishi kerak: bot ishlamasa ham sayt ishlayveradi
            tavsif = (javob or {}).get('description', "Telegram'ga ulanib bo'lmadi")
            self.stderr.write(f"set_telegram_webhook: o'rnatilmadi — {tavsif}")
