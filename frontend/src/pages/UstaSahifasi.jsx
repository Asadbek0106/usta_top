import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, formaXatolari } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Maydon, { UmumiyXato } from '../components/Maydon'
import Reyting, { Yulduzlar } from '../components/Reyting'
import Sahifalash from '../components/Sahifalash'
import { sana, somda } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

export default function UstaSahifasi() {
  const { id } = useParams()
  // key={id}: boshqa ustaga o'tilganda sahifa holati (sharhlar sahifasi, forma) to'liq yangilanadi
  return <UstaTafsiloti key={id} id={id} />
}

function UstaTafsiloti({ id }) {
  const { data: usta, xato, qaytaYukla } = useSorov(`/ustalar/${id}/`)
  const [sahifa, setSahifa] = useState(1)
  const sharhlar = useSorov(usta ? `/ustalar/${id}/sharhlar/` : null, { page: sahifa > 1 ? sahifa : '' })
  useSarlavha(usta?.ism ?? (xato?.status === 404 ? 'Usta topilmadi' : 'Usta'))

  if (xato?.status === 404) {
    return (
      <div className="bosh">
        <h1>Usta topilmadi</h1>
        <p>Bunday usta yo'q yoki uning profili hali tasdiqlanmagan.</p>
        <Link to="/" className="tugma tugma--asosiy">Ustalar ro'yxatiga qaytish</Link>
      </div>
    )
  }
  if (xato) return <XatoBlok xato={xato} qaytaUrinish={qaytaYukla} />
  if (!usta) return <Yuklanmoqda />

  return (
    <div className="usta-sahifa">
      <Link to="/" className="orqaga">Barcha ustalar</Link>

      <header className="usta-sahifa__tepa">
        <div>
          <h1>{usta.ism || 'Ismsiz usta'}</h1>
          <p className="usta-sahifa__shahar">{usta.shahar.nomi}</p>
        </div>
        <Reyting qiymat={usta.reyting} soni={usta.sharhlar_soni} />
      </header>

      {usta.tavsif && <p className="usta-sahifa__tavsif">{usta.tavsif}</p>}

      <div className="usta-sahifa__ustunlar">
        <div>
          <h2>Xizmatlar va narxlar</h2>
          <div className="jadval-ora">
            <table className="jadval">
              <thead>
                <tr><th scope="col">Ish turi</th><th scope="col">Narxi</th><th scope="col">Tajriba</th></tr>
              </thead>
              <tbody>
                {usta.xizmatlar.map((x) => (
                  <tr key={x.id}>
                    <td>{x.kategoriya.nomi}</td>
                    <td>{somda(x.narx_dan)} dan</td>
                    <td>{x.tajriba ? `${x.tajriba} yil` : '1 yildan kam'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2>Mijozlar fikri</h2>
          <XatoBlok xato={sharhlar.xato} qaytaUrinish={sharhlar.qaytaYukla} />
          {sharhlar.data?.count === 0 && <p className="xira">Bu usta hali baholanmagan.</p>}
          <ul className={`sharhlar${sharhlar.yangilanmoqda ? ' ustalar--yangilanmoqda' : ''}`}>
            {sharhlar.data?.results.map((s) => (
              <li key={s.id}>
                <Yulduzlar baho={s.baho} />
                {s.matn && <p>{s.matn}</p>}
                <small className="xira"><time dateTime={s.yaratilgan}>{sana(s.yaratilgan)}</time></small>
              </li>
            ))}
          </ul>
          {sharhlar.data && <Sahifalash sahifa={sahifa} jami={sharhlar.data.count} ozgartir={setSahifa} />}
        </div>

        <ArizaFormasi usta={usta} />
      </div>
    </div>
  )
}

function ArizaFormasi({ usta }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [forma, setForma] = useState({ kategoriya: usta.xizmatlar[0]?.kategoriya.id ?? '', tavsif: '', manzil: '' })
  const [xatolar, setXatolar] = useState(null)
  const [yuborilmoqda, setYuborilmoqda] = useState(false)

  if (!user) {
    return (
      <aside className="ariza-forma">
        <h2>Ustaga ariza qoldirish</h2>
        <p>Ariza yuborish uchun tizimga kiring.</p>
        <Link to="/kirish" state={{ keyin: `/ustalar/${usta.id}` }} className="tugma tugma--asosiy">Kirish</Link>
      </aside>
    )
  }
  if (user.telefon === usta.telefon) {
    return (
      <aside className="ariza-forma">
        <h2>Bu sizning profilingiz</h2>
        <p>Mijozlar sizga shu sahifa orqali ariza qoldiradi.</p>
        <Link to="/usta-profilim" className="tugma tugma--ikkinchi">Profilni tahrirlash</Link>
      </aside>
    )
  }

  const ozgar = (e) => setForma({ ...forma, [e.target.name]: e.target.value })

  // Oddiy xatolarni serverga bormasdan ko'rsatamiz; qolganini (masalan, kategoriya mosligi) backend tekshiradi
  const tekshir = () => {
    const x = {}
    if (!forma.tavsif.trim()) x.tavsif = 'Qanday ish kerakligini yozing.'
    if (!forma.manzil.trim()) x.manzil = 'Manzilni kiriting.'
    return Object.keys(x).length ? x : null
  }

  const yuborish = async (e) => {
    e.preventDefault()
    if (yuborilmoqda) return
    const mahalliy = tekshir()
    setXatolar(mahalliy)
    if (mahalliy) return
    setYuborilmoqda(true)
    try {
      await api('/arizalar/', {
        method: 'POST',
        body: { usta: usta.id, ...forma, tavsif: forma.tavsif.trim(), manzil: forma.manzil.trim() },
      })
      navigate('/arizalarim', { state: { xabar: "Ariza yuborildi. Usta qabul qilganda holati shu yerda o'zgaradi." } })
    } catch (err) {
      setXatolar(err.status === 429 ? { detail: "Juda ko'p ariza yuborildi. Birozdan keyin urinib ko'ring." } : formaXatolari(err))
      setYuborilmoqda(false)
    }
  }

  return (
    <aside className="ariza-forma">
      <h2>Ustaga ariza qoldirish</h2>
      <p className="xira">Telefon: <a href={`tel:${usta.telefon}`}>{usta.telefon}</a></p>
      <form onSubmit={yuborish} noValidate>
        <UmumiyXato xatolar={xatolar} />
        <Maydon nomi="kategoriya" yorliq="Ish turi" xatolar={xatolar}>
          <select name="kategoriya" value={forma.kategoriya} onChange={ozgar}>
            {usta.xizmatlar.map((x) => <option key={x.kategoriya.id} value={x.kategoriya.id}>{x.kategoriya.nomi}</option>)}
          </select>
        </Maydon>
        <Maydon nomi="tavsif" yorliq="Nima qilish kerak?" xatolar={xatolar}>
          <textarea name="tavsif" rows={4} value={forma.tavsif} onChange={ozgar} maxLength={2000}
            placeholder="Masalan: oshxonadagi kran oqyapti, almashtirish kerak" required />
        </Maydon>
        <Maydon nomi="manzil" yorliq="Manzil" xatolar={xatolar}>
          <input name="manzil" value={forma.manzil} onChange={ozgar} maxLength={255} autoComplete="street-address"
            placeholder="Tuman, ko'cha, uy" required />
        </Maydon>
        <button type="submit" className="tugma tugma--asosiy tugma--keng" disabled={yuborilmoqda}>
          {yuborilmoqda ? 'Yuborilmoqda…' : 'Ariza yuborish'}
        </button>
      </form>
    </aside>
  )
}
