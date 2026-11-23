import { useState } from 'react'
import { Link } from 'react-router-dom'

import Reyting from '../components/Reyting'
import Sahifalash from '../components/Sahifalash'
import SevimliTugma from '../components/SevimliTugma'
import { somda } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

export default function Sevimlilar() {
  useSarlavha('Sevimli ustalar')
  const [sahifa, setSahifa] = useState(1)
  const { data, xato, yuklanmoqda, yangilanmoqda, qaytaYukla, ozgartir } = useSorov(
    '/ustalar/sevimlilar/', { page: sahifa > 1 ? sahifa : '' },
  )

  // Olib tashlangan usta ro'yxatda darhol yo'qolmaydi: adashib bosilsa, qaytadan saqlash mumkin
  const ozgardi = (id) => (qiymat) => ozgartir((n) => ({
    ...n, results: n.results.map((u) => (u.id === id ? { ...u, sevimli: qiymat } : u)),
  }))

  return (
    <div className="sevimlilar-sahifa">
      <h1>Sevimli ustalar</h1>
      <p className="xira">Yoqqan ustalarni shu yerga saqlab qo'ying — keyin qidirib o'tirmaysiz.</p>

      <XatoBlok xato={xato} qaytaUrinish={qaytaYukla} />
      {!data && yuklanmoqda && <Yuklanmoqda matn="Yuklanmoqda…" />}

      {data?.count === 0 && (
        <div className="bosh">
          <p>Hozircha saqlangan usta yo'q.</p>
          <p className="xira">Usta sahifasida yoki ro'yxatda ♡ tugmasini bosing.</p>
          <Link to="/" className="tugma tugma--asosiy">Ustalarni ko'rish</Link>
        </div>
      )}

      {data?.results.length > 0 && (
        <ol className={`ustalar${yangilanmoqda ? ' ustalar--yangilanmoqda' : ''}`}>
          {data.results.map((u) => (
            <li key={u.id} className={`usta-qator${u.sevimli ? '' : ' usta-qator--olingan'}`}>
              <Link to={`/ustalar/${u.id}`} className="usta-qator__havola">
                <span className="usta-qator__ism">{u.ism || 'Ismsiz usta'}</span>
                <span className="usta-qator__ish">{u.kategoriyalar.join(', ')}</span>
                <span className="usta-qator__shahar">
                  {u.shahar}
                  {u.eng_arzon !== null && <span className="usta-qator__narx">{somda(u.eng_arzon)} dan</span>}
                </span>
              </Link>
              <Reyting qiymat={u.reyting} soni={u.sharhlar_soni} />
              <SevimliTugma ixcham ustaId={u.id} sevimli={u.sevimli} ozgardi={ozgardi(u.id)} />
            </li>
          ))}
        </ol>
      )}
      {data && <Sahifalash sahifa={sahifa} jami={data.count} ozgartir={setSahifa} />}
    </div>
  )
}
