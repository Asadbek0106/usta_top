import { useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { api, formaXatolari } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Maydon, { UmumiyXato } from '../components/Maydon'
import { useMalumotnoma } from '../components/utils'
import { useSarlavha } from '../hooks/useSarlavha'

export default function UstaBolish() {
  useSarlavha("Usta bo'lish")
  const { user, meniYangila } = useAuth()
  const navigate = useNavigate()
  const shaharlar = useMalumotnoma('shaharlar')
  const kategoriyalar = useMalumotnoma('kategoriyalar')
  // Qatorlar uchun barqaror kalit: o'rtadagi qator o'chirilganda React qolganlarini adashtirmaydi
  const keyingiId = useRef(1)
  const yangiQator = () => ({ kalit: keyingiId.current++, kategoriya_id: '', narx_dan: '', tajriba: '' })
  const [shahar, setShahar] = useState('')
  const [tavsif, setTavsif] = useState('')
  const [xizmatlar, setXizmatlar] = useState(() => [{ kalit: 0, kategoriya_id: '', narx_dan: '', tajriba: '' }])
  const [xatolar, setXatolar] = useState(null)
  const [kutilmoqda, setKutilmoqda] = useState(false)

  if (user.usta_mi && !kutilmoqda) return <Navigate to="/usta-profilim" replace />

  const xizmatniOzgartir = (kalit, maydon, qiymat) =>
    setXizmatlar((r) => r.map((x) => (x.kalit === kalit ? { ...x, [maydon]: qiymat } : x)))

  // Bir kategoriya ikki qatorda tanlanmasin: boshqa qatorlarda band bo'lganlar ro'yxatdan olinadi
  const bandKategoriyalar = (kalit) =>
    new Set(xizmatlar.filter((x) => x.kalit !== kalit && x.kategoriya_id).map((x) => String(x.kategoriya_id)))

  const tekshir = () => {
    const x = {}
    if (!shahar) x.shahar = 'Shaharni tanlang.'
    const qatorlar = xizmatlar.map((q) => {
      const e = {}
      if (!q.kategoriya_id) e.kategoriya_id = 'Ish turini tanlang.'
      if (q.narx_dan === '' || Number(q.narx_dan) < 0) e.narx_dan = 'Narxni kiriting.'
      return e
    })
    if (qatorlar.some((e) => Object.keys(e).length)) x.xizmatlar = qatorlar
    return Object.keys(x).length ? x : null
  }

  const yuborish = async (e) => {
    e.preventDefault()
    if (kutilmoqda) return
    const mahalliy = tekshir()
    setXatolar(mahalliy)
    if (mahalliy) return
    setKutilmoqda(true)
    try {
      await api('/ustalar/', {
        method: 'POST',
        body: {
          shahar,
          tavsif: tavsif.trim(),
          xizmatlar: xizmatlar.map(({ kategoriya_id, narx_dan, tajriba }) => ({ kategoriya_id, narx_dan, tajriba: tajriba || 0 })),
        },
      })
      await meniYangila()
      navigate('/usta-profilim', { replace: true, state: { yangi: true } })
    } catch (err) {
      setXatolar(formaXatolari(err))
      setKutilmoqda(false)
    }
  }

  // Xizmatlar xatosi ro'yxat ko'rinishida keladi: [{narx_dan: [...]}, {}] yoki umumiy matn ["..."]
  const xizmatXatosi = (i) => {
    const r = xatolar?.xizmatlar
    return Array.isArray(r) && r[i] && typeof r[i] === 'object' ? r[i] : null
  }
  const xizmatlarUmumiy = Array.isArray(xatolar?.xizmatlar) && typeof xatolar.xizmatlar[0] === 'string'

  return (
    <div className="forma-sahifa forma-sahifa--keng">
      <h1>Usta bo'lish</h1>
      <p>Profilingizni to'ldiring. Admin tekshirgandan keyin u ustalar katalogida ko'rinadi.</p>
      <form onSubmit={yuborish} noValidate>
        <UmumiyXato xatolar={xatolar} />
        <Maydon nomi="shahar" yorliq="Qaysi shaharda ishlaysiz?" xatolar={xatolar}>
          <select value={shahar} onChange={(e) => setShahar(e.target.value)} required>
            <option value="">Tanlang</option>
            {shaharlar.map((s) => <option key={s.id} value={s.id}>{s.nomi}</option>)}
          </select>
        </Maydon>
        <Maydon nomi="tavsif" yorliq="O'zingiz haqingizda" xatolar={xatolar} izoh="Tajribangiz, qanday ishlarni yaxshi bajarishingiz">
          <textarea rows={3} maxLength={2000} value={tavsif} onChange={(e) => setTavsif(e.target.value)} />
        </Maydon>

        <fieldset className="xizmatlar-forma">
          <legend>Xizmatlaringiz</legend>
          {xizmatlarUmumiy && <p className="xabar xabar--xato" role="alert">{xatolar.xizmatlar.join(' ')}</p>}
          {xizmatlar.map((x, i) => {
            const band = bandKategoriyalar(x.kalit)
            const qx = xizmatXatosi(i)
            return (
              <div key={x.kalit} className="xizmat-qator">
                <Maydon nomi={`kategoriya_id-${x.kalit}`} yorliq="Ish turi" xato={qx?.kategoriya_id}>
                  <select value={x.kategoriya_id} onChange={(e) => xizmatniOzgartir(x.kalit, 'kategoriya_id', e.target.value)}>
                    <option value="">Tanlang</option>
                    {kategoriyalar.filter((k) => !band.has(String(k.id))).map((k) => <option key={k.id} value={k.id}>{k.nomi}</option>)}
                  </select>
                </Maydon>
                <Maydon nomi={`narx_dan-${x.kalit}`} yorliq="Narxi, so'mdan" xato={qx?.narx_dan}>
                  <input type="number" inputMode="numeric" min="0" step="1000" value={x.narx_dan}
                    onChange={(e) => xizmatniOzgartir(x.kalit, 'narx_dan', e.target.value)} />
                </Maydon>
                <Maydon nomi={`tajriba-${x.kalit}`} yorliq="Tajriba, yil" xato={qx?.tajriba}>
                  <input type="number" inputMode="numeric" min="0" max="80" value={x.tajriba}
                    onChange={(e) => xizmatniOzgartir(x.kalit, 'tajriba', e.target.value)} />
                </Maydon>
                {xizmatlar.length > 1 && (
                  <button type="button" className="tugma tugma--matn"
                    onClick={() => setXizmatlar((r) => r.filter((q) => q.kalit !== x.kalit))}
                    aria-label={`${i + 1}-xizmatni olib tashlash`}>
                    Olib tashlash
                  </button>
                )}
              </div>
            )
          })}
          {xizmatlar.length < kategoriyalar.length && (
            <button type="button" className="tugma tugma--chiziq" onClick={() => setXizmatlar((r) => [...r, yangiQator()])}>
              Yana xizmat qo'shish
            </button>
          )}
        </fieldset>

        <button type="submit" className="tugma tugma--asosiy" disabled={kutilmoqda}>
          {kutilmoqda ? 'Yuborilmoqda…' : 'Profilni yaratish'}
        </button>
      </form>
    </div>
  )
}
