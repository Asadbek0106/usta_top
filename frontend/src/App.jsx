import { lazy } from 'react'
import { Route, Routes } from 'react-router-dom'

import Himoyalangan from './auth/Himoyalangan'
import Layout from './components/Layout'
import Katalog from './pages/Katalog'

// Bosh sahifa darhol yuklanadi, qolganlari kerak bo'lganda alohida fayl sifatida keladi:
// mehmon foydalanuvchi profil va arizalar kodini umuman yuklab olmaydi
const UstaSahifasi = lazy(() => import('./pages/UstaSahifasi'))
const Kirish = lazy(() => import('./pages/Kirish'))
const RoyxatdanOtish = lazy(() => import('./pages/RoyxatdanOtish'))
const Arizalarim = lazy(() => import('./pages/Arizalarim'))
const UstaBolish = lazy(() => import('./pages/UstaBolish'))
const UstaProfilim = lazy(() => import('./pages/UstaProfilim'))
const Topilmadi = lazy(() => import('./pages/Topilmadi'))

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Katalog />} />
        <Route path="ustalar/:id" element={<UstaSahifasi />} />
        <Route path="kirish" element={<Kirish />} />
        <Route path="royxatdan-otish" element={<RoyxatdanOtish />} />
        <Route path="arizalarim" element={<Himoyalangan><Arizalarim /></Himoyalangan>} />
        <Route path="usta-bolish" element={<Himoyalangan><UstaBolish /></Himoyalangan>} />
        <Route path="usta-profilim" element={<Himoyalangan faqatUsta><UstaProfilim /></Himoyalangan>} />
        <Route path="*" element={<Topilmadi />} />
      </Route>
    </Routes>
  )
}
