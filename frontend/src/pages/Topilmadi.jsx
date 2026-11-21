import { Link } from 'react-router-dom'

import { useSarlavha } from '../hooks/useSarlavha'

export default function Topilmadi() {
  useSarlavha('Sahifa topilmadi')
  return (
    <div className="bosh">
      <h1>Sahifa topilmadi</h1>
      <p>Manzil noto'g'ri yozilgan yoki sahifa o'chirilgan.</p>
      <Link to="/" className="tugma tugma--asosiy">Ustalar ro'yxatiga o'tish</Link>
    </div>
  )
}
