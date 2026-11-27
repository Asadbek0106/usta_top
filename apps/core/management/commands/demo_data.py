import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.arizalar.models import Ariza, ArizaTarixi, Sharh
from apps.ustalar.models import Kategoriya, Shahar, Usta, Xizmat

SHAHARLAR = ['Toshkent', 'Samarqand', 'Buxoro', 'Andijon', 'Namangan']
KATEGORIYALAR = [
    ('Santexnik', 'santexnik'),
    ('Elektrik', 'elektrik'),
    ('Kafelchi', 'kafelchi'),
    ('Konditsioner ustasi', 'konditsioner'),
    ('Mebelchi', 'mebelchi'),
]
PAROL = 'Demo12345!'


class Command(BaseCommand):
    help = "Sinov uchun demo ma'lumotlar yaratadi (qayta ishga tushirsa ham dublikat qilmaydi)"

    def foydalanuvchi(self, telefon, ism):
        user = User.objects.filter(telefon=telefon).first()
        return user or User.objects.create_user(telefon, PAROL, first_name=ism)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("demo_data faqat DEBUG=True rejimida ishlaydi (production'da ishlatilmaydi).")
        self.yarat()

    @transaction.atomic
    def yarat(self):
        random.seed(42)

        shaharlar = [Shahar.objects.get_or_create(nomi=nomi)[0] for nomi in SHAHARLAR]
        kategoriyalar = [
            Kategoriya.objects.get_or_create(slug=slug, defaults={'nomi': nomi})[0]
            for nomi, slug in KATEGORIYALAR
        ]

        ustalar = []
        for i in range(1, 11):
            user = self.foydalanuvchi(f'+99890000{i:04d}', f'Usta {i}')
            usta, _ = Usta.objects.get_or_create(
                user=user,
                defaults={
                    'shahar': random.choice(shaharlar),
                    'tavsif': f"{i} yillik tajribaga ega usta",
                    'tasdiqlangan': i <= 8,
                },
            )
            for kategoriya in random.sample(kategoriyalar, 2):
                Xizmat.objects.get_or_create(
                    usta=usta,
                    kategoriya=kategoriya,
                    defaults={
                        'narx_dan': Decimal(random.randrange(50, 500) * 1000),
                        'tajriba': random.randint(1, 15),
                    },
                )
            ustalar.append(usta)

        mijozlar = [self.foydalanuvchi(f'+99891000{i:04d}', f'Mijoz {i}') for i in range(1, 6)]

        if not Ariza.objects.exists():
            tasdiqlangan_ustalar = [u for u in ustalar if u.tasdiqlangan]
            hozir = timezone.now()
            for _ in range(40):
                usta = random.choice(tasdiqlangan_ustalar)
                xizmat = random.choice(list(usta.xizmatlar.all()))
                status = random.choice(Ariza.Status.values)
                mijoz = random.choice(mijozlar)
                # Arizalar oxirgi ~6 oyga tarqatiladi: ustaning statistikasida oylar bo'yicha grafik chiqishi uchun
                yaratilgan = hozir - timedelta(days=random.randint(0, 170), hours=random.randint(0, 23))
                yangilangan = min(hozir, yaratilgan + timedelta(days=random.randint(1, 5)))
                narx = taklif = None
                if status in (Ariza.Status.NARX_TAKLIF, Ariza.Status.QABUL, Ariza.Status.BAJARILDI):
                    taklif = xizmat.narx_dan + Decimal(random.randrange(0, 20) * 10000)
                if status in (Ariza.Status.QABUL, Ariza.Status.BAJARILDI):
                    narx = taklif
                ariza = Ariza.objects.create(
                    mijoz=mijoz,
                    usta=usta,
                    kategoriya=xizmat.kategoriya,
                    tavsif="Uyda ta'mirlash ishi kerak",
                    manzil="Toshkent, Chilonzor tumani",
                    status=status,
                    taklif_narx=taklif,
                    kelishilgan_narx=narx,
                )
                Ariza.objects.filter(pk=ariza.pk).update(yaratilgan=yaratilgan, yangilangan=yangilangan)

                tarix = [ArizaTarixi(ariza=ariza, yangi_status=Ariza.Status.YANGI, kim=mijoz, vaqt=yaratilgan)]
                if taklif is not None:
                    oraliq = (yangilangan - yaratilgan) / 3
                    tarix.append(ArizaTarixi(ariza=ariza, eski_status=Ariza.Status.YANGI,
                                             yangi_status=Ariza.Status.NARX_TAKLIF, kim=usta.user,
                                             izoh=f"Taklif: {int(taklif):,} so'm".replace(',', ' '),
                                             vaqt=yaratilgan + oraliq))
                if status in (Ariza.Status.QABUL, Ariza.Status.BAJARILDI):
                    tarix.append(ArizaTarixi(ariza=ariza, eski_status=Ariza.Status.NARX_TAKLIF,
                                             yangi_status=Ariza.Status.QABUL, kim=mijoz,
                                             vaqt=yaratilgan + 2 * oraliq))
                if status == Ariza.Status.BAJARILDI:
                    tarix.append(ArizaTarixi(ariza=ariza, eski_status=Ariza.Status.QABUL,
                                             yangi_status=Ariza.Status.BAJARILDI, kim=usta.user, vaqt=yangilangan))
                if status == Ariza.Status.BEKOR:
                    tarix.append(ArizaTarixi(ariza=ariza, eski_status=Ariza.Status.YANGI,
                                             yangi_status=Ariza.Status.BEKOR, kim=mijoz, vaqt=yangilangan))
                ArizaTarixi.objects.bulk_create(tarix)

                if status == Ariza.Status.BAJARILDI:
                    javob = random.random() < 0.5
                    sharh = Sharh.objects.create(
                        ariza=ariza, baho=random.randint(3, 5), matn="Ish sifatli bajarildi",
                        usta_javobi="Rahmat! Yana murojaat qiling." if javob else '',
                        javob_vaqti=yangilangan + timedelta(hours=3) if javob else None,
                    )
                    Sharh.objects.filter(pk=sharh.pk).update(yaratilgan=yangilangan)

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {Usta.objects.count()} usta, {User.objects.count()} foydalanuvchi, "
            f"{Ariza.objects.count()} ariza, {Sharh.objects.count()} sharh. Parol: {PAROL}"
        ))
