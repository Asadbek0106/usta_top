import uuid
from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Ariza(TimeStampedModel):
    class Status(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        NARX_TAKLIF = 'narx_taklif', 'Narx taklif qilindi'
        QABUL = 'qabul', 'Qabul qilindi'
        BAJARILDI = 'bajarildi', 'Bajarildi'
        BEKOR = 'bekor', 'Bekor qilindi'

    # Ish jarayoni:
    #   yangi        — mijoz ish tavsifi va rasmlarini yubordi, usta ko'rib narx taklif qiladi
    #   narx_taklif  — usta narx aytdi; mijoz rozi bo'lsa → qabul, rad etsa → yana yangi
    #                  (usta boshqa narx taklif qilishi mumkin). Javob kutilayotganda usta narxni o'zgartira oladi.
    #   qabul        — narx kelishildi, usta ishni bajaradi → bajarildi
    # Tugamagan arizani mijoz ham, usta ham istalgan payt bekor qila oladi.
    OTISHLAR = {
        Status.YANGI: {Status.NARX_TAKLIF, Status.BEKOR},
        Status.NARX_TAKLIF: {Status.NARX_TAKLIF, Status.QABUL, Status.YANGI, Status.BEKOR},
        Status.QABUL: {Status.BAJARILDI, Status.BEKOR},
    }

    mijoz = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='arizalar',
    )
    usta = models.ForeignKey('ustalar.Usta', on_delete=models.CASCADE, related_name='arizalar')
    kategoriya = models.ForeignKey('ustalar.Kategoriya', on_delete=models.PROTECT, related_name='arizalar')
    tavsif = models.TextField()
    manzil = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.YANGI)
    taklif_narx = models.DecimalField(
        "Usta taklif qilgan narx", max_digits=12, decimal_places=2, null=True, blank=True,
    )
    taklif_izoh = models.TextField("Taklif izohi", blank=True)
    kelishilgan_narx = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        ordering = ['-yaratilgan']
        indexes = [
            models.Index(fields=['usta', 'status']),
            models.Index(fields=['mijoz', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kelishilgan_narx__isnull=True) | models.Q(kelishilgan_narx__gte=0),
                name='kelishilgan_narx_manfiy_emas',
            ),
            models.CheckConstraint(
                condition=models.Q(taklif_narx__isnull=True) | models.Q(taklif_narx__gte=0),
                name='taklif_narx_manfiy_emas',
            ),
        ]

    def __str__(self):
        return f"#{self.pk} {self.mijoz} → {self.usta} [{self.get_status_display()}]"

    def clean(self):
        if not (self.usta_id and self.mijoz_id):
            return
        if self.mijoz_id == self.usta.user_id:
            raise ValidationError("Usta o'ziga ariza bera olmaydi.")
        if self.kategoriya_id and not self.usta.xizmatlar.filter(kategoriya_id=self.kategoriya_id).exists():
            raise ValidationError({'kategoriya': "Bu usta tanlangan kategoriyada ishlamaydi."})

    def otish_mumkinmi(self, yangi_status):
        return yangi_status in self.OTISHLAR.get(self.status, set())


def ariza_rasmi_yoli(instance, filename):
    """Fayl nomi tasodifiy UUID: asl nom (shaxsiy ma'lumot bo'lishi mumkin) saqlanmaydi va
    manzilni taxmin qilib boshqa mijozlarning rasmlarini ochib bo'lmaydi."""
    kengaytma = PurePath(filename).suffix.lower()[:5] or '.jpg'
    return f'arizalar/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{kengaytma}'


class ArizaRasm(models.Model):
    """Mijoz arizaga biriktirgan rasm: usta ishni ko'rib, narxni shunga qarab belgilaydi."""

    ariza = models.ForeignKey(Ariza, on_delete=models.CASCADE, related_name='rasmlar')
    rasm = models.ImageField("Rasm", upload_to=ariza_rasmi_yoli)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ariza rasmi"
        verbose_name_plural = "Ariza rasmlari"
        ordering = ['pk']

    def __str__(self):
        return f"#{self.ariza_id} rasmi"


class Sharh(TimeStampedModel):
    ariza = models.OneToOneField(Ariza, on_delete=models.CASCADE, related_name='sharh')
    baho = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    matn = models.TextField(blank=True)
    usta_javobi = models.TextField("Ustaning javobi", blank=True)
    javob_vaqti = models.DateTimeField("Javob yozilgan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ['-yaratilgan']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(baho__gte=1, baho__lte=5),
                name='baho_1_5_oraligida',
            ),
        ]

    def __str__(self):
        return f"{self.ariza.usta}: {self.baho}★"

    def clean(self):
        if self.ariza_id and self.ariza.status != Ariza.Status.BAJARILDI:
            raise ValidationError("Sharhni faqat bajarilgan ariza uchun yozish mumkin.")


class ArizaTarixi(models.Model):
    """Arizaning har bir holat o'zgarishi: kim, qachon, qaysi holatdan qaysi holatga o'tkazgani.

    Birinchi yozuv ariza yaratilganda qo'shiladi (eski_status bo'sh bo'ladi).
    """

    ariza = models.ForeignKey(Ariza, on_delete=models.CASCADE, related_name='tarix')
    eski_status = models.CharField(max_length=20, choices=Ariza.Status.choices, blank=True)
    yangi_status = models.CharField(max_length=20, choices=Ariza.Status.choices)
    # Masalan: "Taklif: 150 000 so'm" yoki mijoz narxni rad etgan sabab
    izoh = models.CharField(max_length=500, blank=True)
    kim = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    # auto_now_add emas: eski arizalar uchun tarixni migratsiyada asl sanasi bilan tiklash kerak
    vaqt = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Ariza tarixi"
        verbose_name_plural = "Ariza tarixi"
        ordering = ['vaqt', 'pk']

    def __str__(self):
        eski = Ariza.Status(self.eski_status).label if self.eski_status else '—'
        return f"#{self.ariza_id}: {eski} → {self.get_yangi_status_display()}"
