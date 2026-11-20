from apps.arizalar.models import Ariza, Sharh
from apps.core.testing import (
    BaseAPITestCase,
    ariza_yarat,
    foydalanuvchi_yarat,
    usta_yarat,
)

from .models import Kategoriya, Usta, Xizmat

USTALAR = '/api/v1/ustalar/'
MEN = '/api/v1/ustalar/men/'
XIZMATLARIM = '/api/v1/xizmatlarim/'


class UstaRoyxatiTest(BaseAPITestCase):
    def test_mehmon_ustalarni_kora_oladi(self):
        javob = self.client.get(USTALAR)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data['count'], 2)

    def test_tasdiqlanmagan_usta_korinmaydi(self):
        usta_yarat('+998900000009', shahar=self.shahar, kategoriyalar=[self.santexnik], tasdiqlangan=False)
        self.assertEqual(self.client.get(USTALAR).data['count'], 2)

    def test_bloklangan_usta_korinmaydi(self):
        self.begona_usta.user.is_active = False
        self.begona_usta.user.save()
        self.assertEqual(self.client.get(USTALAR).data['count'], 1)

    def test_batafsil_sahifada_xizmatlar_va_reyting(self):
        ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                            status=Ariza.Status.BAJARILDI)
        Sharh.objects.create(ariza=ariza, baho=4)
        ariza2 = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                             status=Ariza.Status.BAJARILDI)
        Sharh.objects.create(ariza=ariza2, baho=5)

        javob = self.client.get(f'{USTALAR}{self.usta.pk}/')
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data['reyting'], 4.5)
        self.assertEqual(javob.data['sharhlar_soni'], 2)
        self.assertEqual(len(javob.data['xizmatlar']), 1)

    def test_bir_xil_baholar_ham_togri_sanaladi(self):
        for _ in range(3):
            ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                                status=Ariza.Status.BAJARILDI)
            Sharh.objects.create(ariza=ariza, baho=5)
        javob = self.client.get(f'{USTALAR}{self.usta.pk}/')
        self.assertEqual(javob.data['sharhlar_soni'], 3)

    def test_usta_sharhlari(self):
        ariza = ariza_yarat(mijoz=self.mijoz, usta=self.usta, kategoriya=self.santexnik,
                            status=Ariza.Status.BAJARILDI)
        Sharh.objects.create(ariza=ariza, baho=5, matn='Zo‘r')
        javob = self.client.get(f'{USTALAR}{self.usta.pk}/sharhlar/')
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data['count'], 1)
        self.assertEqual(self.client.get(f'{USTALAR}{self.begona_usta.pk}/sharhlar/').data['results'], [])

    def test_faqat_faol_kategoriyalar(self):
        Kategoriya.objects.create(nomi='Eski', slug='eski', faol=False)
        javob = self.client.get('/api/v1/kategoriyalar/')
        self.assertEqual(len(javob.data), 2)


class UstaProfiliYaratishTest(BaseAPITestCase):
    def malumot(self, **kwargs):
        return {
            'shahar': self.shahar.pk,
            'tavsif': 'Tajribali usta',
            'xizmatlar': [{'kategoriya_id': self.elektrik.pk, 'narx_dan': '80000', 'tajriba': 3}],
            **kwargs,
        }

    def test_foydalanuvchi_usta_bolishi(self):
        self.kirish(self.mijoz)
        javob = self.client.post(USTALAR, self.malumot(), format='json')
        self.assertEqual(javob.status_code, 201, javob.data)
        usta = Usta.objects.get(user=self.mijoz)
        self.assertFalse(usta.tasdiqlangan)  # admin tasdiqlamaguncha ko'rinmaydi
        self.assertEqual(usta.xizmatlar.count(), 1)

    def test_mehmon_usta_bololmaydi(self):
        self.assertEqual(self.client.post(USTALAR, self.malumot(), format='json').status_code, 401)

    def test_ikkinchi_profil_yaratib_bolmaydi(self):
        self.kirish(self.usta.user)
        self.assertEqual(self.client.post(USTALAR, self.malumot(), format='json').status_code, 400)

    def test_xizmatsiz_profil_yaratib_bolmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.post(USTALAR, self.malumot(xizmatlar=[]), format='json').status_code, 400)

    def test_bir_kategoriya_ikki_marta(self):
        self.kirish(self.mijoz)
        xizmat = {'kategoriya_id': self.elektrik.pk, 'narx_dan': '80000', 'tajriba': 3}
        javob = self.client.post(USTALAR, self.malumot(xizmatlar=[xizmat, xizmat]), format='json')
        self.assertEqual(javob.status_code, 400)

    def test_ozini_ozi_tasdiqlab_bolmaydi(self):
        self.kirish(self.mijoz)
        self.client.post(USTALAR, self.malumot(tasdiqlangan=True), format='json')
        self.assertFalse(Usta.objects.get(user=self.mijoz).tasdiqlangan)


class MenProfilimTest(BaseAPITestCase):
    def test_usta_oz_profilini_koradi(self):
        self.kirish(self.usta.user)
        javob = self.client.get(MEN)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data['id'], self.usta.pk)

    def test_oddiy_foydalanuvchi_kirolmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.get(MEN).status_code, 403)

    def test_usta_profilini_tahrirlaydi(self):
        self.kirish(self.usta.user)
        javob = self.client.patch(MEN, {'tavsif': 'Yangi tavsif', 'shahar': self.shahar2.pk}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.usta.refresh_from_db()
        self.assertEqual(self.usta.tavsif, 'Yangi tavsif')
        self.assertEqual(self.usta.shahar, self.shahar2)

    def test_tahrirlashda_tasdiqlangan_ozgarmaydi(self):
        usta = usta_yarat('+998900000009', shahar=self.shahar, kategoriyalar=[self.santexnik], tasdiqlangan=False)
        self.kirish(usta.user)
        self.client.patch(MEN, {'tasdiqlangan': True}, format='json')
        usta.refresh_from_db()
        self.assertFalse(usta.tasdiqlangan)

    def test_mijoz_tahrirlay_olmaydi(self):
        self.kirish(self.mijoz)
        self.assertEqual(self.client.patch(MEN, {'tavsif': 'x'}, format='json').status_code, 403)


class XizmatlarimTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.xizmat = self.usta.xizmatlar.get()
        self.kirish(self.usta.user)

    def test_faqat_oz_xizmatlarini_koradi(self):
        javob = self.client.get(XIZMATLARIM)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual([x['id'] for x in javob.data], [self.xizmat.pk])

    def test_yangi_xizmat_qoshish(self):
        javob = self.client.post(XIZMATLARIM, {'kategoriya_id': self.elektrik.pk, 'narx_dan': '90000',
                                               'tajriba': 2}, format='json')
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(self.usta.xizmatlar.count(), 2)

    def test_bir_kategoriyani_ikki_marta_qoshib_bolmaydi(self):
        javob = self.client.post(XIZMATLARIM, {'kategoriya_id': self.santexnik.pk, 'narx_dan': '1000',
                                               'tajriba': 1}, format='json')
        self.assertEqual(javob.status_code, 400)

    def test_manfiy_narx(self):
        javob = self.client.post(XIZMATLARIM, {'kategoriya_id': self.elektrik.pk, 'narx_dan': '-5',
                                               'tajriba': 1}, format='json')
        self.assertEqual(javob.status_code, 400)

    def test_narxni_ozgartirish(self):
        javob = self.client.patch(f'{XIZMATLARIM}{self.xizmat.pk}/', {'narx_dan': '250000'}, format='json')
        self.assertEqual(javob.status_code, 200, javob.data)
        self.xizmat.refresh_from_db()
        self.assertEqual(self.xizmat.narx_dan, 250000)

    def test_begona_xizmatni_ozgartirib_bolmaydi(self):
        begona = self.begona_usta.xizmatlar.get()
        javob = self.client.patch(f'{XIZMATLARIM}{begona.pk}/', {'narx_dan': '1'}, format='json')
        self.assertEqual(javob.status_code, 404)

    def test_xizmatni_ochirish(self):
        yangi = Xizmat.objects.create(usta=self.usta, kategoriya=self.elektrik, narx_dan=1000)
        self.assertEqual(self.client.delete(f'{XIZMATLARIM}{yangi.pk}/').status_code, 204)
        self.assertFalse(Xizmat.objects.filter(pk=yangi.pk).exists())

    def test_oxirgi_xizmatni_ochirib_bolmaydi(self):
        javob = self.client.delete(f'{XIZMATLARIM}{self.xizmat.pk}/')
        self.assertEqual(javob.status_code, 400)
        self.assertTrue(Xizmat.objects.filter(pk=self.xizmat.pk).exists())

    def test_usta_bolmagan_foydalanuvchi(self):
        self.kirish(foydalanuvchi_yarat('+998930000000'))
        self.assertEqual(self.client.get(XIZMATLARIM).status_code, 403)


class UstaFiltrVaTartibTest(BaseAPITestCase):
    """9-etap: filtr, qidiruv, tartiblash, sahifalash va so'rovlar soni."""

    def setUp(self):
        super().setUp()
        # self.usta va self.begona_usta: Toshkent, santexnik 100 000 so'mdan
        self.elektrik_usta = usta_yarat(
            '+998900000003', shahar=self.shahar2, kategoriyalar=[self.elektrik], narx=300000,
        )
        Xizmat.objects.create(usta=self.elektrik_usta, kategoriya=self.santexnik, narx_dan=500000)

    def idlar(self, javob):
        self.assertEqual(javob.status_code, 200, javob.data)
        return [u['id'] for u in javob.data['results']]

    def sharh_qoldir(self, usta, baho):
        ariza = ariza_yarat(mijoz=self.mijoz, usta=usta, kategoriya=usta.kategoriyalar.first(),
                            status=Ariza.Status.BAJARILDI)
        Sharh.objects.create(ariza=ariza, baho=baho)

    def test_shahar_boyicha(self):
        javob = self.client.get(USTALAR, {'shahar': self.shahar2.pk})
        self.assertEqual(self.idlar(javob), [self.elektrik_usta.pk])

    def test_kategoriya_boyicha(self):
        self.assertEqual(self.idlar(self.client.get(USTALAR, {'kategoriya': 'elektrik'})), [self.elektrik_usta.pk])
        self.assertEqual(len(self.idlar(self.client.get(USTALAR, {'kategoriya': 'santexnik'}))), 3)

    def test_narx_boyicha(self):
        idlar = self.idlar(self.client.get(USTALAR, {'narx_max': 150000}))
        self.assertCountEqual(idlar, [self.usta.pk, self.begona_usta.pk])

    def test_kategoriya_va_narx_bitta_xizmatga_tegishli(self):
        # elektrik_usta: elektrik 300 000 (arzon), santexnik 500 000 (qimmat).
        # "350 000 gacha santexnik" so'ralganda u chiqmasligi kerak.
        idlar = self.idlar(self.client.get(USTALAR, {'kategoriya': 'santexnik', 'narx_max': 350000}))
        self.assertCountEqual(idlar, [self.usta.pk, self.begona_usta.pk])

    def test_minimal_reyting(self):
        self.sharh_qoldir(self.usta, 5)
        self.sharh_qoldir(self.begona_usta, 3)
        self.assertEqual(self.idlar(self.client.get(USTALAR, {'reyting_min': 4})), [self.usta.pk])

    def test_notogri_filtr_qiymati_400(self):
        self.assertEqual(self.client.get(USTALAR, {'reyting_min': 'abc'}).status_code, 400)

    def test_qidiruv(self):
        self.usta.user.first_name = 'Alisher'
        self.usta.user.save()
        self.assertEqual(self.idlar(self.client.get(USTALAR, {'search': 'alish'})), [self.usta.pk])

    def test_sukut_boyicha_reyting_kamayishi_va_reytingsizlar_oxirida(self):
        self.sharh_qoldir(self.usta, 5)
        self.sharh_qoldir(self.begona_usta, 3)
        self.assertEqual(
            self.idlar(self.client.get(USTALAR)),
            [self.usta.pk, self.begona_usta.pk, self.elektrik_usta.pk],
        )

    def test_osish_tartibida_ham_reytingsizlar_oxirida(self):
        self.sharh_qoldir(self.usta, 5)
        self.sharh_qoldir(self.begona_usta, 3)
        self.assertEqual(
            self.idlar(self.client.get(USTALAR, {'ordering': 'reyting'})),
            [self.begona_usta.pk, self.usta.pk, self.elektrik_usta.pk],
        )

    def test_sahifalash(self):
        javob = self.client.get(USTALAR, {'page_size': 2})
        self.assertEqual(javob.data['count'], 3)
        self.assertEqual(len(javob.data['results']), 2)
        self.assertIsNotNone(javob.data['next'])

        ikkinchi = self.client.get(USTALAR, {'page_size': 2, 'page': 2})
        self.assertEqual(len(ikkinchi.data['results']), 1)
        self.assertIsNone(ikkinchi.data['next'])

    def test_mavjud_bolmagan_sahifa_404(self):
        self.assertEqual(self.client.get(USTALAR, {'page': 99}).status_code, 404)

    def test_royxat_sorovlar_soni_ustalar_soniga_bogliq_emas(self):
        # N+1 muammosidan himoya: 3 ta usta bo'lsa ham, 13 ta bo'lsa ham so'rovlar soni bir xil.
        for i in range(10):
            usta_yarat(f'+99890100{i:04d}', shahar=self.shahar, kategoriyalar=[self.santexnik, self.elektrik])
        with self.assertNumQueries(3):  # COUNT + ustalar (JOIN) + kategoriyalar (prefetch)
            javob = self.client.get(USTALAR)
        self.assertEqual(javob.data['count'], 13)
