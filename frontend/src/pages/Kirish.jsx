import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { formaXatolari } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Maydon, { UmumiyXato } from '../components/Maydon'
import { xavfsizManzil } from '../components/utils'
import { useSarlavha } from '../hooks/useSarlavha'

export default function Kirish() {
  useSarlavha('Kirish')
  const { user, kirish } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const keyin = xavfsizManzil(location.state?.keyin)
  // Parol tiklangandan keyin keladigan xabar
  const [xabar] = useState(location.state?.xabar)
  const [forma, setForma] = useState({ telefon: '', password: '' })
  const [xatolar, setXatolar] = useState(null)
  const [kutilmoqda, setKutilmoqda] = useState(false)

  if (user && !kutilmoqda) return <Navigate to={keyin} replace />

  const yuborish = async (e) => {
    e.preventDefault()
    if (kutilmoqda) return
    const mahalliy = {}
    if (!forma.telefon.trim()) mahalliy.telefon = 'Telefon raqamni kiriting.'
    if (!forma.password) mahalliy.password = 'Parolni kiriting.'
    if (Object.keys(mahalliy).length) return setXatolar(mahalliy)

    setKutilmoqda(true)
    setXatolar(null)
    try {
      await kirish(forma.telefon.trim(), forma.password)
      navigate(keyin, { replace: true })
    } catch (err) {
      if (err.status === 401) setXatolar({ detail: "Telefon raqam yoki parol noto'g'ri." })
      else if (err.status === 429) setXatolar({ detail: "Urinishlar juda ko'p. Bir daqiqadan keyin qaytadan urinib ko'ring." })
      else setXatolar(formaXatolari(err))
      setKutilmoqda(false)
    }
  }

  return (
    <div className="forma-sahifa">
      <h1>Kirish</h1>
      {xabar && <p className="xabar xabar--ok" role="status">{xabar}</p>}
      <form onSubmit={yuborish} noValidate>
        <UmumiyXato xatolar={xatolar} />
        <Maydon nomi="telefon" yorliq="Telefon raqam" xatolar={xatolar}>
          <input type="tel" inputMode="tel" autoComplete="tel" value={forma.telefon} placeholder="+998 90 123 45 67"
            onChange={(e) => setForma({ ...forma, telefon: e.target.value })} required />
        </Maydon>
        <Maydon nomi="password" yorliq="Parol" xatolar={xatolar}>
          <input type="password" autoComplete="current-password" value={forma.password}
            onChange={(e) => setForma({ ...forma, password: e.target.value })} required />
        </Maydon>
        <button type="submit" className="tugma tugma--asosiy tugma--keng" disabled={kutilmoqda}>
          {kutilmoqda ? 'Kirilmoqda…' : 'Kirish'}
        </button>
      </form>
      <p><Link to="/parol-tiklash">Parolni unutdingizmi?</Link></p>
      <p>Akkauntingiz yo'qmi? <Link to="/royxatdan-otish" state={{ keyin }}>Ro'yxatdan o'ting</Link></p>
    </div>
  )
}
