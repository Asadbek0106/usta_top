import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { api, formaXatolari } from '../api/client'
import Maydon, { UmumiyXato } from '../components/Maydon'
import Reyting from '../components/Reyting'
import Statistika from '../components/Statistika'
import { somda, useMalumotnoma } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

export default function UstaProfilim() {
  useSarlavha('Usta profilim')
  const yangi = useLocation().state?.yangi
  const profil = useSorov('/ustalar/men/')
  // Ommaviy sahifa faqat tasdiqlangan ustalar uchun ochiladi — shu orqali holatni bilamiz.
  // (To'g'ri yechim: API'da `tasdiqlangan` maydonini qaytarish — README'dagi takliflarga qarang.)
  const ommaviy = useSorov(profil.data ? `/ustalar/${profil.data.id}/` : null)
  const katalogda = ommaviy.data ? true : ommaviy.xato?.status === 404 ? false : null

  if (profil.xato) return <XatoBlok xato={profil.xato} qaytaUrinish={profil.qaytaYukla} />
  if (!profil.data) return <Yuklanmoqda />

  return (
    <div className="profil">
      <header className="usta-sahifa__tepa">
        <div>
          <h1>Usta profilim</h1>
          {katalogda === true && <p><Link to={`/ustalar/${profil.data.id}`}>Mijozlar ko'radigan sahifam</Link></p>}
        </div>
        <Reyting qiymat={profil.data.reyting} soni={profil.data.sharhlar_soni} />
      </header>

      {katalogda === false && (
        <p className="xabar xabar--kutish" role="status">
          {yangi ? 'Profil yaratildi. ' : ''}Admin tekshirgandan keyin profilingiz katalogda ko'rinadi.
        </p>
      )}

      <Statistika />

      <div className="profil__ustunlar">
        {/* key: profil qayta yuklansa forma ham yangi qiymatlar bilan boshlanadi */}
        <AsosiyForma key={profil.data.id} profil={profil.data} saqlandi={profil.ozgartir} />
        <Xizmatlarim />
      </div>
    </div>
  )
}

function AsosiyForma({ profil, saqlandi }) {
  const shaharlar = useMalumotnoma('shaharlar')
  const [forma, setForma] = useState({ shahar: String(profil.shahar.id), tavsif: profil.tavsif })
  const [xatolar, setXatolar] = useState(null)
  const [holat, setHolat] = useState('') // '' | 'saqlanmoqda' | 'saqlandi'

  const ozgardi = forma.shahar !== String(profil.shahar.id) || forma.tavsif !== profil.tavsif

  const saqla = async (e) => {
    e.preventDefault()
    if (holat === 'saqlanmoqda') return
    setXatolar(null)
    setHolat('saqlanmoqda')
    try {
      const yangi = await api('/ustalar/men/', { method: 'PATCH', body: { ...forma, tavsif: forma.tavsif.trim() } })
      saqlandi(yangi)
      setForma({ shahar: String(yangi.shahar.id), tavsif: yangi.tavsif })
      setHolat('saqlandi')
    } catch (err) {
      setXatolar(formaXatolari(err))
      setHolat('')
    }
  }

  const ozgar = (maydon) => (e) => {
    setForma({ ...forma, [maydon]: e.target.value })
    setHolat('')
  }

  return (
    <form onSubmit={saqla} className="profil__forma" noValidate>
      <h2>Asosiy ma'lumotlar</h2>
      <UmumiyXato xatolar={xatolar} />
      <Maydon nomi="shahar" yorliq="Shahar" xatolar={xatolar}>
        <select value={forma.shahar} onChange={ozgar('shahar')}>
          {shaharlar.length === 0 && <option value={forma.shahar}>{profil.shahar.nomi}</option>}
          {shaharlar.map((s) => <option key={s.id} value={s.id}>{s.nomi}</option>)}
        </select>
      </Maydon>
      <Maydon nomi="tavsif" yorliq="O'zingiz haqingizda" xatolar={xatolar}>
        <textarea rows={4} maxLength={2000} value={forma.tavsif} onChange={ozgar('tavsif')} />
      </Maydon>
      <button type="submit" className="tugma tugma--asosiy" disabled={!ozgardi || holat === 'saqlanmoqda'}>
        {holat === 'saqlanmoqda' ? 'Saqlanmoqda…' : 'Saqlash'}
      </button>
      <span className="xabar-qisqa" role="status">{holat === 'saqlandi' ? 'Saqlandi' : ''}</span>
    </form>
  )
}

const BOSH_XIZMAT = { kategoriya_id: '', narx_dan: '', tajriba: '' }

function Xizmatlarim() {
  const kategoriyalar = useMalumotnoma('kategoriyalar')
  const { data: xizmatlar, xato, qaytaYukla, ozgartir } = useSorov('/xizmatlarim/')
  const [yangi, setYangi] = useState(BOSH_XIZMAT)
  const [xatolar, setXatolar] = useState(null)
  const [band, setBand] = useState(false)
  const [tahrir, setTahrir] = useState(null) // { id, narx_dan, tajriba }

  const bajar = async (fn) => {
    if (band) return
    setBand(true)
    setXatolar(null)
    try {
      await fn()
    } catch (err) {
      setXatolar(formaXatolari(err))
    } finally {
      setBand(false)
    }
  }

  const qoshish = (e) => {
    e.preventDefault()
    if (!yangi.kategoriya_id || yangi.narx_dan === '') {
      setXatolar({
        ...(!yangi.kategoriya_id && { kategoriya_id: 'Ish turini tanlang.' }),
        ...(yangi.narx_dan === '' && { narx_dan: 'Narxni kiriting.' }),
      })
      return
    }
    bajar(async () => {
      const x = await api('/xizmatlarim/', { method: 'POST', body: { ...yangi, tajriba: yangi.tajriba || 0 } })
      ozgartir((r) => [...r, x])
      setYangi(BOSH_XIZMAT)
    })
  }

  const saqla = (e) => {
    e.preventDefault()
    bajar(async () => {
      const { id, narx_dan, tajriba } = tahrir
      const x = await api(`/xizmatlarim/${id}/`, { method: 'PATCH', body: { narx_dan, tajriba: tajriba || 0 } })
      ozgartir((r) => r.map((q) => (q.id === x.id ? x : q)))
      setTahrir(null)
    })
  }

  const ochir = (x) => {
    if (!window.confirm(`"${x.kategoriya.nomi}" xizmatini o'chirasizmi?`)) return
    bajar(async () => {
      await api(`/xizmatlarim/${x.id}/`, { method: 'DELETE' })
      ozgartir((r) => r.filter((q) => q.id !== x.id))
    })
  }

  if (xato) return <section className="profil__xizmatlar"><h2>Xizmatlarim</h2><XatoBlok xato={xato} qaytaUrinish={qaytaYukla} /></section>
  if (!xizmatlar) return <section className="profil__xizmatlar"><h2>Xizmatlarim</h2><Yuklanmoqda /></section>

  const bandlar = new Set(xizmatlar.map((x) => x.kategoriya.id))
  const boshKategoriyalar = kategoriyalar.filter((k) => !bandlar.has(k.id))
  const yolgiz = xizmatlar.length <= 1

  return (
    <section className="profil__xizmatlar">
      <h2>Xizmatlarim</h2>
      <UmumiyXato xatolar={xatolar} />
      <form onSubmit={saqla} className="jadval-ora">
        <table className="jadval">
          <thead>
            <tr>
              <th scope="col">Ish turi</th><th scope="col">Narxi, so'mdan</th><th scope="col">Tajriba, yil</th>
              <th scope="col"><span className="sr-only">Amallar</span></th>
            </tr>
          </thead>
          <tbody>
            {xizmatlar.map((x) => (tahrir?.id === x.id ? (
              // Alohida key shart: aks holda React "Tahrirlash" (type=button) DOM elementini qayta ishlatib,
              // uni "Saqlash" (type=submit) ga aylantiradi va brauzer o'sha bosishni forma yuborish deb qabul qiladi
              <tr key={`tahrir-${x.id}`} className="jadval__tahrir">
                <td>{x.kategoriya.nomi}</td>
                <td>
                  <input aria-label="Narxi, so'mdan" type="number" inputMode="numeric" min="0" step="1000" value={tahrir.narx_dan}
                    onChange={(e) => setTahrir({ ...tahrir, narx_dan: e.target.value })} required />
                </td>
                <td>
                  <input aria-label="Tajriba, yil" type="number" inputMode="numeric" min="0" max="80" value={tahrir.tajriba}
                    onChange={(e) => setTahrir({ ...tahrir, tajriba: e.target.value })} />
                </td>
                <td className="jadval__amallar">
                  <button type="submit" className="tugma tugma--matn" disabled={band}>Saqlash</button>
                  <button type="button" className="tugma tugma--matn" onClick={() => setTahrir(null)}>Bekor</button>
                </td>
              </tr>
            ) : (
              <tr key={x.id}>
                <td>{x.kategoriya.nomi}</td>
                <td>{somda(x.narx_dan)}</td>
                <td>{x.tajriba}</td>
                <td className="jadval__amallar">
                  <button type="button" className="tugma tugma--matn" disabled={band}
                    onClick={() => setTahrir({ id: x.id, narx_dan: String(Math.round(Number(x.narx_dan))), tajriba: String(x.tajriba) })}>
                    Tahrirlash
                  </button>
                  <button type="button" className="tugma tugma--matn tugma--matn-xavfli" disabled={band || yolgiz}
                    title={yolgiz ? 'Kamida bitta xizmat qolishi kerak' : undefined} onClick={() => ochir(x)}>
                    O'chirish
                  </button>
                </td>
              </tr>
            )))}
          </tbody>
        </table>
      </form>

      {boshKategoriyalar.length > 0 && (
        <form onSubmit={qoshish} className="xizmat-qator" noValidate>
          <Maydon nomi="kategoriya_id" yorliq="Ish turi" xatolar={xatolar}>
            <select value={yangi.kategoriya_id} onChange={(e) => setYangi({ ...yangi, kategoriya_id: e.target.value })}>
              <option value="">Tanlang</option>
              {boshKategoriyalar.map((k) => <option key={k.id} value={k.id}>{k.nomi}</option>)}
            </select>
          </Maydon>
          <Maydon nomi="narx_dan" yorliq="Narxi, so'mdan" xatolar={xatolar}>
            <input type="number" inputMode="numeric" min="0" step="1000" value={yangi.narx_dan} onChange={(e) => setYangi({ ...yangi, narx_dan: e.target.value })} />
          </Maydon>
          <Maydon nomi="tajriba" yorliq="Tajriba, yil" xatolar={xatolar}>
            <input type="number" inputMode="numeric" min="0" max="80" value={yangi.tajriba} onChange={(e) => setYangi({ ...yangi, tajriba: e.target.value })} />
          </Maydon>
          <button type="submit" className="tugma tugma--ikkinchi" disabled={band}>Qo'shish</button>
        </form>
      )}
    </section>
  )
}
