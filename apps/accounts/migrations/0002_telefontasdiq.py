from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelefonTasdiq',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefon', models.CharField(db_index=True, max_length=13, verbose_name='Telefon raqam')),
                ('kod', models.CharField(max_length=6, verbose_name='Kod')),
                ('chat_id', models.BigIntegerField(verbose_name='Telegram chat ID')),
                ('urinishlar', models.PositiveSmallIntegerField(default=0, verbose_name="Noto'g'ri urinishlar")),
                ('ishlatilgan', models.BooleanField(default=False, verbose_name='Ishlatilgan')),
                ('yaratilgan', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')),
            ],
            options={
                'verbose_name': 'Telefon tasdiqlash kodi',
                'verbose_name_plural': 'Telefon tasdiqlash kodlari',
                'ordering': ('-yaratilgan',),
            },
        ),
    ]
