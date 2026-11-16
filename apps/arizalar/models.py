from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel



class Ariza(TimeStampedModel):
    class Status(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        QABUL = 'qabul', 'Qabul qilindi'
        BAJARILDI = 'bajarildi', 'Bajarildi'
        BEKOR = 'bekor', 'Bekor qilindi'

    OTISHLAR = {
        Status.YANGI: {Status.QABUL, Status.BEKOR},
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


class Sharh(TimeStampedModel):
    ariza = models.OneToOneField(Ariza, on_delete=models.CASCADE, related_name='sharh')
    baho = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    matn = models.TextField(blank=True)

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
