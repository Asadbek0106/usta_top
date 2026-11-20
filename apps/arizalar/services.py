from django.db import transaction

from apps.core.exceptions import BiznesXatosi

from .models import Ariza, Sharh


@transaction.atomic
def _status_ozgartir(ariza, yangi_status, **qoshimcha):
    ariza = Ariza.objects.select_for_update().get(pk=ariza.pk)

    if not ariza.otish_mumkinmi(yangi_status):
        raise BiznesXatosi(
            f"'{ariza.get_status_display()}' holatidagi arizani "
            f"'{Ariza.Status(yangi_status).label}' holatiga o'tkazib bo'lmaydi.",
            code='notogri_otish',
        )

    ariza.status = yangi_status
    for maydon, qiymat in qoshimcha.items():
        setattr(ariza, maydon, qiymat)
    ariza.save(update_fields=['status', 'yangilangan', *qoshimcha])
    return ariza


def qabul_qilish(ariza, kelishilgan_narx=None):
    qoshimcha = {}
    if kelishilgan_narx is not None:
        qoshimcha['kelishilgan_narx'] = kelishilgan_narx
    return _status_ozgartir(ariza, Ariza.Status.QABUL, **qoshimcha)


def bajarildi_deb_belgilash(ariza):
    return _status_ozgartir(ariza, Ariza.Status.BAJARILDI)


def bekor_qilish(ariza):
    return _status_ozgartir(ariza, Ariza.Status.BEKOR)


@transaction.atomic
def sharh_qoldirish(ariza, *, baho, matn=''):
    ariza = Ariza.objects.select_for_update().get(pk=ariza.pk)

    if ariza.status != Ariza.Status.BAJARILDI:
        raise BiznesXatosi("Sharhni faqat bajarilgan ariza uchun yozish mumkin.", code='bajarilmagan')
    if Sharh.objects.filter(ariza=ariza).exists():
        raise BiznesXatosi("Bu ariza uchun sharh allaqachon yozilgan.", code='sharh_bor')

    return Sharh.objects.create(ariza=ariza, baho=baho, matn=matn)
