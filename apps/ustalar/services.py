"""Ustaning shaxsiy kabinetidagi statistika."""
from datetime import datetime

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.arizalar.models import Ariza, Sharh

OYLAR = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']


def _oy_boshlari(oxirgi, soni):
    """oxirgi oydan orqaga qarab `soni` ta oyning birinchi kuni (eskisidan yangisiga)."""
    natija = []
    yil, oy = oxirgi.year, oxirgi.month
    for _ in range(soni):
        natija.append(oxirgi.replace(year=yil, month=oy))
        oy -= 1
        if oy == 0:
            yil, oy = yil - 1, 12
    return natija[::-1]


def _som(qiymat):
    return int(qiymat or 0)


def usta_statistikasi(usta, oylar_soni=6):
    bajarildi = Q(status=Ariza.Status.BAJARILDI)
    arizalar = Ariza.objects.filter(usta=usta)

    umumiy = arizalar.aggregate(
        jami=Count('id'),
        bajarildi=Count('id', filter=bajarildi),
        daromad=Sum('kelishilgan_narx', filter=bajarildi),
    )
    holatlar = {s: 0 for s in Ariza.Status.values}
    holatlar.update(dict(arizalar.order_by().values_list('status').annotate(n=Count('id'))))

    hozir = timezone.localtime()
    shu_oy_boshi = hozir.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    shu_oy = arizalar.filter(yaratilgan__gte=shu_oy_boshi).aggregate(
        arizalar=Count('id'),
        bajarildi=Count('id', filter=bajarildi),
        daromad=Sum('kelishilgan_narx', filter=bajarildi),
    )

    # Oxirgi N oy: arizalar yuborilgan oyi bo'yicha guruhlanadi. Ariza bo'lmagan oylar ham 0 bilan chiqadi,
    # aks holda grafikda bo'shliq bo'lib qoladi.
    oylar = _oy_boshlari(shu_oy_boshi, oylar_soni)
    qatorlar = (
        arizalar.filter(yaratilgan__gte=oylar[0])
        .annotate(oy=TruncMonth('yaratilgan'))
        .order_by()
        .values('oy')
        .annotate(
            arizalar=Count('id'),
            bajarildi=Count('id', filter=bajarildi),
            daromad=Sum('kelishilgan_narx', filter=bajarildi),
        )
    )
    oy_boyicha = {}
    for q in qatorlar:
        oy = q['oy']
        if isinstance(oy, datetime):
            oy = timezone.localtime(oy) if timezone.is_aware(oy) else oy
        oy_boyicha[(oy.year, oy.month)] = q

    sharhlar = Sharh.objects.filter(ariza__usta=usta)
    baholar = {b: 0 for b in range(1, 6)}
    baholar.update(dict(sharhlar.order_by().values_list('baho').annotate(n=Count('id'))))
    reyting = sharhlar.aggregate(r=Avg('baho'))['r']

    yakunlangan = holatlar[Ariza.Status.BAJARILDI] + holatlar[Ariza.Status.BEKOR]

    return {
        'jami_arizalar': umumiy['jami'],
        'holatlar': holatlar,
        'daromad': _som(umumiy['daromad']),
        # Yakunlangan arizalarning (bajarilgan + bekor qilingan) qanchasi bajarilgan
        'bajarish_foizi': round(100 * holatlar[Ariza.Status.BAJARILDI] / yakunlangan) if yakunlangan else None,
        'shu_oy': {
            'arizalar': shu_oy['arizalar'],
            'bajarildi': shu_oy['bajarildi'],
            'daromad': _som(shu_oy['daromad']),
        },
        'oylar': [
            {
                'oy': f'{oy.year}-{oy.month:02d}',
                'nomi': OYLAR[oy.month - 1],
                'arizalar': oy_boyicha.get((oy.year, oy.month), {}).get('arizalar', 0),
                'bajarildi': oy_boyicha.get((oy.year, oy.month), {}).get('bajarildi', 0),
                'daromad': _som(oy_boyicha.get((oy.year, oy.month), {}).get('daromad')),
            }
            for oy in oylar
        ],
        'reyting': round(reyting, 1) if reyting is not None else None,
        'sharhlar_soni': sum(baholar.values()),
        'baholar': {str(b): n for b, n in baholar.items()},
        'kategoriyalar': [
            {'nomi': nomi, 'soni': soni}
            for nomi, soni in arizalar.order_by().values('kategoriya__nomi')
            .annotate(soni=Count('id'))
            .order_by('-soni', 'kategoriya__nomi')
            .values_list('kategoriya__nomi', 'soni')
        ],
    }
