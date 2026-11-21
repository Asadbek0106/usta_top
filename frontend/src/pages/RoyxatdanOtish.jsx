import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { formaXatolari } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Maydon, { UmumiyXato } from '../components/Maydon'
import { xavfsizManzil } from '../components/utils'
import { useSarlavha } from '../hooks/useSarlavha'

export default function RoyxatdanOtish() {
  useSarlavha("Ro'yxatdan o'tish")
  const { user, royxatdanOtish } = useAuth()
  const navigate = useNavigate()
  const keyin = xavfsizManzil(useLocation().state?.keyin)
  const [forma, setForma] = useState({ telefon: '', first_name: '', last_name: '', password: '', password2: '' })
  const [xatolar, setXatolar] = useState(null)
  const [kutilmoqda, setKutilmoqda] = useState(false)

  if (user && !kutilmoqda) return <Navigate to={keyin} replace />

  const ozgar = (e) => setForma({ ...forma, [e.target.name]: e.target.value })

  const tekshir = () => {
    const x = {}
    if (!forma.telefon.trim()) x.telefon = 'Telefon raqamni kiriting.'
    if (!forma.first_name.trim()) x.first_name = 'Ismingizni kiriting — ustalar sizni shu nom bilan ko\'radi.'
    if (forma.password.length < 8) x.password = "Parol kamida 8 ta belgidan iborat bo'lsin."
    if (forma.password && forma.password !== forma.password2) x.password2 = 'Parollar mos kelmadi.'
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
      await royxatdanOtish({ ...forma, telefon: forma.telefon.trim(), first_name: forma.first_name.trim(), last_name: forma.last_name.trim() })
      navigate(keyin, { replace: true })
    } catch (err) {
      setXatolar(err.status === 429 ? { detail: "Urinishlar juda ko'p. Bir daqiqadan keyin qaytadan urinib ko'ring." } : formaXatolari(err))
      setKutilmoqda(false)
    }
  }

  return (
    <div className="forma-sahifa">
      <h1>Ro'yxatdan o'tish</h1>
      <form onSubmit={yuborish} noValidate>
        <UmumiyXato xatolar={xatolar} />
        <Maydon nomi="telefon" yorliq="Telefon raqam" xatolar={xatolar} izoh="Shu raqam bilan tizimga kirasiz">
          <input name="telefon" type="tel" inputMode="tel" autoComplete="tel" value={forma.telefon} onChange={ozgar}
            placeholder="+998 90 123 45 67" required />
        </Maydon>
        <div className="ikki-ustun">
          <Maydon nomi="first_name" yorliq="Ism" xatolar={xatolar}>
            <input name="first_name" autoComplete="given-name" value={forma.first_name} onChange={ozgar} required />
          </Maydon>
          <Maydon nomi="last_name" yorliq="Familiya (ixtiyoriy)" xatolar={xatolar}>
            <input name="last_name" autoComplete="family-name" value={forma.last_name} onChange={ozgar} />
          </Maydon>
        </div>
        <Maydon nomi="password" yorliq="Parol" xatolar={xatolar} izoh="Kamida 8 ta belgi, faqat raqamlardan iborat bo'lmasin">
          <input name="password" type="password" autoComplete="new-password" value={forma.password} onChange={ozgar} required />
        </Maydon>
        <Maydon nomi="password2" yorliq="Parolni takrorlang" xatolar={xatolar}>
          <input name="password2" type="password" autoComplete="new-password" value={forma.password2} onChange={ozgar} required />
        </Maydon>
        <button type="submit" className="tugma tugma--asosiy tugma--keng" disabled={kutilmoqda}>
          {kutilmoqda ? 'Yaratilmoqda…' : "Ro'yxatdan o'tish"}
        </button>
      </form>
      <p>Akkauntingiz bormi? <Link to="/kirish" state={{ keyin }}>Kiring</Link></p>
    </div>
  )
}
