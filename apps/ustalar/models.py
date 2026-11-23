from django.conf import settings
from django.db import models
from django.db.models import Avg, Count, OuterRef, Subquery
from django.db.models.functions import Round

from apps.core.models import TimeStampedModel


class Shahar(models.Model):
    nomi = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Shahar"
        verbose_name_plural = "Shaharlar"
        ordering = ['nomi']

    def __str__(self):
        return self.nomi


class Kategoriya(models.Model):
    nomi = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    faol = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['nomi']

    def __str__(self):
        return self.nomi


class UstaQuerySet(models.QuerySet):
    def faol(self):
        return self.filter(tasdiqlangan=True, user__is_active=True)

    def reyting_bilan(self):
        return self.annotate(
            reyting=Round(Avg('arizalar__sharh__baho'), 1),
            sharhlar_soni=Count('arizalar__sharh', distinct=True),
        )

    def narx_bilan(self):
        # Subquery: Count/Avg bilan bitta so'rovda JOIN qilinsa qatorlar ko'payib ketadi
        xizmatlar = Xizmat.objects.filter(usta=OuterRef('pk'))
        return self.annotate(
            eng_arzon=Subquery(xizmatlar.order_by('narx_dan').values('narx_dan')[:1]),
            tajriba_yil=Subquery(xizmatlar.order_by('-tajriba').values('tajriba')[:1]),
        )


class Usta(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usta_profil',
    )
    shahar = models.ForeignKey(Shahar, on_delete=models.PROTECT, related_name='ustalar')
    kategoriyalar = models.ManyToManyField(
        Kategoriya,
        through='Xizmat',
        related_name='ustalar',
    )
    tavsif = models.TextField(blank=True)
    tasdiqlangan = models.BooleanField(default=False)

    objects = UstaQuerySet.as_manager()

    class Meta:
        verbose_name = "Usta"
        verbose_name_plural = "Ustalar"
        ordering = ['-yaratilgan']

    def __str__(self):
        return str(self.user)


class Xizmat(models.Model):
    usta = models.ForeignKey(Usta, on_delete=models.CASCADE, related_name='xizmatlar')
    kategoriya = models.ForeignKey(Kategoriya, on_delete=models.PROTECT, related_name='xizmatlar')
    narx_dan = models.DecimalField(max_digits=12, decimal_places=2)
    tajriba = models.PositiveSmallIntegerField(default=0, help_text="Yil")

    class Meta:
        verbose_name = "Xizmat"
        verbose_name_plural = "Xizmatlar"
        constraints = [
            models.UniqueConstraint(fields=['usta', 'kategoriya'], name='usta_kategoriya_unique'),
            models.CheckConstraint(condition=models.Q(narx_dan__gte=0), name='narx_manfiy_emas'),
        ]

    def __str__(self):
        return f"{self.usta} — {self.kategoriya}"


class Sevimli(models.Model):
    """Mijoz keyinroq qayta topish uchun saqlab qo'ygan usta."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sevimli_ustalar',
    )
    usta = models.ForeignKey(Usta, on_delete=models.CASCADE, related_name='sevimlilar')
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sevimli usta"
        verbose_name_plural = "Sevimli ustalar"
        ordering = ['-yaratilgan']
        constraints = [
            models.UniqueConstraint(fields=['user', 'usta'], name='sevimli_unique'),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.usta}"
