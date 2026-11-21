import { useEffect, useState } from 'react'

import { api } from '../api/client'

// Brauzerlar o'zbek tilini to'liq qo'llab-quvvatlamaydi ("150,000", "2026 M11 21"),
// shuning uchun format qo'lda yoziladi: 150 000 so'm, 21-noyabr, 2026
export const somda = (qiymat) => {
  if (qiymat === null || qiymat === undefined || qiymat === '') return '—'
  const son = Number(qiymat)
  if (!Number.isFinite(son)) return '—'
  // \u00a0 — bo'linmas bo'sh joy: "150 000" ikki qatorga bo'linib ketmaydi
  return `${Math.round(son).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0')}\u00a0so'm`
}

const OYLAR = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr']

export const sana = (iso) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getDate()}-${OYLAR[d.getMonth()]}, ${d.getFullYear()}`
}

// Kirishdan keyin faqat ilova ichidagi manzilga qaytaramiz ("//boshqa-sayt.uz" kabi ochiq yo'naltirish yo'q)
export const xavfsizManzil = (m) => (typeof m === 'string' && m.startsWith('/') && !m.startsWith('//') ? m : '/')

// Shaharlar va kategoriyalar kam o'zgaradi: bir marta yuklab, sahifalar orasida qayta ishlatamiz.
// Keshda javobning o'zi emas, Promise saqlanadi — ikki komponent bir vaqtda so'rasa ham so'rov bitta ketadi.
const kesh = new Map()
const natijalar = new Map()

function malumotnomaniOl(nomi) {
  if (!kesh.has(nomi)) {
    const sorov = api(`/${nomi}/`)
      .then((data) => {
        natijalar.set(nomi, data)
        return data
      })
      .catch((err) => {
        kesh.delete(nomi) // xato bo'lsa keyingi safar yana urinib ko'riladi
        throw err
      })
    kesh.set(nomi, sorov)
  }
  return kesh.get(nomi)
}

export function useMalumotnoma(nomi) {
  const [royxat, setRoyxat] = useState(() => natijalar.get(nomi) ?? [])
  useEffect(() => {
    let faol = true
    malumotnomaniOl(nomi).then((data) => faol && setRoyxat(data)).catch(() => {})
    return () => { faol = false }
  }, [nomi])
  return royxat
}
