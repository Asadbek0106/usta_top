from django.db import migrations


def tarixni_tiklash(apps, schema_editor):
    """Bu funksiya qo'shilishidan oldin yaratilgan arizalar uchun tarixni taxminan tiklaydi:
    "yaratildi" yozuvi (asl sanasi bilan) va hozirgi holatga o'tish (oxirgi o'zgarish sanasi bilan).
    Kim o'zgartirgani noma'lum, shuning uchun `kim` bo'sh qoladi."""
    Ariza = apps.get_model('arizalar', 'Ariza')
    ArizaTarixi = apps.get_model('arizalar', 'ArizaTarixi')
    yozuvlar = []
    for ariza in Ariza.objects.filter(tarix__isnull=True).iterator():
        yozuvlar.append(ArizaTarixi(
            ariza=ariza, eski_status='', yangi_status='yangi', kim_id=ariza.mijoz_id, vaqt=ariza.yaratilgan,
        ))
        if ariza.status != 'yangi':
            eski = 'qabul' if ariza.status == 'bajarildi' else 'yangi'
            if ariza.status == 'bajarildi':
                yozuvlar.append(ArizaTarixi(
                    ariza=ariza, eski_status='yangi', yangi_status='qabul', vaqt=ariza.yaratilgan,
                ))
            yozuvlar.append(ArizaTarixi(
                ariza=ariza, eski_status=eski, yangi_status=ariza.status, vaqt=ariza.yangilangan,
            ))
    ArizaTarixi.objects.bulk_create(yozuvlar, batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('arizalar', '0002_sharh_javob_arizatarixi'),
    ]

    operations = [
        migrations.RunPython(tarixni_tiklash, migrations.RunPython.noop),
    ]
