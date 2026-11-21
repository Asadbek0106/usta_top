import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { api, KALITLAR, tokenlar } from '../api/client'

const AuthContext = createContext(null)

// Qaytaradi: foydalanuvchi | null (tizimda emas) | undefined (server javob bermadi — holat o'zgarmaydi)
async function joriyFoydalanuvchi() {
  if (!tokenlar.access) return null
  try {
    return await api('/auth/me/')
  } catch (err) {
    // Faqat token yaroqsiz bo'lsa chiqaramiz. Server vaqtincha ishlamasa (500, tarmoq)
    // foydalanuvchini tizimdan haydab yubormaymiz.
    if (err.status === 401 || err.status === 403) {
      tokenlar.tozala()
      return null
    }
    return undefined
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [yuklanmoqda, setYuklanmoqda] = useState(() => Boolean(tokenlar.access))

  const meniYangila = useCallback(async () => {
    const men = await joriyFoydalanuvchi()
    if (men !== undefined) setUser(men)
    return men ?? null
  }, [])

  useEffect(() => {
    let faol = true
    joriyFoydalanuvchi().then((men) => {
      if (!faol) return
      if (men !== undefined) setUser(men)
      setYuklanmoqda(false)
    })

    const chiqarildi = () => setUser(null)
    // Boshqa tabda kirilsa yoki chiqilsa, bu tab ham shunga moslashadi
    const boshqaTab = (e) => {
      if (e.key === null || e.key === KALITLAR.access || e.key === KALITLAR.refresh) meniYangila()
    }
    window.addEventListener('usta:chiqish', chiqarildi)
    window.addEventListener('storage', boshqaTab)
    return () => {
      faol = false
      window.removeEventListener('usta:chiqish', chiqarildi)
      window.removeEventListener('storage', boshqaTab)
    }
  }, [meniYangila])

  const kirish = useCallback(async (telefon, password) => {
    tokenlar.saqla(await api('/auth/login/', { method: 'POST', body: { telefon, password } }))
    return meniYangila()
  }, [meniYangila])

  const royxatdanOtish = useCallback(async (malumot) => {
    const javob = await api('/auth/register/', { method: 'POST', body: malumot })
    tokenlar.saqla(javob.tokens)
    setUser(javob.user)
    return javob.user
  }, [])

  const chiqish = useCallback(async () => {
    const refresh = tokenlar.refresh
    // Refresh token serverda qora ro'yxatga tushishi uchun avval so'rov, keyin tozalash
    if (refresh) await api('/auth/logout/', { method: 'POST', body: { refresh } }).catch(() => {})
    tokenlar.tozala()
    setUser(null)
  }, [])

  // Qiymat har renderda yangi obyekt bo'lmasin — aks holda butun ilova qayta chiziladi
  const qiymat = useMemo(
    () => ({ user, yuklanmoqda, kirish, royxatdanOtish, chiqish, meniYangila }),
    [user, yuklanmoqda, kirish, royxatdanOtish, chiqish, meniYangila],
  )

  return <AuthContext.Provider value={qiymat}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth AuthProvider ichida ishlatilishi kerak')
  return ctx
}
