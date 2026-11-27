from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BiznesXatosi

from .models import Ariza, ArizaRasm, ArizaTarixi, Sharh


def som_matni(qiymat):
    """150000 → "150 000 so'm" (tarix izohlari uchun)."""
    return f"{int(qiymat):,} so'm".replace(',', ' ')


def tarixga_yoz(ariza, yangi_status, *, eski_status='', kim=None, izoh=''):
    return ArizaTarixi.objects.create(
        ariza=ariza, eski_status=eski_status, yangi_status=yangi_status, kim=kim, izoh=izoh[:500],
    )


@transaction.atomic
def ariza_yaratish(*, rasmlar=(), **malumot):
    ariza = Ariza.objects.create(**malumot)
    for rasm in rasmlar:
        ArizaRasm.objects.create(ariza=ariza, rasm=rasm)
    izoh = f"{len(rasmlar)} ta rasm biriktirildi" if rasmlar else ''
    tarixga_yoz(ariza, ariza.status, kim=ariza.mijoz, izoh=izoh)
    return ariza


@transaction.atomic
def _status_ozgartir(ariza, yangi_status, *, kim=None, izoh='', **qoshimcha):
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
    tarixga_yoz(ariza, yangi_status, eski_status=eski_status, kim=kim, izoh=izoh)
    return ariza


def narx_taklif_qilish(ariza, *, narx, izoh='', kim=None):
    """Usta rasmlar va tavsifni ko'rib narx aytadi. Mijoz javob bermagan bo'lsa, narxni o'zgartirish ham shu."""
    tarix_izohi = f"Taklif: {som_matni(narx)}" + (f". {izoh}" if izoh else '')
    return _status_ozgartir(
        ariza, Ariza.Status.NARX_TAKLIF, kim=kim, izoh=tarix_izohi,
        taklif_narx=narx, taklif_izoh=izoh,
    )


@transaction.atomic
def narxga_rozilik(ariza, *, kutilgan_narx=None, kim=None):
    """Mijoz usta taklif qilgan narxga rozi: narx kelishilgan hisoblanadi va ish boshlanadi.

    kutilgan_narx — mijoz ekranda ko'rgan narx. Usta shu orada narxni o'zgartirgan bo'lsa,
    mijoz o'zi ko'rmagan narxga "rozi" bo'lib qolmasligi uchun so'rov rad etiladi.
    """
    narx = Ariza.objects.select_for_update().values_list('taklif_narx', flat=True).get(pk=ariza.pk)
    if narx is None:
        raise BiznesXatosi("Usta hali narx taklif qilmagan.", code='taklif_yoq')
    if kutilgan_narx is not None and kutilgan_narx != narx:
        raise BiznesXatosi(
            f"Usta narxni o'zgartirdi: yangi narx {som_matni(narx)}. Sahifani yangilab, qaytadan ko'ring.",
            code='narx_ozgargan',
        )
    return _status_ozgartir(
        ariza, Ariza.Status.QABUL, kim=kim, izoh=f"Kelishilgan narx: {som_matni(narx)}",
        kelishilgan_narx=narx,
    )


def narxni_rad_etish(ariza, *, sabab='', kim=None):
    """Mijoz narxga rozi emas: ariza yana "yangi" holatiga qaytadi, usta boshqa narx taklif qilishi mumkin."""
    return _status_ozgartir(
        ariza, Ariza.Status.YANGI, kim=kim, izoh=f"Narx rad etildi. {sabab}".strip(),
        taklif_narx=None, taklif_izoh='',
    )


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
