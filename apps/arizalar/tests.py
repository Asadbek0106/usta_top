import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.core.testing import BaseAPITestCase, ariza_yarat

from . import services
from .models import Ariza, ArizaRasm, ArizaTarixi, Sharh

ARIZALAR = '/api/v1/arizalar/'


def rasm_fayli(nomi='kran.jpg', hajm=(40, 30)):
    buf = io.BytesIO()
    Image.new('RGB', hajm, (200, 80, 40)).save(buf, format='JPEG')
    return SimpleUploadedFile(nomi, buf.getvalue(), content_type='image/jpeg')


class ArizaYaratishTest(BaseAPITestCase):
    def malumot(self, **kwargs):
        return {'usta': self.usta.pk, 'kategoriya': self.santexnik.pk,
                'tavsif': 'Kran oqyapti', 'manzil': 'Chilonzor', **kwargs}

    def test_mijoz_ariza_yaratadi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(), format='json')
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data['status'], 'yangi')
        self.assertEqual(Ariza.objects.get().mijoz, self.mijoz)

    def test_mehmon_ariza_yaratolmaydi(self):
        self.assertEqual(self.client.post(ARIZALAR, self.malumot(), format='json').status_code, 401)

    def test_usta_oziga_ariza_berolmaydi(self):
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(ARIZALAR, self.malumot(), format='json').status_code, 400)

    def test_usta_ishlamaydigan_kategoriya(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(kategoriya=self.elektrik.pk), format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kategoriya', javob.data)

    def test_mijozni_soxtalashtirib_bolmaydi(self):
        self.kirish(self.mijoz)
        self.client.post(ARIZALAR, self.malumot(mijoz=self.begona_mijoz.pk), format='json')
        self.assertEqual(Ariza.objects.get().mijoz, self.mijoz)

    def test_status_bilan_yaratib_bolmaydi(self):
        self.kirish(self.mijoz)
        self.client.post(ARIZALAR, self.malumot(status='bajarildi'), format='json')
        self.assertEqual(Ariza.objects.get().status, Ariza.Status.YANGI)


class ArizaKorishTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)

    def test_mijoz_va_usta_koradi(self):
        for user in (self.mijoz, self.usta.user):
            self.kirish(user)
            self.assertEqual(self.client.get(ARIZALAR).data['count'], 1)
            self.assertEqual(self.client.get(f'{ARIZALAR}{self.ariza.pk}/').status_code, 200)

    def test_begonalar_kormaydi(self):
        for user in (self.begona_mijoz, self.begona_usta.user):
            self.kirish(user)
            self.assertEqual(self.client.get(ARIZALAR).data['count'], 0)
            self.assertEqual(self.client.get(f'{ARIZALAR}{self.ariza.pk}/').status_code, 404)


class ArizaTahrirlashTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.url = f'{ARIZALAR}{self.ariza.pk}/'

    def test_mijoz_yangi_arizani_tahrirlaydi(self):
        self.kirish(self.mijoz)
        javob = self.client.patch(self.url, {'tavsif': 'Yangi tavsif', 'manzil': 'Yunusobod'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.tavsif, 'Yangi tavsif')
        self.assertEqual(self.ariza.manzil, 'Yunusobod')

    def test_qabul_qilingan_arizani_tahrirlab_bolmaydi(self):
        Ariza.objects.filter(pk=self.ariza.pk).update(status=Ariza.Status.QABUL)
        self.kirish(self.mijoz)
        self.assertEqual(self.client.patch(self.url, {'tavsif': 'x'}, format='json').status_code, 400)

    def test_usta_arizani_tahrirlay_olmaydi(self):
        self.kirish(self.usta.user)
        self.assertEqual(self.client.patch(self.url, {'tavsif': 'x'}, format='json').status_code, 403)

    def test_begona_tahrirlay_olmaydi(self):
        self.kirish(self.begona_mijoz)
        self.assertEqual(self.client.patch(self.url, {'tavsif': 'x'}, format='json').status_code, 404)

    def test_patch_orqali_status_ozgarmaydi(self):
        self.kirish(self.mijoz)
        self.client.patch(self.url, {'status': 'bajarildi', 'kelishilgan_narx': '1'}, format='json')
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.status, Ariza.Status.YANGI)
        self.assertIsNone(self.ariza.kelishilgan_narx)

    def test_put_ruxsat_etilmagan(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.put(self.url, {'tavsif': 'x', 'manzil': 'y'}, format='json').status_code, 405)

    def test_arizani_ochirib_bolmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.delete(self.url).status_code, 405)


class ArizaHolatlariTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.url = f'{ARIZALAR}{self.ariza.pk}'

    def test_toliq_oqim_va_reyting(self):
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/narx-taklif/', {'narx': '150000', 'izoh': 'Kran narxi ichida'},
                                 format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['status'], 'narx_taklif')
        self.assertEqual(javob.data['taklif_narx'], '150000.00')
        self.assertEqual(javob.data['taklif_izoh'], 'Kran narxi ichida')
        self.assertIsNone(javob.data['kelishilgan_narx'])

        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/narx-rozi/', {'narx': '150000'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['status'], 'qabul')
        self.assertEqual(javob.data['kelishilgan_narx'], '150000.00')

        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(f'{self.url}/bajarildi/').status_code, 200)

        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/sharh/', {'baho': 5, 'matn': 'Zo‘r'}, format='json')
        self.assertEqual(javob.status_code, 201, javob.data)

        javob = self.client.get(f'/api/v1/ustalar/{self.usta.pk}/')
        self.assertEqual(javob.data['reyting'], 5.0)
        self.assertEqual(javob.data['sharhlar_soni'], 1)

    def test_begona_usta_narx_taklif_qilolmaydi(self):
        self.kirish(self.begona_usta.user)
        self.assertEqual(self.client.post(f'{self.url}/narx-taklif/', {'narx': '1000'}, format='json').status_code, 404)

    def test_mijoz_narx_taklif_qilolmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.post(f'{self.url}/narx-taklif/', {'narx': '1000'}, format='json').status_code, 403)

    def test_yangi_arizani_bajarildi_qilib_bolmaydi(self):
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/bajarildi/')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'notogri_otish')

    def test_mijoz_ham_usta_ham_bekor_qila_oladi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.post(f'{self.url}/bekor/').status_code, 200)

        boshqa = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(f'{ARIZALAR}{boshqa.pk}/bekor/').status_code, 200)

    def test_bekor_qilingan_arizaga_narx_taklif_qilib_bolmaydi(self):
        services.bekor_qilish(self.ariza)
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/narx-taklif/', {'narx': '1000'}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'notogri_otish')

    def test_narx_musbat_va_majburiy(self):
        self.kirish(self.usta.user)
        for malumot in ({}, {'narx': '-100'}, {'narx': '0'}, {'narx': 'abc'}):
            self.assertEqual(self.client.post(f'{self.url}/narx-taklif/', malumot, format='json').status_code, 400)
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.status, Ariza.Status.YANGI)

    def test_eski_qabul_yoli_yoq(self):
        # Usta mijozning roziligisiz ishni o'zi "qabul qilib" qo'ya olmaydi
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(f'{self.url}/qabul/', {'kelishilgan_narx': '1'}, format='json').status_code,
                         404)


class NarxKelishuvTest(BaseAPITestCase):
    """Usta narx taklif qiladi, mijoz rozi bo'ladi yoki rad etadi."""

    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.url = f'{ARIZALAR}{self.ariza.pk}'

    def taklif(self, narx='200000', izoh=''):
        return services.narx_taklif_qilish(self.ariza, narx=Decimal(narx), izoh=izoh, kim=self.usta.user)

    def test_taklifsiz_rozi_bolib_bolmaydi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/narx-rozi/', {}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'taklif_yoq')

    def test_usta_mijoz_orniga_rozi_bololmaydi(self):
        self.taklif()
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(f'{self.url}/narx-rozi/', {}, format='json').status_code, 403)
        self.assertEqual(self.client.post(f'{self.url}/narx-rad/', {}, format='json').status_code, 403)

    def test_narx_ozgargan_bolsa_rozilik_rad_etiladi(self):
        self.taklif('200000')
        self.taklif('250000')  # usta mijoz javob bermasidan narxni o'zgartirdi
        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/narx-rozi/', {'narx': '200000'}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'narx_ozgargan')
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.status, Ariza.Status.NARX_TAKLIF)
        self.assertIsNone(self.ariza.kelishilgan_narx)

        javob = self.client.post(f'{self.url}/narx-rozi/', {'narx': '250000'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['kelishilgan_narx'], '250000.00')

    def test_rad_etilsa_yangi_holatga_qaytadi_va_qayta_taklif_mumkin(self):
        self.taklif('500000', 'Quvurni ham almashtirish kerak')
        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/narx-rad/', {'sabab': 'Juda qimmat'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['status'], 'yangi')
        self.assertIsNone(javob.data['taklif_narx'])
        self.assertEqual(javob.data['taklif_izoh'], '')
        self.assertEqual(javob.data['tarix'][-1]['izoh'], 'Narx rad etildi. Juda qimmat')

        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/narx-taklif/', {'narx': '400000'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['taklif_narx'], '400000.00')

    def test_yangi_arizada_rad_etib_bolmaydi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/narx-rad/', {}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'notogri_otish')

    def test_qabul_qilingandan_keyin_narxni_ozgartirib_bolmaydi(self):
        self.taklif()
        services.narxga_rozilik(self.ariza, kim=self.mijoz)
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/narx-taklif/', {'narx': '999999'}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.kelishilgan_narx, Decimal('200000'))

    def test_taklif_kutilayotganda_mijoz_arizani_tahrirlay_olmaydi(self):
        self.taklif()
        self.kirish(self.mijoz)
        self.assertEqual(self.client.patch(f'{self.url}/', {'tavsif': 'boshqa ish'}, format='json').status_code, 400)

    def test_tarixga_narx_yoziladi(self):
        self.taklif('150000', 'Ehtiyot qismlar bilan')
        services.narxga_rozilik(self.ariza, kim=self.mijoz)
        izohlar = list(ArizaTarixi.objects.filter(ariza=self.ariza).values_list('yangi_status', 'izoh'))
        self.assertEqual(izohlar, [
            ('narx_taklif', "Taklif: 150 000 so'm. Ehtiyot qismlar bilan"),
            ('qabul', "Kelishilgan narx: 150 000 so'm"),
        ])


class ArizaRasmTest(BaseAPITestCase):
    def malumot(self, **kwargs):
        return {'usta': self.usta.pk, 'kategoriya': self.santexnik.pk,
                'tavsif': 'Kran oqyapti', 'manzil': 'Chilonzor', **kwargs}

    def test_rasmlar_bilan_ariza_yuboriladi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(rasmlar=[rasm_fayli('a.jpg'), rasm_fayli('b.JPG')]),
                                 format='multipart')
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(len(javob.data['rasmlar']), 2)
        manzil = javob.data['rasmlar'][0]['rasm']
        self.assertTrue(manzil.startswith('/media/arizalar/'), manzil)
        self.assertTrue(manzil.endswith('.jpg'))
        self.assertNotIn('a.jpg', manzil)  # asl fayl nomi saqlanmaydi
        self.assertEqual(javob.data['tarix'][0]['izoh'], '2 ta rasm biriktirildi')

        # Usta ham shu rasmlarni ko'radi
        self.kirish(self.usta.user)
        self.assertEqual(len(self.client.get(f"{ARIZALAR}{javob.data['id']}/").data['rasmlar']), 2)

    def test_rasmsiz_ham_yuborish_mumkin(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(), format='multipart')
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data['rasmlar'], [])

    def test_rasm_bolmagan_fayl_rad_etiladi(self):
        self.kirish(self.mijoz)
        soxta = SimpleUploadedFile('virus.jpg', b'bu rasm emas', content_type='image/jpeg')
        javob = self.client.post(ARIZALAR, self.malumot(rasmlar=[soxta]), format='multipart')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('rasmlar', javob.data)
        self.assertFalse(Ariza.objects.exists())

    def test_rasmlar_soni_cheklangan(self):
        self.kirish(self.mijoz)
        rasmlar = [rasm_fayli(f'{i}.jpg') for i in range(6)]
        javob = self.client.post(ARIZALAR, self.malumot(rasmlar=rasmlar), format='multipart')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('rasmlar', javob.data)

    @override_settings(ARIZA_RASM_HAJMI_MB=0)
    def test_katta_rasm_rad_etiladi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(rasmlar=[rasm_fayli()]), format='multipart')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('rasmlar', javob.data)
        self.assertFalse(ArizaRasm.objects.exists())

    def test_rasmni_ochish(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(rasmlar=[rasm_fayli()]), format='multipart')
        rasm = self.client.get(javob.data['rasmlar'][0]['rasm'])
        self.assertEqual(rasm.status_code, 200)
        self.assertEqual(rasm['Content-Type'], 'image/jpeg')


class SharhTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                                 status=Ariza.Status.BAJARILDI)
        self.url = f'{ARIZALAR}{self.ariza.pk}/sharh/'

    def test_usta_sharh_yozolmaydi(self):
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(self.url, {'baho': 5}, format='json').status_code, 403)

    def test_bajarilmagan_arizaga_sharh_yozib_bolmaydi(self):
        Ariza.objects.filter(pk=self.ariza.pk).update(status=Ariza.Status.QABUL)
        self.kirish(self.mijoz)
        javob = self.client.post(self.url, {'baho': 5}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'bajarilmagan')

    def test_ikkinchi_sharh_rad_etiladi(self):
        self.kirish(self.mijoz)
        self.client.post(self.url, {'baho': 4}, format='json')
        javob = self.client.post(self.url, {'baho': 5}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'sharh_bor')
        self.assertEqual(Sharh.objects.count(), 1)

    def test_baho_1_dan_5_gacha(self):
        self.kirish(self.mijoz)
        for baho in (0, 6, 9):
            self.assertEqual(self.client.post(self.url, {'baho': baho}, format='json').status_code, 400)
        self.assertEqual(Sharh.objects.count(), 0)


class ArizaFiltrTest(BaseAPITestCase):
    """9-etap: arizalarni rol va status bo'yicha filtrlash."""

    def setUp(self):
        super().setUp()
        # self.usta.user bir vaqtning o'zida ham usta (unga ariza kelgan), ham mijoz (o'zi ariza yuborgan)
        self.kelgan = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.yuborgan = ariza_yarat(mijoz=self.usta.user, usta=self.begona_usta, kategoriya=self.santexnik,
                                    status=Ariza.Status.BAJARILDI)
        self.kirish(self.usta.user)

    def idlar(self, **params):
        javob = self.client.get(ARIZALAR, params)
        self.assertEqual(javob.status_code, 200, javob.data)
        return [a['id'] for a in javob.data['results']]

    def test_hammasi(self):
        self.assertCountEqual(self.idlar(), [self.kelgan.pk, self.yuborgan.pk])

    def test_rol_boyicha(self):
        self.assertEqual(self.idlar(rol='usta'), [self.kelgan.pk])
        self.assertEqual(self.idlar(rol='mijoz'), [self.yuborgan.pk])

    def test_status_boyicha(self):
        self.assertEqual(self.idlar(status='bajarildi'), [self.yuborgan.pk])

    def test_notogri_rol_400(self):
        self.assertEqual(self.client.get(ARIZALAR, {'rol': 'admin'}).status_code, 400)

    def test_sukut_boyicha_eng_yangisi_birinchi(self):
        self.assertEqual(self.idlar(), [self.yuborgan.pk, self.kelgan.pk])

    def test_royxat_sorovlar_soni(self):
        for _ in range(10):
            ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        # COUNT + arizalar (bog'lanishlar JOIN orqali) + tarix va rasmlar (prefetch): ariza soniga bog'liq emas
        with self.assertNumQueries(4):
            self.client.get(ARIZALAR)


class ArizaQoshimchaHimoyaTest(BaseAPITestCase):
    """Nofaol kategoriya va spamdan himoya."""

    def malumot(self):
        return {'usta': self.usta.pk, 'kategoriya': self.santexnik.pk, 'tavsif': 'Kran', 'manzil': 'Chilonzor'}

    def test_nofaol_kategoriyaga_ariza_berib_bolmaydi(self):
        self.santexnik.faol = False
        self.santexnik.save()
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, self.malumot(), format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertIn('kategoriya', javob.data)

    def test_soatiga_20_tadan_ortiq_ariza_yuborib_bolmaydi(self):
        self.kirish(self.mijoz)
        for _ in range(20):
            self.assertEqual(self.client.post(ARIZALAR, self.malumot(), format='json').status_code, 201)
        self.assertEqual(self.client.post(ARIZALAR, self.malumot(), format='json').status_code, 429)
        # Cheklov faqat yaratishga tegishli: ro'yxatni ko'rish ishlayveradi
        self.assertEqual(self.client.get(ARIZALAR).status_code, 200)


class ArizaTarixiTest(BaseAPITestCase):
    def test_yaratishdan_bajarilgunicha_tarix_yoziladi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(ARIZALAR, {'usta': self.usta.pk, 'kategoriya': self.santexnik.pk,
                                            'tavsif': 'Kran', 'manzil': 'Chilonzor'}, format='json')
        pk = javob.data['id']
        self.assertEqual([t['yangi_status'] for t in javob.data['tarix']], ['yangi'])
        self.assertIsNone(javob.data['tarix'][0]['eski_status_nomi'])

        self.kirish(self.usta.user)
        self.client.post(f'{ARIZALAR}{pk}/narx-taklif/', {'narx': '150000'}, format='json')
        self.kirish(self.mijoz)
        self.client.post(f'{ARIZALAR}{pk}/narx-rozi/', {}, format='json')
        self.kirish(self.usta.user)
        javob = self.client.post(f'{ARIZALAR}{pk}/bajarildi/')

        tarix = javob.data['tarix']
        self.assertEqual([(t['eski_status'], t['yangi_status']) for t in tarix],
                         [('', 'yangi'), ('yangi', 'narx_taklif'), ('narx_taklif', 'qabul'), ('qabul', 'bajarildi')])
        self.assertEqual(tarix[1]['kim'], str(self.usta.user))
        self.assertEqual(tarix[2]['kim'], str(self.mijoz))
        self.assertEqual(tarix[3]['yangi_status_nomi'], 'Bajarildi')

    def test_bekor_qilganni_tarix_eslab_qoladi(self):
        ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.kirish(self.mijoz)
        self.client.post(f'{ARIZALAR}{ariza.pk}/bekor/')
        yozuv = ArizaTarixi.objects.get(ariza=ariza)
        self.assertEqual((yozuv.eski_status, yozuv.yangi_status, yozuv.kim), ('yangi', 'bekor', self.mijoz))

    def test_rad_etilgan_otish_tarixga_yozilmaydi(self):
        ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik)
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(f'{ARIZALAR}{ariza.pk}/bajarildi/').status_code, 400)
        self.assertFalse(ArizaTarixi.objects.filter(ariza=ariza).exists())


class SharhJavobTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                                 status=Ariza.Status.BAJARILDI)
        self.url = f'{ARIZALAR}{self.ariza.pk}/sharh/javob/'

    def sharh_yoz(self):
        return Sharh.objects.create(ariza=self.ariza, baho=4, matn='Yaxshi')

    def test_usta_sharhga_javob_yozadi_va_tahrirlaydi(self):
        self.sharh_yoz()
        self.kirish(self.usta.user)
        javob = self.client.post(self.url, {'matn': '  Rahmat!  '}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['usta_javobi'], 'Rahmat!')
        self.assertIsNotNone(javob.data['javob_vaqti'])

        self.client.post(self.url, {'matn': 'Katta rahmat!'}, format='json')
        self.assertEqual(Sharh.objects.get().usta_javobi, 'Katta rahmat!')

    def test_javob_ustaning_ommaviy_sahifasida_korinadi(self):
        self.sharh_yoz()
        services.sharhga_javob(self.ariza, matn='Rahmat!')
        javob = self.client.get(f'/api/v1/ustalar/{self.usta.pk}/sharhlar/')
        self.assertEqual(javob.data['results'][0]['usta_javobi'], 'Rahmat!')

    def test_mijoz_va_begona_usta_javob_yoza_olmaydi(self):
        self.sharh_yoz()
        self.kirish(self.mijoz)
        self.assertEqual(self.client.post(self.url, {'matn': 'x'}, format='json').status_code, 403)
        self.kirish(self.begona_usta.user)
        self.assertEqual(self.client.post(self.url, {'matn': 'x'}, format='json').status_code, 404)

    def test_sharh_yoq_bolsa_javob_yozib_bolmaydi(self):
        self.kirish(self.usta.user)
        javob = self.client.post(self.url, {'matn': 'Rahmat'}, format='json')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'sharh_yoq')

    def test_bosh_javob_qabul_qilinmaydi(self):
        self.sharh_yoz()
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(self.url, {'matn': '   '}, format='json').status_code, 400)

    def test_mijoz_sharh_yozganda_javobni_soxtalashtira_olmaydi(self):
        self.kirish(self.mijoz)
        self.client.post(f'{ARIZALAR}{self.ariza.pk}/sharh/', {'baho': 5, 'usta_javobi': 'soxta'}, format='json')
        self.assertEqual(Sharh.objects.get().usta_javobi, '')
