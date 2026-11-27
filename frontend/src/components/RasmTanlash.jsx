import { useEffect, useRef, useState } from 'react'

export const RASM_SONI = 5
export const RASM_HAJMI_MB = 5
// HEIC (iPhone) ni server o'qiy olmaydi. accept'da aniq turlar berilsa, iPhone rasmni o'zi JPEG'ga aylantirib yuboradi
const TURLAR = ['image/jpeg', 'image/png', 'image/webp']

// Arizaga rasm biriktirish: tanlash, oldindan ko'rish va olib tashlash.
// rasmlar — [{ fayl: File, url: 'blob:...' }] massivi, ozgar — yangi massiv bilan chaqiriladi.
// Serverga yuborishda faqat r.fayl olinadi.
export default function RasmTanlash({ rasmlar, ozgar, xato: serverXatosi }) {
  const [xato, setXato] = useState('')

  // Oldindan ko'rish uchun blob: manzillar xotirada turadi — forma yopilganda bo'shatamiz
  const joriy = useRef(rasmlar)
  useEffect(() => { joriy.current = rasmlar }, [rasmlar])
  useEffect(() => () => joriy.current.forEach((r) => URL.revokeObjectURL(r.url)), [])

  const tanlandi = (e) => {
    const yangilar = [...e.target.files]
    e.target.value = '' // xuddi shu faylni olib tashlab, qayta tanlash mumkin bo'lishi uchun
    const xatolar = []
    const yaroqli = yangilar.filter((f) => {
      if (!TURLAR.includes(f.type)) {
        xatolar.push(`«${f.name}» rasm emas yoki bu format qo'llab-quvvatlanmaydi (JPG, PNG, WEBP).`)
        return false
      }
      if (f.size > RASM_HAJMI_MB * 1024 * 1024) {
        xatolar.push(`«${f.name}» juda katta: har bir rasm ${RASM_HAJMI_MB} MB dan oshmasin.`)
        return false
      }
      return true
    })
    const joy = RASM_SONI - rasmlar.length
    if (yaroqli.length > joy) xatolar.push(`Ko'pi bilan ${RASM_SONI} ta rasm yuklash mumkin.`)
    setXato(xatolar.join(' '))
    if (yaroqli.length && joy > 0) {
      const qoshiladi = yaroqli.slice(0, joy).map((fayl) => ({ fayl, url: URL.createObjectURL(fayl) }))
      ozgar([...rasmlar, ...qoshiladi])
    }
  }

  const olibTashla = (i) => {
    setXato('')
    URL.revokeObjectURL(rasmlar[i].url)
    ozgar(rasmlar.filter((_, j) => j !== i))
  }

  const korsatilganXato = xato || serverXatosi

  return (
    <div className={`maydon rasm-tanlash${korsatilganXato ? ' maydon--xato' : ''}`}>
      <span className="rasm-tanlash__yorliq" id="rasmlar-yorliq">Ishning rasmlari</span>
      <small className="maydon__izoh">
        Usta rasmga qarab narxni aniqroq aytadi. {RASM_SONI} tagacha, har biri {RASM_HAJMI_MB} MB gacha.
      </small>

      {rasmlar.length > 0 && (
        <ul className="rasm-tanlash__royxat" aria-labelledby="rasmlar-yorliq">
          {rasmlar.map((r, i) => (
            <li key={r.url}>
              <img src={r.url} alt={r.fayl.name} />
              <button type="button" className="rasm-tanlash__ochir" onClick={() => olibTashla(i)}
                aria-label={`${r.fayl.name} rasmini olib tashlash`}>×</button>
            </li>
          ))}
        </ul>
      )}

      {rasmlar.length < RASM_SONI && (
        <>
          <input id="rasmlar" type="file" accept={TURLAR.join(',')} multiple className="sr-only"
            onChange={tanlandi} aria-describedby={korsatilganXato ? 'rasmlar-xato' : undefined} />
          <label htmlFor="rasmlar" className="tugma tugma--chiziq rasm-tanlash__tugma">
            {rasmlar.length ? "Yana rasm qo'shish" : 'Rasm biriktirish'}
          </label>
        </>
      )}

      {korsatilganXato && <small id="rasmlar-xato" className="maydon__xato" role="alert">{korsatilganXato}</small>}
    </div>
  )
}

// Ariza kartasidagi rasmlar: bosilsa to'liq o'lchamda yangi oynada ochiladi
export function RasmlarGalereyasi({ rasmlar }) {
  if (!rasmlar?.length) return null
  return (
    <ul className="ariza__rasmlar" aria-label="Ish rasmlari">
      {rasmlar.map((r, i) => (
        <li key={r.id}>
          <a href={r.rasm} target="_blank" rel="noopener noreferrer">
            <img src={r.rasm} alt={`Ish rasmi ${i + 1}`} loading="lazy" />
          </a>
        </li>
      ))}
    </ul>
  )
}
