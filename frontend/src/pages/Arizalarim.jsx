import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Yulduzlar } from '../components/Reyting'
import Sahifalash from '../components/Sahifalash'
import StatusBelgi from '../components/StatusBelgi'
import UstaJavobi from '../components/UstaJavobi'
import { sana, somda } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

const STATUSLAR = [
  ['', 'Barcha holatlar'], ['yangi', 'Yangi'], ['qabul', 'Qabul qilingan'],
  ['bajarildi', 'Bajarilgan'], ['bekor', 'Bekor qilingan'],
]
const ROLLAR = [['', 'Hammasi'], ['mijoz', 'Men yuborganlar'], ['usta', 'Menga kelganlar']]

export default function Arizalarim() {
  useSarlavha('Arizalarim')
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const filtr = Object.fromEntries(params)
  const sahifa = Math.max(1, Number(filtr.page) || 1)
  const { data: natija, xato, yuklanmoqda, yangilanmoqda, ozgartir: natijaniOzgartir, qaytaYukla } = useSorov('/arizalar/', filtr)

  // "Ariza yuborildi" xabari bir marta ko'rsatiladi: sahifa yangilansa yoki orqaga qaytilsa qayta chiqmaydi
  const [xabar] = useState(location.state?.xabar)
  useEffect(() => {
    if (location.state?.xabar) navigate(location.pathname + location.search, { replace: true, state: null })
  }, [location, navigate])

  const ozgartir = (yangi) => {
    const k = { ...filtr, page: '', ...yangi }
    setParams(Object.fromEntries(Object.entries(k).filter(([, v]) => v !== '' && v != null)))
  }

  // Amal bajarilgach ro'yxatdagi bitta arizani javob bilan almashtiramiz — butun ro'yxatni qayta yuklamasdan
  const yangila = (ariza) =>
    natijaniOzgartir((n) => ({ ...n, results: n.results.map((a) => (a.id === ariza.id ? ariza : a)) }))

  const filtrBor = Boolean(filtr.status || filtr.rol)

  return (
    <div className="arizalar-sahifa">
      <h1>Arizalarim</h1>
      {xabar && <p className="xabar xabar--ok" role="status">{xabar}</p>}

      <div className="arizalar-sahifa__filtr">
        {user.usta_mi ? (
          <div className="tablar" role="group" aria-label="Arizalar turi">
            {ROLLAR.map(([q, nomi]) => (
              <button key={q} type="button" aria-pressed={(filtr.rol ?? '') === q}
                className={`chip${(filtr.rol ?? '') === q ? ' chip--tanlangan' : ''}`} onClick={() => ozgartir({ rol: q })}>
                {nomi}
              </button>
            ))}
          </div>
        ) : <span />}
        <label>
          <span className="sr-only">Holat bo'yicha filtr</span>
          <select value={filtr.status ?? ''} onChange={(e) => ozgartir({ status: e.target.value })}>
            {STATUSLAR.map(([q, n]) => <option key={q} value={q}>{n}</option>)}
          </select>
        </label>
      </div>

      <XatoBlok xato={xato} qaytaUrinish={qaytaYukla} />
      {!natija && yuklanmoqda && <Yuklanmoqda matn="Arizalar yuklanmoqda…" />}

      {natija?.count === 0 && (
        <div className="bosh">
          {filtrBor ? (
            <>
              <p>Bu filtrga mos ariza yo'q.</p>
              <button type="button" className="tugma tugma--chiziq" onClick={() => setParams({})}>Filtrni tozalash</button>
            </>
          ) : (
            <>
              <p>Hozircha ariza yo'q.</p>
              <Link to="/" className="tugma tugma--asosiy">Usta topish</Link>
            </>
          )}
        </div>
      )}

      <ul className={`arizalar${yangilanmoqda ? ' ustalar--yangilanmoqda' : ''}`} aria-busy={yuklanmoqda}>
        {natija?.results.map((a) => <ArizaKartasi key={a.id} ariza={a} men={user} yangila={yangila} />)}
      </ul>
      {natija && <Sahifalash sahifa={sahifa} jami={natija.count} ozgartir={(p) => ozgartir({ page: p > 1 ? p : '' })} />}
    </div>
  )
}

function ArizaKartasi({ ariza, men, yangila }) {
  // Ustaning o'ziga kelgan ariza. Telefon emas, id bo'yicha solishtirish ishonchliroq bo'lardi,
  // lekin API ustaning user id'sini qaytarmaydi; telefon esa unikal.
  const ustamanmi = ariza.usta.telefon === men.telefon
  const [xato, setXato] = useState('')
  const [band, setBand] = useState(false)
  const [narx, setNarx] = useState('')

  const amal = async (nomi, body) => {
    if (band) return
    setBand(true)
    setXato('')
    try {
      yangila(await api(`/arizalar/${ariza.id}/${nomi}/`, { method: 'POST', body: body ?? {} }))
    } catch (e) {
      setXato(e.message)
    } finally {
      setBand(false)
    }
  }

  const tugadi = ariza.status === 'bajarildi' || ariza.status === 'bekor'

  return (
    <li className="ariza">
      <div className="ariza__tepa">
        <h2>{ariza.kategoriya}</h2>
        <StatusBelgi status={ariza.status} nomi={ariza.status_nomi} />
      </div>
      <p className="ariza__tavsif">{ariza.tavsif}</p>
      <dl className="ariza__malumot">
        <div><dt>Manzil</dt><dd>{ariza.manzil}</dd></div>
        {ustamanmi
          ? <div><dt>Mijoz</dt><dd>{ariza.mijoz}</dd></div>
          : (
            <div>
              <dt>Usta</dt>
              <dd><Link to={`/ustalar/${ariza.usta.id}`}>{ariza.usta.ism || 'Usta'}</Link>, <a href={`tel:${ariza.usta.telefon}`}>{ariza.usta.telefon}</a></dd>
            </div>
          )}
        <div><dt>Kelishilgan narx</dt><dd>{somda(ariza.kelishilgan_narx)}</dd></div>
        <div><dt>Yuborilgan</dt><dd><time dateTime={ariza.yaratilgan}>{sana(ariza.yaratilgan)}</time></dd></div>
      </dl>

      {ariza.tarix?.length > 0 && <Tarix tarix={ariza.tarix} />}

      {xato && <p className="xabar xabar--xato" role="alert">{xato}</p>}

      {!tugadi && (
        <div className="ariza__amallar">
          {ustamanmi && ariza.status === 'yangi' && (
            <form className="qabul" onSubmit={(e) => { e.preventDefault(); amal('qabul', narx ? { kelishilgan_narx: narx } : {}) }}>
              <label className="sr-only" htmlFor={`narx-${ariza.id}`}>Kelishilgan narx, so'm</label>
              <input id={`narx-${ariza.id}`} type="number" inputMode="numeric" min="0" step="1" placeholder="Narx, so'm (ixtiyoriy)"
                value={narx} onChange={(e) => setNarx(e.target.value)} />
              <button type="submit" className="tugma tugma--asosiy" disabled={band}>Qabul qilish</button>
            </form>
          )}
          {ustamanmi && ariza.status === 'qabul' && (
            <button type="button" className="tugma tugma--asosiy" disabled={band} onClick={() => amal('bajarildi')}>
              Bajarildi deb belgilash
            </button>
          )}
          {!ustamanmi && ariza.status === 'qabul' && (
            <p className="xira ariza__izoh">Usta ishni tugatgach, arizani "Bajarildi" deb belgilaydi. Shundan keyin baho qo'yasiz.</p>
          )}
          <button type="button" className="tugma tugma--xavfli" disabled={band}
            onClick={() => window.confirm('Arizani bekor qilasizmi? Bu amalni ortga qaytarib bo\'lmaydi.') && amal('bekor')}>
            Bekor qilish
          </button>
        </div>
      )}

      {ariza.sharh && (
        <div className="ariza__sharh">
          <Yulduzlar baho={ariza.sharh.baho} />
          {ariza.sharh.matn && <p>{ariza.sharh.matn}</p>}
          {ariza.sharh.usta_javobi && <UstaJavobi matn={ariza.sharh.usta_javobi} vaqt={ariza.sharh.javob_vaqti} />}
          {ustamanmi && (
            <JavobFormasi
              arizaId={ariza.id}
              mavjud={ariza.sharh.usta_javobi}
              tayyor={(sharh) => yangila({ ...ariza, sharh })}
            />
          )}
        </div>
      )}

      {!ustamanmi && ariza.status === 'bajarildi' && !ariza.sharh && (
        <SharhFormasi arizaId={ariza.id} tayyor={(sharh) => yangila({ ...ariza, sharh })} />
      )}
    </li>
  )
}

const vaqtMatni = (iso) => {
  const d = new Date(iso)
  const soat = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return `${sana(iso)}, ${soat}`
}

function Tarix({ tarix }) {
  return (
    <details className="tarix">
      <summary>Ariza tarixi ({tarix.length})</summary>
      <ol className="tarix__royxat">
        {tarix.map((t) => (
          <li key={t.id} className={`tarix__qadam tarix__qadam--${t.yangi_status}`}>
            <span className="tarix__nomi">
              {t.eski_status ? `${t.eski_status_nomi} → ${t.yangi_status_nomi}` : 'Ariza yuborildi'}
            </span>
            <span className="xira">
              <time dateTime={t.vaqt}>{vaqtMatni(t.vaqt)}</time>
              {t.kim && <> · {t.kim}</>}
            </span>
          </li>
        ))}
      </ol>
    </details>
  )
}

function JavobFormasi({ arizaId, mavjud, tayyor }) {
  const [ochiq, setOchiq] = useState(false)
  const [matn, setMatn] = useState(mavjud || '')
  const [xato, setXato] = useState('')
  const [band, setBand] = useState(false)

  if (!ochiq) {
    return (
      <button type="button" className="tugma tugma--matn usta-javobi__tugma" onClick={() => setOchiq(true)}>
        {mavjud ? 'Javobni tahrirlash' : 'Sharhga javob yozish'}
      </button>
    )
  }

  const yuborish = async (e) => {
    e.preventDefault()
    if (band) return
    if (!matn.trim()) return setXato('Javob matnini yozing.')
    setBand(true)
    setXato('')
    try {
      tayyor(await api(`/arizalar/${arizaId}/sharh/javob/`, { method: 'POST', body: { matn: matn.trim() } }))
      setOchiq(false)
    } catch (err) {
      setXato(err.message)
    } finally {
      setBand(false)
    }
  }

  return (
    <form className="javob-forma" onSubmit={yuborish}>
      <label htmlFor={`javob-${arizaId}`}>Javobingiz (hamma ko'radi)</label>
      <textarea id={`javob-${arizaId}`} rows={2} maxLength={2000} value={matn} onChange={(e) => setMatn(e.target.value)}
        placeholder="Masalan: Rahmat! Yana murojaat qiling." />
      {xato && <p className="xabar xabar--xato" role="alert">{xato}</p>}
      <div className="javob-forma__tugmalar">
        <button type="submit" className="tugma tugma--ikkinchi" disabled={band}>{band ? 'Saqlanmoqda…' : 'Javobni saqlash'}</button>
        <button type="button" className="tugma tugma--matn" onClick={() => setOchiq(false)}>Bekor</button>
      </div>
    </form>
  )
}

const BAHO_NOMLARI = { 1: 'Juda yomon', 2: 'Yomon', 3: "O'rtacha", 4: 'Yaxshi', 5: "A'lo" }

function SharhFormasi({ arizaId, tayyor }) {
  const [baho, setBaho] = useState(5)
  const [matn, setMatn] = useState('')
  const [xato, setXato] = useState('')
  const [band, setBand] = useState(false)

  const yuborish = async (e) => {
    e.preventDefault()
    if (band) return
    setBand(true)
    setXato('')
    try {
      tayyor(await api(`/arizalar/${arizaId}/sharh/`, { method: 'POST', body: { baho, matn: matn.trim() } }))
    } catch (err) {
      setXato(err.message)
      setBand(false)
    }
  }

  return (
    <form className="sharh-forma" onSubmit={yuborish}>
      <fieldset>
        <legend>Ustaning ishini baholang</legend>
        <div className="baho-tanlash">
          {[1, 2, 3, 4, 5].map((n) => (
            <label key={n} className={n <= baho ? 'faol' : ''} title={BAHO_NOMLARI[n]}>
              <input type="radio" name={`baho-${arizaId}`} value={n} checked={baho === n} onChange={() => setBaho(n)} />
              <span aria-hidden="true">★</span>
              <span className="sr-only">{n} ball — {BAHO_NOMLARI[n]}</span>
            </label>
          ))}
          <span className="baho-tanlash__nomi" aria-hidden="true">{BAHO_NOMLARI[baho]}</span>
        </div>
      </fieldset>
      <label className="sr-only" htmlFor={`matn-${arizaId}`}>Izoh</label>
      <textarea id={`matn-${arizaId}`} rows={2} maxLength={2000} placeholder="Izoh (ixtiyoriy)" value={matn} onChange={(e) => setMatn(e.target.value)} />
      {xato && <p className="xabar xabar--xato" role="alert">{xato}</p>}
      <button type="submit" className="tugma tugma--ikkinchi" disabled={band}>{band ? 'Yuborilmoqda…' : 'Bahoni yuborish'}</button>
    </form>
  )
}
