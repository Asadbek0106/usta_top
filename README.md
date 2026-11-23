# Usta

Ustalarni (santexnik, elektrik, kafelchi va boshqalar) topish va ularga ariza qoldirish platformasi. Kurs ishi.

Loyiha ikki qismdan iborat:

- **Backend** — Django REST Framework'da yozilgan REST API (`apps/`, `config/`). Frontend yoki mobil ilova unga HTTP orqali murojaat qiladi va JSON oladi.
- **Frontend** — React ilovasi (`frontend/`). Batafsil: [frontend/README.md](frontend/README.md).

Telefon raqam Telegram bot orqali tasdiqlanadi. Loyiha Docker'da ishlaydi, GitHub Actions'da avtomatik tekshiriladi va Render'ga deploy qilinadi.

## Texnologiyalar

| Qism | Texnologiya |
|---|---|
| Til / framework | Python 3.14, Django 6.1 |
| API | Django REST Framework 3.18 |
| Autentifikatsiya | JWT (`djangorestframework-simplejwt`), refresh token rotatsiyasi va blacklist |
| Telefon tasdiqlash | Telegram Bot API (webhook; lokalda polling), tashqi kutubxonasiz |
| Filtr va qidiruv | `django-filter`, DRF `SearchFilter`, `OrderingFilter` |
| Hujjat | OpenAPI 3 (`drf-spectacular`), Swagger UI va ReDoc |
| Sozlamalar | `django-environ` (`.env` fayli, 12-Factor) |
| Testlar | `pytest`, `pytest-django`, `pytest-cov`; linter `ruff` |
| Baza | SQLite (development), PostgreSQL (Docker va production, `DATABASE_URL` orqali) |
| Frontend | React 19, Vite 8, React Router 7 |
| Infratuzilma | Docker, Docker Compose, GitHub Actions (CI/CD), Render (Blueprint) |

## Imkoniyatlar

**Mijoz uchun**

- **Telefon raqam bilan ro'yxatdan o'tish va kirish** (username yo'q). `+998 90 123-45-67` kabi yozuvlar avtomatik tozalanadi. Bot sozlangan bo'lsa, raqam Telegram orqali tasdiqlanadi: bot 6 xonali kod beradi.
- **Parolni tiklash.** Ro'yxatdan o'tgan raqam botga yuborilsa, bot parolni tiklash kodini beradi. Yangi parol o'rnatilgach, boshqa qurilmalardagi barcha sessiyalar yopiladi.
- **Ustalar katalogi**: shahar, kategoriya, narx va reyting bo'yicha filtr, ism yoki tavsif bo'yicha qidiruv. Saralash: reyting, sharhlar soni, eng arzon narx, tajriba yoki yangilari birinchi. Ro'yxat sahifalarga bo'linadi.
- **Sevimli ustalar**: yoqqan ustani saqlab qo'yish va keyin "Sevimlilar" sahifasidan topish.
- **Arizalar**: mijoz ariza yuboradi → usta narxni kelishib qabul qiladi → usta bajarildi deb belgilaydi → mijoz baho (1–5) va sharh qoldiradi. Har bir bosqichda faqat ruxsat etilgan o'tishlar mumkin.
- **Ariza tarixi**: arizaning har bir holat o'zgarishi saqlanadi (kim, qachon, qaysi holatdan qaysiga). Frontend'da u vaqt chizig'i ko'rinishida chiqadi.

**Usta uchun**

- **Usta profili**: bitta usta bir nechta xizmat ko'rsatadi, har biriga alohida narx va tajriba. Yangi usta admin tasdiqlagandan keyin katalogda ko'rinadi.
- **Shaxsiy statistika**: jami arizalar, bajarilganlar, daromad (bajarilgan arizalarning kelishilgan narxlari), bajarish ulushi. Bundan tashqari oxirgi 6 oy bo'yicha grafik, baholar taqsimoti va eng ko'p so'ralgan xizmatlar.
- **Sharhga javob**: usta mijoz sharhiga ochiq javob yozadi. Javob ustaning sahifasida sharh ostida ko'rinadi.

**Admin uchun**

- **Admin panel**: ustalarni tasdiqlash (moderatsiya), inline xizmatlar, ariza tarixi (faqat o'qish uchun), sevimlilar, tasdiqlash kodlari, qidiruv va filtrlar.

## Loyiha tuzilmasi

```
usta/
├── config/
│   ├── settings/
│   │   ├── base.py        # umumiy sozlamalar
│   │   ├── dev.py         # development
│   │   ├── prod.py        # production: xavfsizlik, SMTP, Render domeni
│   │   └── test.py        # testlar: tez hasher, xotiradagi baza
│   ├── urls.py            # admin, Swagger, /health/, /api/v1/
│   └── api_v1.py          # API'ning 1-versiyasi URL'lari
├── apps/
│   ├── core/              # TimeStampedModel, xatolar, pagination, filtrlar, demo_data, ensure_superuser
│   ├── accounts/          # custom User (telefon), JWT, Telegram bot, parolni tiklash
│   ├── ustalar/           # Shahar, Kategoriya, Usta, Xizmat, Sevimli; statistika (services.py)
│   └── arizalar/          # Ariza, ArizaTarixi, Sharh; holat o'tishlari (services.py)
├── frontend/              # React ilovasi (alohida README)
├── requirements/
│   ├── base.txt           # ishlab chiqarish uchun paketlar
│   └── dev.txt            # + test va lint paketlari
├── .github/workflows/     # CI/CD: lint, testlar, Docker image
├── Dockerfile             # production image (multi-stage)
├── docker-compose.yml     # lokal muhit: PostgreSQL + Django + Vite
├── render.yaml            # Render Blueprint: API, frontend va baza
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
| **Service** (`arizalar/services.py`, `ustalar/services.py`) | Biznes mantiq: holat o'tishlari va ularning tarixi, tranzaksiya, `select_for_update`, statistika hisob-kitobi |
| **Model** | Ma'lumot, qoidalar (`OTISHLAR`, `clean()`), baza cheklovlari (`CheckConstraint`, `UniqueConstraint`) |

Reyting, eng arzon narx va tajriba katalog so'rovining o'zida (annotate va subquery bilan) hisoblanadi. Ustalar soni qancha bo'lmasin, ro'yxat 3 ta SQL so'rov bilan olinadi.

## Ishga tushirish (Windows, PowerShell)

### Backend

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
| http://127.0.0.1:8000/health/ | Server va baza holati (monitoring uchun) |

`demo_data` buyrug'i 10 ta usta, 5 ta mijoz va oxirgi 6 oyga tarqatilgan 40 ta ariza yaratadi (tarixi, sharhlari va usta javoblari bilan). Barcha foydalanuvchilarning paroli: `Demo12345!`.
Ustalar: `+998900000001` … `+998900000010`, mijozlar: `+998910000001` … `+998910000005`.

### Frontend

Backend ishlab turgan holda, alohida terminalda:

```powershell
cd frontend
npm install
npm run dev
```

Brauzerda: http://localhost:5173. Vite `/api` so'rovlarini Django'ga yo'naltiradi, shuning uchun CORS sozlash shart emas.

### Telegram bot (ixtiyoriy)

Token berilmasa, ro'yxatdan o'tish kodsiz ishlaydi, parolni tiklash esa o'chiq turadi.

1. [@BotFather](https://t.me/BotFather) da bot yarating va `.env` fayliga yozing:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_BOT_USERNAME=usta_test_bot
   ```
2. Lokal kompyuterda botni polling rejimida ishga tushiring (ochiq HTTPS manzil kerak emas):
   ```powershell
   python manage.py telegram_polling
   ```

Serverda (Render) bot webhook orqali ishlaydi: `set_telegram_webhook` buyrug'i har deploy'da manzilni o'zi o'rnatadi. Lokal sinov uchun alohida test bot ishlating, aks holda polling serverdagi webhook'ni uzib qo'yadi.

## API endpoint'lari (`/api/v1/`)

To'liq va doim yangi hujjat Swagger'da: `/api/docs/`.

### Autentifikatsiya

| Metod | URL | Tavsif |
|---|---|---|
| POST | `auth/register/` | Ro'yxatdan o'tish (bot yoqilgan bo'lsa `kod` majburiy), javobda darhol tokenlar |
| POST | `auth/login/` | `access` va `refresh` token olish |
| POST | `auth/refresh/` | Yangi `access` token (refresh rotatsiya qilinadi) |
| POST | `auth/logout/` | Refresh tokenni bekor qilish (blacklist) |
| GET, PATCH | `auth/me/` | Mening profilim |
| POST | `auth/parol-tiklash/` | Bot bergan kod bilan yangi parol o'rnatish: `telefon`, `kod`, `password`, `password2` |
| GET | `auth/telegram/` | Frontend uchun: kod kerakmi va bot havolasi |
| POST | `auth/telegram/webhook/` | Faqat Telegram uchun (maxfiy kalit bilan himoyalangan) |

### Ustalar

| Metod | URL | Kim | Tavsif |
|---|---|---|---|
| GET | `shaharlar/`, `kategoriyalar/` | hamma | Ma'lumotnomalar |
| GET | `ustalar/` | hamma | Katalog: filtr, qidiruv, saralash, sahifalash |
| GET | `ustalar/{id}/` | hamma | Usta haqida batafsil (xizmatlar, narxlar, reyting) |
| GET | `ustalar/{id}/sharhlar/` | hamma | Ustaning sharhlari va unga yozilgan javoblar |
| POST, DELETE | `ustalar/{id}/sevimli/` | foydalanuvchi | Sevimlilarga qo'shish / olib tashlash |
| GET | `ustalar/sevimlilar/` | foydalanuvchi | Mening sevimli ustalarim |
| POST | `ustalar/` | foydalanuvchi | Usta bo'lib ro'yxatdan o'tish (xizmatlari bilan birga) |
| GET, PATCH | `ustalar/men/` | usta | Ustaning o'z profili |
| GET | `ustalar/men/statistika/` | usta | Arizalar, daromad, oylar bo'yicha statistika, baholar |
| GET, POST, PATCH, DELETE | `xizmatlarim/` | usta | Ustaning o'z xizmatlari |

Kirgan foydalanuvchi uchun katalog javobida har bir ustada `sevimli: true/false` maydoni bor.

`ustalar/` uchun parametrlar:

| Parametr | Misol | Ma'nosi |
|---|---|---|
| `shahar` | `?shahar=1` | Shahar ID |
| `kategoriya` | `?kategoriya=santexnik` | Kategoriya slug'i |
| `narx_max` | `?narx_max=150000` | Narxi shu summagacha boshlanadigan xizmat |
| `reyting_min` | `?reyting_min=4.5` | Minimal reyting |
| `search` | `?search=alisher` | Ism, familiya, tavsif bo'yicha qidiruv |
| `ordering` | `?ordering=eng_arzon` | `reyting`, `sharhlar_soni`, `eng_arzon`, `tajriba_yil`, `yaratilgan` (`-` — kamayish tartibi) |
| `page`, `page_size` | `?page=2&page_size=50` | Sahifalash (sukut 20, ko'pi bilan 100) |

`kategoriya` va `narx_max` birga berilsa, ikkala shart **bitta xizmatga** tegishli bo'lishi kerak: "santexnik xizmati 150 000 so'mgacha".
Reytingi hali yo'q ustalar tartiblash yo'nalishidan qat'i nazar ro'yxat oxirida turadi.

### Arizalar

| Metod | URL | Kim | Tavsif |
|---|---|---|---|
| GET | `arizalar/` | ishtirokchilar | Mening arizalarim (har biri tarixi bilan). `?rol=mijoz\|usta`, `?status=...`, `?ordering=yaratilgan` |
| POST | `arizalar/` | mijoz | Ariza yuborish |
| GET | `arizalar/{id}/` | ishtirokchilar | Batafsil |
| PATCH | `arizalar/{id}/` | mijoz | Tavsif va manzilni tahrirlash (faqat "yangi" holatda) |
| POST | `arizalar/{id}/qabul/` | usta | Qabul qilish, ixtiyoriy `kelishilgan_narx` |
| POST | `arizalar/{id}/bajarildi/` | usta | Bajarildi deb belgilash |
| POST | `arizalar/{id}/bekor/` | ishtirokchilar | Bekor qilish |
| POST | `arizalar/{id}/sharh/` | mijoz | Baho (1–5) va izoh, faqat bajarilgan arizaga |
| POST | `arizalar/{id}/sharh/javob/` | usta | Sharhga javob yozish yoki uni tahrirlash |

Ariza holatlari:

```
yangi ──► qabul ──► bajarildi
  │         │
  └────┬────┘
       ▼
     bekor
```

Har bir o'tish `ArizaTarixi` jadvaliga yoziladi. Rad etilgan (ruxsat etilmagan) o'tish tarixga tushmaydi.

Biznes xatolari bir xil ko'rinishda qaytadi: `{"detail": "...", "code": "notogri_otish"}`.

## Testlar

```powershell
pytest                      # barcha testlar
pytest --cov                # qamrov (coverage) hisoboti bilan
pytest apps/ustalar         # faqat bitta app
ruff check .                # linter

cd frontend
npm run lint                # ESLint
npm run build               # production build
```

Testlar `config/settings/test.py` bilan ishlaydi: xotiradagi SQLite va tez parol hasheri. Shuning uchun 150 dan ortiq test bir necha soniyada o'tadi. Telegram'ga haqiqiy so'rov yuborilmaydi: bot funksiyalari mock bilan tekshiriladi.

Testlar orasida N+1 muammosidan himoya ham bor: ro'yxatdagi yozuvlar soni oshsa ham SQL so'rovlar soni o'zgarmasligi tekshiriladi.

## Xavfsizlik bo'yicha qarorlar

- Maxfiy sozlamalar (`SECRET_KEY`, baza, SMTP, bot tokeni) faqat `.env` faylida turadi, u Git'ga tushmaydi.
- Parollar Django validatorlaridan o'tadi va hash ko'rinishida saqlanadi.
- Login, ro'yxatdan o'tish va parolni tiklash uchun throttling bor: daqiqasiga 5 ta urinish. Ariza yuborish soatiga 20 ta bilan cheklangan.
- Telegram kodlari:
  - bot faqat foydalanuvchining **o'z** kontaktini qabul qiladi;
  - kod 10 daqiqa amal qiladi, 5 ta xato urinishdan keyin bekor bo'ladi;
  - bitta chatdan 10 daqiqada ko'pi bilan 3 ta kod so'rash mumkin;
  - ro'yxatdan o'tish va parolni tiklash kodlari bir-birining o'rniga ishlamaydi.
- Webhook so'rovlari maxfiy kalit bilan tekshiriladi: begona odam botning o'rniga soxta xabar yubora olmaydi.
- Parol tiklangach, foydalanuvchining barcha refresh tokenlari bekor qilinadi.
- Har bir foydalanuvchi faqat o'z arizalarini ko'radi; begona ariza uchun 403 emas, 404 qaytadi.
- Mijoz so'rovda boshqa `mijoz` yuborsa ham e'tiborga olinmaydi (`HiddenField` + `CurrentUserDefault`). Usta javobini faqat ustaning o'zi yoza oladi.
- Holat o'zgarishlari `select_for_update` bilan qulflanadi (race condition'dan himoya).
- `prod.py`: `DEBUG=False`, HTTPS redirect, xavfsiz cookie'lar, HSTS.

## Docker bilan ishga tushirish

Kerak: Docker Desktop.

```powershell
docker compose up --build
```

Bu buyruq uchta servisni ko'taradi:

| Servis | Nima | Port |
|---|---|---|
| `db` | PostgreSQL 17, ma'lumotlar `postgres_data` volume'ida saqlanadi | 5433 (ichkarida 5432) |
| `web` | Django + gunicorn (3 worker), ishga tushganda migratsiyalarni o'zi qo'llaydi | 8000 |
| `frontend` | Vite development serveri, `/api` so'rovlarini `web` ga yo'naltiradi | 5173 |

`web` faqat baza tayyor bo'lgandan keyin ishga tushadi (`healthcheck` + `depends_on`).

Sinov ma'lumotlari va admin:

```powershell
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.dev -e DEBUG=True web python manage.py demo_data
docker compose exec web python manage.py createsuperuser
```

Foydali buyruqlar:

| Buyruq | Vazifasi |
|---|---|
| `docker compose ps` | Servislar holati (`healthy` bo'lishi kerak) |
| `docker compose logs -f web` | Django loglari |
| `docker compose down` | To'xtatish (ma'lumotlar saqlanadi) |
| `docker compose down -v` | To'xtatish va bazani butunlay tozalash |

## CI/CD (GitHub Actions)

`.github/workflows/django-ci.yml` `master` ga har bir push va pull request'da ishlaydi:

1. **Frontend** — `npm ci`, ESLint, production build.
2. **Lint** — `ruff check .`
3. **Testlar** — haqiqiy PostgreSQL bilan:
   - `manage.py check`;
   - yozilmay qolgan migratsiya yo'qligini tekshirish;
   - migratsiyalarni qo'llash;
   - OpenAPI sxemasini tekshirish;
   - `pytest --cov`.
4. **Docker** — image'ni qurish va uni smoke test qilish (`/health/` javob beradimi). `master` ga push bo'lganda image GitHub Container Registry'ga yuklanadi.

## Deploy (Render)

`render.yaml` (Blueprint) bitta fayl orqali uchta servis yaratadi:

| Servis | Nima |
|---|---|
| `usta-api` | Django (Docker). Ishga tushganda `migrate`, `ensure_superuser` va `set_telegram_webhook` buyruqlarini o'zi bajaradi |
| `usta-frontend` | React (statik sayt). `/api/*` so'rovlari `usta-api` ga yo'naltiriladi |
| `usta-db` | PostgreSQL |

Birinchi marta: Render Dashboard → **New → Blueprint** → repozitoriyni tanlang. Keyin `usta-api` ning **Environment** bo'limida quyidagilarni qo'shing:

| O'zgaruvchi | Nima uchun |
|---|---|
| `DJANGO_SUPERUSER_TELEFON`, `DJANGO_SUPERUSER_PASSWORD` | Admin akkaunti avtomatik yaratilishi uchun |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` | Telefon tasdiqlash va parolni tiklash uchun |

Keyingi safar `master` ga push qilish kifoya: Render avtomatik deploy qiladi va yangi migratsiyalarni qo'llaydi.

Bepul rejaning cheklovlari:

- server 15 daqiqa so'rov kelmasa uxlab qoladi, keyingi birinchi so'rov sekinroq javob beradi;
- bepul PostgreSQL bazasi yaratilganidan 30 kun o'tib o'chiriladi;
- server diskiga yozilgan fayllar qayta ishga tushganda yo'qoladi.
