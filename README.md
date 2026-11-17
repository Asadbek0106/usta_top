# Usta API

Ustalarni (santexnik, elektrik, kafelchi va boshqalar) topish va ularga ariza qoldirish platformasining backend qismi.
Loyiha REST API ko'rinishida yozilgan: mobil ilova yoki frontend unga HTTP orqali murojaat qiladi va JSON oladi.

## Texnologiyalar

| Qism | Texnologiya |
|---|---|
| Til / framework | Python 3.14, Django 6.1 |
| API | Django REST Framework 3.18 |
| Autentifikatsiya | JWT (`djangorestframework-simplejwt`), refresh token rotatsiyasi va blacklist |
| Filtr va qidiruv | `django-filter`, DRF `SearchFilter`, `OrderingFilter` |
| Hujjat | OpenAPI 3 (`drf-spectacular`), Swagger UI va ReDoc |
| Sozlamalar | `django-environ` (`.env` fayli, 12-Factor) |
| Testlar | `pytest`, `pytest-django`, `pytest-cov` |
| Baza | SQLite (development), PostgreSQL (production, `DATABASE_URL` orqali) |

## Imkoniyatlar

- **Telefon raqam orqali ro'yxatdan o'tish va kirish** (username yo'q). `+998 90 123-45-67` kabi yozuvlar avtomatik tozalanadi.
- **Ustalar katalogi**: shahar, kategoriya, narx va reyting bo'yicha filtr, ism/tavsif bo'yicha qidiruv, reyting bo'yicha tartiblash, sahifalash.
- **Usta profili**: bitta usta bir nechta xizmat ko'rsatadi, har biriga alohida narx va tajriba. Yangi usta admin tasdiqlagandan keyin katalogda ko'rinadi.
- **Arizalar oqimi**: mijoz ariza yuboradi → usta qabul qiladi (narxni kelishib) → usta bajarildi deb belgilaydi → mijoz sharh yozadi. Har bir bosqichda faqat ruxsat etilgan o'tishlar mumkin.
- **Reyting**: sharhlar asosida bitta SQL so'rovda hisoblanadi.
- **Admin panel**: moderatsiya (ustalarni tasdiqlash), inline xizmatlar, qidiruv va filtrlar.

## Loyiha tuzilmasi

```
usta/
├── config/
│   ├── settings/
│   │   ├── base.py        # umumiy sozlamalar
│   │   ├── dev.py         # development
│   │   ├── prod.py        # production: xavfsizlik, SMTP
│   │   └── test.py        # testlar: tez hasher, xotiradagi baza
│   ├── urls.py            # admin, Swagger, /api/v1/
│   └── api_v1.py          # API'ning 1-versiyasi URL'lari
├── apps/
│   ├── core/              # umumiy: TimeStampedModel, xatolar, pagination, filtrlar, demo_data
│   ├── accounts/          # custom User (telefon), ro'yxatdan o'tish, JWT
│   ├── ustalar/           # Shahar, Kategoriya, Usta, Xizmat
│   └── arizalar/          # Ariza, Sharh, service qatlami
├── requirements/
│   ├── base.txt           # ishlab chiqarish uchun paketlar
│   └── dev.txt            # + test paketlari
├── .env.example
└── pytest.ini
```

## Arxitektura

```
HTTP so'rov → View → Serializer → Service → Model → Baza
```

| Qatlam | Vazifasi |
|---|---|
| **View** | Faqat HTTP: autentifikatsiya, permission, javob qaytarish |
| **Serializer** | Kiruvchi ma'lumotni tekshirish va JSON'ga aylantirish |
| **Service** (`arizalar/services.py`) | Biznes mantiq: holat o'tishlari, tranzaksiya, `select_for_update` |
| **Model** | Ma'lumot, qoidalar (`OTISHLAR`, `clean()`), baza cheklovlari (`CheckConstraint`, `UniqueConstraint`) |

## Ishga tushirish (Windows, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements\dev.txt

Copy-Item .env.example .env      # keyin SECRET_KEY ni o'zgartiring
python manage.py migrate
python manage.py createsuperuser
python manage.py demo_data       # sinov ma'lumotlari (faqat DEBUG=True da)
python manage.py runserver
```

| Manzil | Nima |
|---|---|
| http://127.0.0.1:8000/ | Swagger'ga yo'naltiradi |
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/api/redoc/ | ReDoc |
| http://127.0.0.1:8000/admin/ | Admin panel |

`demo_data` yaratgan barcha foydalanuvchilarning paroli: `Demo12345!`
Ustalar: `+998900000001` … `+998900000010`, mijozlar: `+998910000001` … `+998910000005`.

## API endpoint'lari (`/api/v1/`)

### Autentifikatsiya

| Metod | URL | Tavsif |
|---|---|---|
| POST | `auth/register/` | Ro'yxatdan o'tish, javobda darhol tokenlar |
| POST | `auth/login/` | `access` va `refresh` token olish |
| POST | `auth/refresh/` | Yangi `access` token (refresh rotatsiya qilinadi) |
| POST | `auth/logout/` | Refresh tokenni bekor qilish (blacklist) |
| GET, PATCH | `auth/me/` | Mening profilim |

### Ustalar

| Metod | URL | Tavsif |
|---|---|---|
| GET | `shaharlar/`, `kategoriyalar/` | Ma'lumotnomalar |
| GET | `ustalar/` | Katalog: filtr, qidiruv, tartiblash, sahifalash |
| GET | `ustalar/{id}/` | Usta haqida batafsil (xizmatlar, narxlar, reyting) |
| GET | `ustalar/{id}/sharhlar/` | Ustaning sharhlari |
| POST | `ustalar/` | Usta bo'lib ro'yxatdan o'tish (xizmatlari bilan birga) |
| GET, PATCH | `ustalar/men/` | Ustaning o'z profili |
| GET, POST, PATCH, DELETE | `xizmatlarim/` | Ustaning o'z xizmatlari |

`ustalar/` uchun parametrlar:

| Parametr | Misol | Ma'nosi |
|---|---|---|
| `shahar` | `?shahar=1` | Shahar ID |
| `kategoriya` | `?kategoriya=santexnik` | Kategoriya slug'i |
| `narx_max` | `?narx_max=150000` | Narxi shu summagacha boshlanadigan xizmat |
| `reyting_min` | `?reyting_min=4.5` | Minimal reyting |
| `search` | `?search=alisher` | Ism, familiya, tavsif bo'yicha qidiruv |
| `ordering` | `?ordering=-sharhlar_soni` | `reyting`, `sharhlar_soni`, `yaratilgan` (`-` kamayish tartibi) |
| `page`, `page_size` | `?page=2&page_size=50` | Sahifalash (sukut 20, ko'pi bilan 100) |

`kategoriya` va `narx_max` birga berilsa, ikkala shart **bitta xizmatga** tegishli bo'lishi kerak: "santexnik xizmati 150 000 so'mgacha".
Reytingi hali yo'q ustalar tartiblash yo'nalishidan qat'i nazar ro'yxat oxirida turadi.

### Arizalar

| Metod | URL | Kim | Tavsif |
|---|---|---|---|
| GET | `arizalar/` | ishtirokchilar | Mening arizalarim. `?rol=mijoz\|usta`, `?status=...`, `?ordering=yaratilgan` |
| POST | `arizalar/` | mijoz | Ariza yuborish |
| GET | `arizalar/{id}/` | ishtirokchilar | Batafsil |
| PATCH | `arizalar/{id}/` | mijoz | Tavsif va manzilni tahrirlash (faqat "yangi" holatda) |
| POST | `arizalar/{id}/qabul/` | usta | Qabul qilish, ixtiyoriy `kelishilgan_narx` |
| POST | `arizalar/{id}/bajarildi/` | usta | Bajarildi deb belgilash |
| POST | `arizalar/{id}/bekor/` | ishtirokchilar | Bekor qilish |
| POST | `arizalar/{id}/sharh/` | mijoz | Baho (1–5) va izoh, faqat bajarilgan arizaga |

Ariza holatlari:

```
yangi ──► qabul ──► bajarildi
  │         │
  └────┬────┘
       ▼
     bekor
```

Biznes xatolari bir xil ko'rinishda qaytadi: `{"detail": "...", "code": "notogri_otish"}`.

## Testlar

```powershell
pytest                      # barcha testlar
pytest --cov                # qamrov (coverage) hisoboti bilan
pytest apps/ustalar         # faqat bitta app
```

Testlar `config/settings/test.py` bilan ishlaydi: xotiradagi SQLite va tez parol hasheri.
Shuning uchun 90 dan ortiq test bir necha soniyada o'tadi. Testlar orasida N+1 muammosidan
himoya ham bor: ro'yxatdagi yozuvlar soni oshsa ham SQL so'rovlar soni o'zgarmasligi tekshiriladi.

## Xavfsizlik bo'yicha qarorlar

- Maxfiy sozlamalar (`SECRET_KEY`, baza, SMTP) faqat `.env` faylida, u Git'ga tushmaydi.
- Parollar Django validatorlaridan o'tadi va hash ko'rinishida saqlanadi.
- Login va ro'yxatdan o'tish uchun throttling: daqiqasiga 5 ta urinish.
- Har bir foydalanuvchi faqat o'z arizalarini ko'radi; begona ariza uchun 403 emas, 404 qaytadi.
- Mijoz so'rovda boshqa `mijoz` yuborsa ham e'tiborga olinmaydi (`HiddenField` + `CurrentUserDefault`).
- Holat o'zgarishlari `select_for_update` bilan qulflanadi (race condition'dan himoya).
- `prod.py`: `DEBUG=False`, HTTPS redirect, xavfsiz cookie'lar, HSTS.
