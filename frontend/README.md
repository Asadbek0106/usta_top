# Usta — frontend

Usta API uchun React ilovasi: ustalar katalogi, usta sahifasi, ariza yuborish, arizalar bilan ishlash (tarixi bilan), sevimli ustalar, parolni tiklash, usta profili va statistikasi.

## Texnologiyalar

| Qism | Texnologiya |
|---|---|
| UI | React 19 |
| Yig'uvchi (bundler) | Vite 8 |
| Marshrutlar | React Router 7 |
| Shriftlar | Unbounded (sarlavhalar), Golos Text (matn) — `@fontsource` orqali loyiha ichida |

## Ishga tushirish

Kerak: Node.js 20 yoki undan yangi. Backend `http://127.0.0.1:8000` da ishlab turgan bo'lishi kerak.

```powershell
cd frontend
npm install
npm run dev
```

Brauzerda: http://localhost:5173

`vite.config.js` dagi proxy `/api` so'rovlarini Django'ga yo'naltiradi, shuning uchun backend'da CORS sozlash shart emas.

| Buyruq | Vazifasi |
|---|---|
| `npm run dev` | Development serveri, kod o'zgarsa sahifa o'zi yangilanadi |
| `npm run build` | Production uchun `dist/` papkasiga yig'ish |
| `npm run preview` | Yig'ilgan versiyani lokal ko'rish |
| `npm run lint` | ESLint (React hooks qoidalari bilan) |

## Tuzilma

```
src/
├── api/client.js          # fetch o'rami: JWT qo'shish, 401 da tokenni yangilash, xatolarni o'qish
├── auth/
│   ├── AuthContext.jsx    # kirish, ro'yxatdan o'tish, chiqish, joriy foydalanuvchi
│   └── Himoyalangan.jsx   # faqat tizimga kirganlar (yoki faqat ustalar) uchun sahifalar
├── components/            # Layout, Reyting, Sahifalash, Maydon, StatusBelgi, utils
│   ├── Statistika.jsx     # ustaning statistikasi: raqamlar, oylar grafigi, baholar
│   ├── SevimliTugma.jsx   # ♡ tugmasi (optimistik yangilanish)
│   └── UstaJavobi.jsx     # sharh ostidagi usta javobi
├── pages/
│   ├── Katalog.jsx        # ustalar: kategoriya, shahar, narx, reyting, qidiruv, saralash
│   ├── UstaSahifasi.jsx   # xizmatlar, sharhlar va javoblar, ariza formasi
│   ├── Arizalarim.jsx     # qabul / bajarildi / bekor qilish, tarix, sharh va unga javob
│   ├── Sevimlilar.jsx     # saqlangan ustalar
│   ├── UstaBolish.jsx     # usta profilini yaratish
│   ├── UstaProfilim.jsx   # statistika, profilni tahrirlash, xizmatlarni boshqarish
│   ├── ParolTiklash.jsx   # Telegram bot kodi bilan yangi parol
│   ├── Kirish.jsx, RoyxatdanOtish.jsx, Topilmadi.jsx
├── App.jsx                # marshrutlar
└── styles.css             # dizayn tizimi
```

## Muhim qarorlar

- **Token yangilash.** Access token eskirsa (401), `client.js` refresh token bilan yangisini oladi va so'rovni bir marta qaytaradi. Bir vaqtda bir nechta so'rov 401 olsa ham, token faqat bir marta yangilanadi.
- **Filtrlar URL'da saqlanadi** (`/?kategoriya=santexnik&shahar=1`). Sahifani yangilasangiz yoki havolani ulashsangiz, filtr saqlanib qoladi.
- **Backend xatolari maydon yonida ko'rsatiladi.** DRF qaytargan `{"telefon": ["..."]}` ko'rinishidagi xatolar tegishli maydon ostiga chiqadi.
- **Dizayn:** ish kiyimi indigosi va xavfsizlik jileti sariq rangi. Sariq faqat reyting va asosiy tugma uchun ishlatiladi.

## Arxitektura qarorlari

- **`api/client.js`** — yagona so'rov qatlami. Access token eskirsa bir marta yangilanadi (parallel so'rovlar bitta
  refresh'ni kutadi). Refresh ham eskirgan bo'lsa sessiya tozalanadi va ochiq ma'lumot (katalog) **tokensiz qayta
  so'raladi** — foydalanuvchi bir haftadan keyin qaytsa ham sahifa buzilmaydi. Login/register/logout so'rovlariga
  eski token qo'shilmaydi.
- **`hooks/useSorov.js`** — GET so'rovlar uchun hook: filtr o'zgarsa eski so'rov `AbortController` bilan bekor
  qilinadi (race condition yo'q), qayta yuklashda eski natija xiralashib turadi, xato bo'lsa "Qayta urinish" tugmasi.
- **`AuthContext`** — server vaqtincha ishlamasa foydalanuvchi tizimdan chiqarilmaydi (faqat 401/403 da);
  boshqa tabda kirish/chiqish shu tabga ham ta'sir qiladi (`storage` hodisasi).
- **Kod bo'lish (code splitting)** — bosh sahifadan boshqa sahifalar `React.lazy` bilan alohida yuklanadi.
- **Xatolarga chidamlilik** — `XatoChegarasi` (error boundary) render xatosida oq ekran o'rniga xabar ko'rsatadi.
- **Qulaylik (a11y)** — "Asosiy qismga o'tish" havolasi, har sahifada `document.title`, sahifa almashganda fokus
  `<main>` ga o'tadi, forma xatolari `aria-invalid` / `aria-describedby` orqali maydonga bog'langan.
- **Formalar** — oddiy xatolar (bo'sh maydon, parollar mos emas) serverga bormasdan ko'rsatiladi, ikki marta
  yuborishdan himoya bor, 429 (juda ko'p urinish) uchun tushunarli xabar.
