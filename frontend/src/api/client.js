// Backend bilan ishlash uchun yagona joy: token qo'shish, yangilash, bekor qilish va xatolarni o'qish.

const BASE = '/api/v1'
export const KALITLAR = { access: 'usta.access', refresh: 'usta.refresh' }

// Token talab qilmaydigan va eskirgan token yuborilsa 401 qaytaradigan manzillar
const OCHIQ_YOLLAR = ['/auth/login/', '/auth/register/', '/auth/refresh/', '/auth/logout/', '/auth/parol-tiklash/']

export const tokenlar = {
  get access() { return localStorage.getItem(KALITLAR.access) },
  get refresh() { return localStorage.getItem(KALITLAR.refresh) },
  saqla({ access, refresh }) {
    if (access) localStorage.setItem(KALITLAR.access, access)
    if (refresh) localStorage.setItem(KALITLAR.refresh, refresh)
  },
  tozala() {
    localStorage.removeItem(KALITLAR.access)
    localStorage.removeItem(KALITLAR.refresh)
  },
}

// Server JSON emas, HTML xato sahifasi qaytarganda foydalanuvchiga ko'rsatiladigan matn
function holatMatni(status) {
  if (status >= 500) return `Serverda xato yuz berdi (${status}). Birozdan keyin qaytadan urinib ko'ring.`
  if (status === 404) return 'Manzil topilmadi (404).'
  if (status === 403) return "Bu amal uchun ruxsat yo'q (403)."
  if (status === 400) return "Server so'rovni rad etdi (400). Backend sozlamalarini (ALLOWED_HOSTS) tekshiring."
  return `So'rov bajarilmadi (${status})`
}

export class ApiXato extends Error {
  constructor(status, data) {
    super(xatoMatni(data) || holatMatni(status))
    this.name = 'ApiXato'
    this.status = status
    this.data = data
  }
}

// DRF xatosini bitta o'qiladigan matnga aylantiradi
export function xatoMatni(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  if (Array.isArray(data)) return data.map(xatoMatni).filter(Boolean).join(' ')
  if (typeof data === 'object') return Object.values(data).map(xatoMatni).filter(Boolean).join(' ')
  return String(data)
}

// Forma uchun: maydon xatolari obyekti ({telefon: [...]}) yoki umumiy {detail}
export function formaXatolari(err) {
  if (err?.data && typeof err.data === 'object' && !Array.isArray(err.data)) return err.data
  return { detail: err?.message || "Noma'lum xato" }
}

// So'rov bekor qilinganini (sahifadan chiqib ketildi, filtr o'zgardi) oddiy xatodan ajratish uchun
export const bekorQilinganmi = (err) => err?.name === 'AbortError'

const ALOQA_YOQ = "Server bilan aloqa yo'q. Internetni tekshirib, qaytadan urinib ko'ring."

// Bir vaqtda bir nechta so'rov 401 olsa, token faqat bir marta yangilanadi
let yangilanish = null

function tokenniYangila() {
  const refresh = tokenlar.refresh
  if (!refresh) return Promise.resolve(false)
  yangilanish ??= fetch(`${BASE}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
    .then(async (javob) => {
      if (!javob.ok) return false
      tokenlar.saqla(await javob.json())
      return true
    })
    // Tarmoq uzilgan bo'lsa foydalanuvchini tizimdan chiqarmaymiz — keyinroq yana urinadi
    .catch(() => { throw new ApiXato(0, ALOQA_YOQ) })
    .finally(() => { yangilanish = null })
  return yangilanish
}

function sessiyaTugadi() {
  tokenlar.tozala()
  window.dispatchEvent(new Event('usta:chiqish'))
}

async function javobniOqi(javob) {
  const matn = javob.status === 204 ? '' : await javob.text()
  if (!matn) return null
  try {
    return JSON.parse(matn)
  } catch {
    // Javob JSON emas (Django'ning HTML xato sahifasi yoki proxy xatosi): HTML'ni foydalanuvchiga
    // ko'rsatmaymiz, xabar status kodi bo'yicha tuziladi (holatMatni)
    if (/^\s*</.test(matn)) {
      console.error(`API ${javob.status} HTML javob qaytardi:`, javob.url)
      return null
    }
    return matn.trim().slice(0, 300) || null
  }
}

export async function api(yol, { method = 'GET', body, params, signal, qaytaUrinish = true, tokenBilan = true } = {}) {
  const url = new URL(`${BASE}${yol}`, window.location.origin)
  Object.entries(params ?? {}).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) url.searchParams.set(k, v)
  })

  const ochiq = OCHIQ_YOLLAR.includes(yol)
  const access = tokenBilan && !ochiq ? tokenlar.access : null
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (access) headers.Authorization = `Bearer ${access}`

  let javob
  try {
    javob = await fetch(url, { method, headers, signal, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch (err) {
    if (bekorQilinganmi(err)) throw err
    throw new ApiXato(0, ALOQA_YOQ)
  }

  if (javob.status === 401 && access && qaytaUrinish) {
    // Access token eskirgan: yangilab, so'rovni bir marta qaytaramiz
    if (await tokenniYangila()) return api(yol, { method, body, params, signal, qaytaUrinish: false })
    // Refresh ham eskirgan: sessiya tugadi. Ochiq ma'lumot (katalog) so'ralgan bo'lsa,
    // xato ko'rsatish o'rniga tokensiz qayta so'raymiz — sahifa mehmon sifatida ishlayveradi
    sessiyaTugadi()
    return api(yol, { method, body, params, signal, qaytaUrinish: false, tokenBilan: false })
  }

  const data = await javobniOqi(javob)
  if (!javob.ok) throw new ApiXato(javob.status, data)
  return data
}
