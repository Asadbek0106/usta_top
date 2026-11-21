import { Navigate, useLocation } from 'react-router-dom'

import Yuklanmoqda from '../components/Yuklanmoqda'
import { useAuth } from './AuthContext'

// Faqat tizimga kirganlar ko'radigan sahifalar uchun
export default function Himoyalangan({ children, faqatUsta = false }) {
  const { user, yuklanmoqda } = useAuth()
  const location = useLocation()

  if (yuklanmoqda) return <Yuklanmoqda />
  if (!user) {
    // Qidiruv parametrlari ham saqlanadi: /arizalarim?status=yangi → kirgandan keyin aynan shu yerga
    return <Navigate to="/kirish" replace state={{ keyin: location.pathname + location.search }} />
  }
  if (faqatUsta && !user.usta_mi) return <Navigate to="/usta-bolish" replace />
  return children
}
