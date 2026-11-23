import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import Reyting from '../components/Reyting'
import Sahifalash from '../components/Sahifalash'
import SevimliTugma from '../components/SevimliTugma'
import { somda, useMalumotnoma } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

const SARALASH = [
  { qiymat: '-reyting', nomi: 'Avval reytingi yuqori' },
  { qiymat: '-sharhlar_soni', nomi: "Avval sharhi ko'p" },
  { qiymat: 'eng_arzon', nomi: 'Avval arzonlari' },
  { qiymat: '-tajriba_yil', nomi: 'Avval tajribalilari' },
  { qiymat: '-yaratilgan', nomi: 'Avval yangilari' },
]
const NARXLAR = [100000, 200000, 300000, 500000]
// Bu kalitlar "filtr" hisoblanadi; page va ordering — yo'q (ular "tozalash" tugmasini chiqarmaydi)
const FILTR_KALITLARI = ['search', 'kategoriya', 'shahar', 'narx_max', 'reyting_min']

export default function Katalog() {
  useSarlavha(null)
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const shaharlar = useMalumotnoma('shaharlar')
  const kategoriyalar = useMalumotnoma('kategoriyalar')
  const filtr = Object.fromEntries(params)
  const sahifa = Math.max(1, Number(filtr.page) || 1)
  const { data: natija, xato, yuklanmoqda, yangilanmoqda, qaytaYukla, ozgartir: natijaniOzgartir } = useSorov('/ustalar/', filtr)
  const sevimliOzgardi = (id) => (qiymat) => natijaniOzgartir((n) => ({
    ...n, results: n.results.map((u) => (u.id === id ? { ...u, sevimli: qiymat } : u)),
  }))

  // Qidiruv maydoni URL bilan sinxron: "orqaga" bosilsa yoki filtr tozalansa matn ham yangilanadi
  const urlQidiruv = params.get('search') ?? ''
  const [qidiruv, setQidiruv] = useState(urlQidiruv)
  const [oldingiUrl, setOldingiUrl] = useState(urlQidiruv)
  if (urlQidiruv !== oldingiUrl) {
    setOldingiUrl(urlQidiruv)
    setQidiruv(urlQidiruv)
  }

  // Filtr o'zgarsa birinchi sahifaga qaytiladi; URL'da saqlanadi — havolani ulashish mumkin
  const ozgartir = (yangi, { sahifaniSaqla = false } = {}) => {
    const keyingi = { ...filtr, ...(sahifaniSaqla ? {} : { page: '' }), ...yangi }
    setParams(Object.fromEntries(Object.entries(keyingi).filter(([, v]) => v !== '' && v != null)))
  }

  const sahifaniOzgartir = (p) => {
    ozgartir({ page: p > 1 ? p : '' }, { sahifaniSaqla: true })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const filtrBor = FILTR_KALITLARI.some((k) => filtr[k])
  const tanlanganKategoriya = kategoriyalar.find((k) => k.slug === filtr.kategoriya)

  return (
    <>
      <section className="kirish-blok">
        <h1>Uyingizdagi ishni kimga topshirasiz?</h1>
        <p className="kirish-blok__matn">
          Shahringizdagi tekshirilgan ustalar, ularning narxlari va mijozlar qo'ygan baholar — bir joyda.
        </p>
        <div className="kategoriyalar" role="group" aria-label="Kategoriya">
          <button
            type="button"
            className={`chip${!filtr.kategoriya ? ' chip--tanlangan' : ''}`}
            aria-pressed={!filtr.kategoriya}
            onClick={() => ozgartir({ kategoriya: '' })}
          >
            Barcha ishlar
          </button>
          {kategoriyalar.map((k) => (
            <button
              key={k.id}
              type="button"
              className={`chip${filtr.kategoriya === k.slug ? ' chip--tanlangan' : ''}`}
              aria-pressed={filtr.kategoriya === k.slug}
              onClick={() => ozgartir({ kategoriya: k.slug })}
            >
              {k.nomi}
            </button>
          ))}
        </div>
      </section>

      <div className="katalog">
        <aside className="filtrlar" aria-label="Filtrlar">
          <form role="search" onSubmit={(e) => { e.preventDefault(); ozgartir({ search: qidiruv.trim() }) }}>
            <label htmlFor="qidiruv">Ism yoki tavsif</label>
            <div className="qidiruv">
              <input id="qidiruv" type="search" value={qidiruv} onChange={(e) => setQidiruv(e.target.value)}
                placeholder="Masalan, Alisher" enterKeyHint="search" />
              <button type="submit" className="tugma tugma--ikkinchi">Izlash</button>
            </div>
          </form>

          <label htmlFor="shahar">Shahar</label>
          <select id="shahar" value={filtr.shahar ?? ''} onChange={(e) => ozgartir({ shahar: e.target.value })}>
            <option value="">Barcha shaharlar</option>
            {shaharlar.map((s) => <option key={s.id} value={s.id}>{s.nomi}</option>)}
          </select>

          <label htmlFor="narx_max">Narx</label>
          <select id="narx_max" value={filtr.narx_max ?? ''} onChange={(e) => ozgartir({ narx_max: e.target.value })}>
            <option value="">Farqi yo'q</option>
            {NARXLAR.map((n) => <option key={n} value={n}>{somda(n)} gacha</option>)}
          </select>

          <label htmlFor="reyting_min">Reyting</label>
          <select id="reyting_min" value={filtr.reyting_min ?? ''} onChange={(e) => ozgartir({ reyting_min: e.target.value })}>
            <option value="">Har qanday</option>
            <option value="4.5">4.5 va yuqori</option>
            <option value="4">4.0 va yuqori</option>
          </select>

          {filtrBor && (
            <button type="button" className="tugma tugma--matn filtrlar__tozalash"
              onClick={() => setParams(filtr.ordering ? { ordering: filtr.ordering } : {})}>
              Filtrlarni tozalash
            </button>
          )}
        </aside>

        <section className="natijalar" aria-labelledby="natijalar-soni" aria-busy={yuklanmoqda}>
          <div className="natijalar__tepa">
            <p id="natijalar-soni" aria-live="polite">
              {natija ? `${natija.count} ta usta topildi` : yuklanmoqda ? 'Qidirilmoqda…' : ''}
              {tanlanganKategoriya && natija && <span className="xira"> · {tanlanganKategoriya.nomi}</span>}
            </p>
            <label className="saralash">
              <span className="sr-only">Saralash</span>
              <select value={filtr.ordering ?? '-reyting'} onChange={(e) => ozgartir({ ordering: e.target.value })}>
                {SARALASH.map((s) => <option key={s.qiymat} value={s.qiymat}>{s.nomi}</option>)}
              </select>
            </label>
          </div>

          <XatoBlok xato={xato} qaytaUrinish={qaytaYukla} />
          {!natija && yuklanmoqda && <Yuklanmoqda matn="Ustalar yuklanmoqda…" />}

          {natija?.results.length === 0 && (
            <div className="bosh">
              <p>Bu shartlarga mos usta topilmadi.</p>
              {filtrBor && <p>Narx yoki reyting chegarasini kengaytirib ko'ring.</p>}
            </div>
          )}

          {natija?.results.length > 0 && (
            <ol className={`ustalar${yangilanmoqda ? ' ustalar--yangilanmoqda' : ''}`}>
              {natija.results.map((u) => (
                <li key={u.id} className="usta-qator">
                  <Link to={`/ustalar/${u.id}`} className="usta-qator__havola">
                    <span className="usta-qator__ism">{u.ism || 'Ismsiz usta'}</span>
                    <span className="usta-qator__ish">{u.kategoriyalar.join(', ')}</span>
                    <span className="usta-qator__shahar">
                      {u.shahar}
                      {u.eng_arzon !== null && <span className="usta-qator__narx">{somda(u.eng_arzon)} dan</span>}
                    </span>
                  </Link>
                  <Reyting qiymat={u.reyting} soni={u.sharhlar_soni} />
                  {user && (
                    <SevimliTugma ixcham ustaId={u.id} sevimli={u.sevimli} ozgardi={sevimliOzgardi(u.id)} />
                  )}
                </li>
              ))}
            </ol>
          )}

          {natija && <Sahifalash sahifa={sahifa} jami={natija.count} ozgartir={sahifaniOzgartir} />}
        </section>
      </div>
    </>
  )
}
