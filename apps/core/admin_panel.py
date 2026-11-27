"""Admin panel (django-unfold) uchun callback'lar: dashboard ma'lumotlari, menyu belgilari, muhit yorlig'i.

Sozlamalar config/settings/base.py dagi UNFOLD lug'atida, dashboard shabloni templates/admin/index.html da.
"""
import json
from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.arizalar.models import Ariza, Sharh
from apps.ustalar.models import Usta

GRAFIK_HAFTALARI = 12


def muhit(request):
    """Sarlavhadagi yorliq: qaysi serverda ishlayotganingizni adashtirmaslik uchun."""
    return ["Development", 'info'] if settings.DEBUG else ["Production", 'danger']


def tasdiq_kutayotganlar(request):
    soni = Usta.objects.filter(tasdiqlangan=False).count()
    return soni or None


def yangi_arizalar(request):
    soni = Ariza.objects.filter(status=Ariza.Status.YANGI).count()
    return soni or None


def _som(qiymat):
    return f"{int(qiymat or 0):,}".replace(',', ' ') + " so'm"


def _haftalik_grafik(hozir):
    """Oxirgi GRAFIK_HAFTALARI hafta: har haftada nechta ariza kelgani (hafta dushanbadan boshlanadi)."""
    bu_hafta = (hozir - timedelta(days=hozir.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    haftalar = [bu_hafta - timedelta(weeks=i) for i in range(GRAFIK_HAFTALARI - 1, -1, -1)]
    sanalar = list(
        Ariza.objects.filter(yaratilgan__gte=haftalar[0]).values_list('yaratilgan', flat=True)
    )
    sonlar = [0] * GRAFIK_HAFTALARI
    for sana in sanalar:
        indeks = (timezone.localtime(sana) - haftalar[0]).days // 7
        if 0 <= indeks < GRAFIK_HAFTALARI:
            sonlar[indeks] += 1
    return json.dumps({
        'labels': [f'{h.day:02d}.{h.month:02d}' for h in haftalar],
        'datasets': [{
            'label': "Arizalar",
            'data': sonlar,
            'backgroundColor': 'var(--color-primary-700)',
            'borderRadius': 4,
            'maxBarThickness': 36,
        }],
    })


def dashboard(request, context):
    hozir = timezone.localtime()
    hafta_oldin = hozir - timedelta(days=7)
    bajarildi = Q(status=Ariza.Status.BAJARILDI)

    arizalar = Ariza.objects.aggregate(
        jami=Count('id'),
        yangi=Count('id', filter=Q(status=Ariza.Status.YANGI)),
        narx_taklif=Count('id', filter=Q(status=Ariza.Status.NARX_TAKLIF)),
        qabul=Count('id', filter=Q(status=Ariza.Status.QABUL)),
        bajarildi=Count('id', filter=bajarildi),
        bekor=Count('id', filter=Q(status=Ariza.Status.BEKOR)),
        hafta=Count('id', filter=Q(yaratilgan__gte=hafta_oldin)),
        aylanma=Sum('kelishilgan_narx', filter=bajarildi),
    )
    foydalanuvchilar = User.objects.aggregate(
        jami=Count('id'),
        hafta=Count('id', filter=Q(date_joined__gte=hafta_oldin)),
    )
    ustalar = Usta.objects.aggregate(
        jami=Count('id'),
        tasdiqlangan=Count('id', filter=Q(tasdiqlangan=True)),
    )
    reyting = Sharh.objects.aggregate(r=Avg('baho'), n=Count('id'))

    yakunlangan = arizalar['bajarildi'] + arizalar['bekor']
    kutayotganlar = (
        Usta.objects.filter(tasdiqlangan=False).select_related('user', 'shahar')
        .prefetch_related('kategoriyalar').order_by('yaratilgan')[:5]
    )
    oxirgi_arizalar = Ariza.objects.select_related('mijoz', 'usta__user', 'kategoriya').order_by('-yaratilgan')[:6]

    context.update({
        'kartalar': [
            {
                'nomi': "Foydalanuvchilar",
                'qiymat': foydalanuvchilar['jami'],
                'izoh': f"+{foydalanuvchilar['hafta']} shu hafta",
                'ikon': 'group',
                'havola': reverse('admin:accounts_user_changelist'),
            },
            {
                'nomi': "Ustalar",
                'qiymat': ustalar['tasdiqlangan'],
                'izoh': f"{ustalar['jami'] - ustalar['tasdiqlangan']} ta tasdiq kutmoqda",
                'ikon': 'engineering',
                'havola': reverse('admin:ustalar_usta_changelist'),
            },
            {
                'nomi': "Arizalar",
                'qiymat': arizalar['jami'],
                'izoh': f"+{arizalar['hafta']} shu hafta, {arizalar['yangi']} ta yangi",
                'ikon': 'assignment',
                'havola': reverse('admin:arizalar_ariza_changelist'),
            },
            {
                'nomi': "Bajarilgan ishlar aylanmasi",
                'qiymat': _som(arizalar['aylanma']),
                'izoh': (
                    f"Bajarish ulushi: {round(100 * arizalar['bajarildi'] / yakunlangan)}%"
                    if yakunlangan else "Hali yakunlangan ariza yo'q"
                ),
                'ikon': 'payments',
                'havola': reverse('admin:arizalar_ariza_changelist') + '?status__exact=bajarildi',
            },
        ],
        'holatlar': [
            {'nomi': "Yangi", 'soni': arizalar['yangi'], 'status': 'yangi', 'rang': 'info'},
            {'nomi': "Narx taklif qilingan", 'soni': arizalar['narx_taklif'], 'status': 'narx_taklif',
             'rang': 'primary'},
            {'nomi': "Qabul qilingan", 'soni': arizalar['qabul'], 'status': 'qabul', 'rang': 'warning'},
            {'nomi': "Bajarilgan", 'soni': arizalar['bajarildi'], 'status': 'bajarildi', 'rang': 'success'},
            {'nomi': "Bekor qilingan", 'soni': arizalar['bekor'], 'status': 'bekor', 'rang': 'default'},
        ],
        'holatlar_jami': arizalar['jami'],
        'reyting': round(reyting['r'], 1) if reyting['r'] is not None else None,
        'sharhlar_soni': reyting['n'],
        'grafik': _haftalik_grafik(hozir),
        'grafik_sarlavha': f"Haftalik arizalar, oxirgi {GRAFIK_HAFTALARI} hafta",
        'kutayotganlar': kutayotganlar,
        'oxirgi_arizalar': oxirgi_arizalar,
    })
    return context
