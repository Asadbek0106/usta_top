from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BiznesXatosi

from .models import Ariza, ArizaTarixi, Sharh


def tarixga_yoz(ariza, yangi_status, *, eski_status='', kim=None):
    return ArizaTarixi.objects.create(ariza=ariza, eski_status=eski_status, yangi_status=yangi_status, kim=kim)


@transaction.atomic
def ariza_yaratish(**malumot):
    ariza = Ariza.objects.create(**malumot)
    tarixga_yoz(ariza, ariza.status, kim=ariza.mijoz)
    return ariza


@transaction.atomic
def _status_ozgartir(ariza, yangi_status, *, kim=None, **qoshimcha):
    ariza = Ariza.objects.select_for_update().get(pk=ariza.pk)

    if not ariza.otish_mumkinmi(yangi_status):
        raise BiznesXatosi(
            f"'{ariza.get_status_display()}' holatidagi arizani "
            f"'{Ariza.Status(yangi_status).label}' holatiga o'tkazib bo'lmaydi.",
            code='notogri_otish',
        )

    eski_status = ariza.status
    ariza.status = yangi_status
    for maydon, qiymat in qoshimcha.items():
        setattr(ariza, maydon, qiymat)
    ariza.save(update_fields=['status', 'yangilangan', *qoshimcha])
    tarixga_yoz(ariza, yangi_status, eski_status=eski_status, kim=kim)
    return ariza


def qabul_qilish(ariza, kelishilgan_narx=None, *, kim=None):
    qoshimcha = {}
    if kelishilgan_narx is not None:
        qoshimcha['kelishilgan_narx'] = kelishilgan_narx
    return _status_ozgartir(ariza, Ariza.Status.QABUL, kim=kim, **qoshimcha)


def bajarildi_deb_belgilash(ariza, *, kim=None):
    return _status_ozgartir(ariza, Ariza.Status.BAJARILDI, kim=kim)


def bekor_qilish(ariza, *, kim=None):
    return _status_ozgartir(ariza, Ariza.Status.BEKOR, kim=kim)


@transaction.atomic
def sharh_qoldirish(ariza, *, baho, matn=''):
    ariza = Ariza.objects.select_for_update().get(pk=ariza.pk)

    if ariza.status != Ariza.Status.BAJARILDI:
        raise BiznesXatosi("Sharhni faqat bajarilgan ariza uchun yozish mumkin.", code='bajarilmagan')
    if Sharh.objects.filter(ariza=ariza).exists():
        raise BiznesXatosi("Bu ariza uchun sharh allaqachon yozilgan.", code='sharh_bor')

    return Sharh.objects.create(ariza=ariza, baho=baho, matn=matn)


@transaction.atomic
def sharhga_javob(ariza, *, matn):
    """Usta mijoz qoldirgan sharhga ochiq javob yozadi (yoki javobini tahrirlaydi)."""
    sharh = Sharh.objects.select_for_update().filter(ariza=ariza).first()
    if sharh is None:
        raise BiznesXatosi("Bu arizaga hali sharh yozilmagan.", code='sharh_yoq')
    sharh.usta_javobi = matn
    sharh.javob_vaqti = timezone.now()
    sharh.save(update_fields=['usta_javobi', 'javob_vaqti', 'yangilangan'])
    return sharh
