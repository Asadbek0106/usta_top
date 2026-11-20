from apps.core.testing import BaseAPITestCase, ariza_yarat

from . import services
from .models import Ariza, Sharh

ARIZALAR = '/api/v1/arizalar/'


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
        javob = self.client.post(f'{self.url}/qabul/', {'kelishilgan_narx': '150000'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data['status'], 'qabul')
        self.assertEqual(javob.data['kelishilgan_narx'], '150000.00')

        self.assertEqual(self.client.post(f'{self.url}/bajarildi/').status_code, 200)

        self.kirish(self.mijoz)
        javob = self.client.post(f'{self.url}/sharh/', {'baho': 5, 'matn': 'Zo‘r'}, format='json')
        self.assertEqual(javob.status_code, 201, javob.data)

        javob = self.client.get(f'/api/v1/ustalar/{self.usta.pk}/')
        self.assertEqual(javob.data['reyting'], 5.0)
        self.assertEqual(javob.data['sharhlar_soni'], 1)

    def test_begona_usta_qabul_qilolmaydi(self):
        self.kirish(self.begona_usta.user)
        self.assertEqual(self.client.post(f'{self.url}/qabul/').status_code, 404)

    def test_mijoz_qabul_qilolmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.post(f'{self.url}/qabul/').status_code, 403)

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

    def test_bekor_qilingan_arizani_qabul_qilib_bolmaydi(self):
        services.bekor_qilish(self.ariza)
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/qabul/')
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data['code'], 'notogri_otish')

    def test_manfiy_kelishilgan_narx(self):
        self.kirish(self.usta.user)
        javob = self.client.post(f'{self.url}/qabul/', {'kelishilgan_narx': '-100'}, format='json')
        self.assertEqual(javob.status_code, 400)


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
        with self.assertNumQueries(2):  # COUNT + arizalar (barcha bog'lanishlar JOIN orqali)
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
