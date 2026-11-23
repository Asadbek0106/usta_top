import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { api, formaXatolari } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Maydon, { UmumiyXato } from '../components/Maydon'
import Yuklanmoqda from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

export default function ParolTiklash() {
  useSarlavha('Parolni tiklash')
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data: telegram, yuklanmoqda } = useSorov('/auth/telegram/')
  const [forma, setForma] = useState({ telefon: '', kod: '', password: '', password2: '' })
  const [xatolar, setXatolar] = useState(null)
  const [kutilmoqda, setKutilmoqda] = useState(false)

  if (user) return <Navigate to="/" replace />
  if (yuklanmoqda && !telegram) return <Yuklanmoqda />

  const ozgar = (e) => setForma({ ...forma, [e.target.name]: e.target.value })

  const tekshir = () => {
    const x = {}
    if (!forma.telefon.trim()) x.telefon = 'Telefon raqamni kiriting.'
    if (!/^\d{6}$/.test(forma.kod.trim())) x.kod = 'Botdan olingan 6 xonali kodni kiriting.'
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
      const javob = await api('/auth/parol-tiklash/', {
        method: 'POST',
        body: { ...forma, telefon: forma.telefon.trim(), kod: forma.kod.trim() },
      })
      navigate('/kirish', { replace: true, state: { xabar: javob.detail } })
    } catch (err) {
      setXatolar(err.status === 429 ? { detail: "Urinishlar juda ko'p. Bir daqiqadan keyin qaytadan urinib ko'ring." } : formaXatolari(err))
      setKutilmoqda(false)
    }
  }

  if (!telegram?.bot) {
    return (
      <div className="forma-sahifa">
        <h1>Parolni tiklash</h1>
        <p className="xabar xabar--kutish">
          Parolni tiklash Telegram bot orqali ishlaydi, lekin bot hozircha sozlanmagan. Administratorga murojaat qiling.
        </p>
        <p><Link to="/kirish">Kirish sahifasiga qaytish</Link></p>
      </div>
    )
  }

  return (
    <div className="forma-sahifa">
      <h1>Parolni tiklash</h1>
      <div className="bot-yoriqnoma">
        <p><b>Kodni Telegram orqali oling</b></p>
        <ol>
          <li>
            <a href={telegram.havola} target="_blank" rel="noopener noreferrer">@{telegram.bot}</a> ni oching va{' '}
            <b>Start</b> tugmasini bosing.
          </li>
          <li><b>📱 Raqamni yuborish</b> tugmasini bosing — raqamingiz ro'yxatdan o'tgan bo'lsa, bot parolni tiklash kodini yuboradi.</li>
          <li>Kodni va yangi parolni pastdagi formaga kiriting.</li>
        </ol>
      </div>
      <form onSubmit={yuborish} noValidate>
        <UmumiyXato xatolar={xatolar} />
        <Maydon nomi="telefon" yorliq="Telefon raqam" xatolar={xatolar}>
          <input name="telefon" type="tel" inputMode="tel" autoComplete="tel" value={forma.telefon} onChange={ozgar}
            placeholder="+998 90 123 45 67" required />
        </Maydon>
        <Maydon nomi="kod" yorliq="Telegram'dan kelgan kod" xatolar={xatolar} izoh="Kod 10 daqiqa amal qiladi">
          <input name="kod" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={forma.kod}
            onChange={ozgar} placeholder="123456" required />
        </Maydon>
        <Maydon nomi="password" yorliq="Yangi parol" xatolar={xatolar} izoh="Kamida 8 ta belgi, faqat raqamlardan iborat bo'lmasin">
          <input name="password" type="password" autoComplete="new-password" value={forma.password} onChange={ozgar} required />
        </Maydon>
        <Maydon nomi="password2" yorliq="Yangi parolni takrorlang" xatolar={xatolar}>
          <input name="password2" type="password" autoComplete="new-password" value={forma.password2} onChange={ozgar} required />
        </Maydon>
        <button type="submit" className="tugma tugma--asosiy tugma--keng" disabled={kutilmoqda}>
          {kutilmoqda ? 'Saqlanmoqda…' : 'Parolni yangilash'}
        </button>
      </form>
      <p>Parol esingizga tushdimi? <Link to="/kirish">Kiring</Link></p>
    </div>
  )
}
