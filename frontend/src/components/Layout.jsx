import { Suspense, useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import XatoChegarasi from './XatoChegarasi'
import Yuklanmoqda from './Yuklanmoqda'

// Yangi sahifaga o'tilganda tepaga qaytish va fokusni asosiy qismga ko'chirish.
// Faqat filtr (?search=...) o'zgarganda sahifa sakramaydi.
function useSahifaAlmashuvi() {
  const { pathname } = useLocation()
  const asosiyRef = useRef(null)
  const birinchi = useRef(true)

  useEffect(() => {
    if (birinchi.current) {
      birinchi.current = false
      return
    }
    window.scrollTo(0, 0)
    asosiyRef.current?.focus({ preventScroll: true })
  }, [pathname])

  return asosiyRef
}

export default function Layout() {
  const { user, chiqish } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const asosiyRef = useSahifaAlmashuvi()

  const chiqishniBosish = async () => {
    await chiqish()
    navigate('/', { replace: true })
  }

  return (
    <>
      <a href="#asosiy" className="otish-havolasi">Asosiy qismga o'tish</a>
      <header className="sarlavha">
        <div className="sarlavha__ichki">
          <Link to="/" className="logo" aria-label="Usta — bosh sahifa">usta</Link>
          <nav className="menyu" aria-label="Asosiy menyu">
            <NavLink to="/" end>Ustalar</NavLink>
            {user && <NavLink to="/arizalarim">Arizalarim</NavLink>}
            {user?.usta_mi && <NavLink to="/usta-profilim">Usta profilim</NavLink>}
            {user && !user.usta_mi && <NavLink to="/usta-bolish">Usta bo'lish</NavLink>}
          </nav>
          <div className="foydalanuvchi">
            {user ? (
              <>
                <span className="foydalanuvchi__ism">{user.first_name || user.telefon}</span>
                <button type="button" className="tugma tugma--matn" onClick={chiqishniBosish}>Chiqish</button>
              </>
            ) : (
              <>
                <Link to="/kirish" className="tugma tugma--matn">Kirish</Link>
                <Link to="/royxatdan-otish" className="tugma tugma--asosiy">Ro'yxatdan o'tish</Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main id="asosiy" className="asosiy" ref={asosiyRef} tabIndex={-1}>
        <XatoChegarasi kalit={pathname}>
          <Suspense fallback={<Yuklanmoqda />}>
            <Outlet />
          </Suspense>
        </XatoChegarasi>
      </main>
      <footer className="pastki">
        <p>Usta — ustalarni topish va ularga ariza qoldirish platformasi. Kurs ishi, {new Date().getFullYear()}.</p>
      </footer>
    </>
  )
}
