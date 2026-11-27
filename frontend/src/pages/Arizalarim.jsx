import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Yulduzlar } from '../components/Reyting'
import { RasmlarGalereyasi } from '../components/RasmTanlash'
import Sahifalash from '../components/Sahifalash'
import StatusBelgi from '../components/StatusBelgi'
import UstaJavobi from '../components/UstaJavobi'
import { sana, somda } from '../components/utils'
import Yuklanmoqda, { XatoBlok } from '../components/Yuklanmoqda'
import { useSarlavha } from '../hooks/useSarlavha'
import { useSorov } from '../hooks/useSorov'

const STATUSLAR = [
  ['', 'Barcha holatlar'], ['yangi', 'Yangi'], ['narx_taklif', 'Narx taklif qilingan'], ['qabul', 'Qabul qilingan'],
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

  // Muvaffaqiyatli bo'lsa true qaytaradi (forma yopilishi uchun)
  const amal = async (nomi, body) => {
    if (band) return false
    setBand(true)
    setXato('')
    try {
      yangila(await api(`/arizalar/${ariza.id}/${nomi}/`, { method: 'POST', body: body ?? {} }))
      return true
    } catch (e) {
      setXato(e.message)
      // Usta shu orada narxni o'zgartirgan: kartadagi narxni yangilab, mijozga yangisini ko'rsatamiz
      if (e.data?.code === 'narx_ozgargan') api(`/arizalar/${ariza.id}/`).then(yangila).catch(() => {})
      return false
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
      <RasmlarGalereyasi rasmlar={ariza.rasmlar} />
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
        {ariza.kelishilgan_narx != null
          ? <div><dt>Kelishilgan narx</dt><dd>{somda(ariza.kelishilgan_narx)}</dd></div>
          : ariza.taklif_narx != null
            ? <div><dt>Taklif qilingan narx</dt><dd>{somda(ariza.taklif_narx)}</dd></div>
            : !tugadi && <div><dt>Narx</dt><dd className="xira">Usta hali narx aytmagan</dd></div>}
        <div><dt>Yuborilgan</dt><dd><time dateTime={ariza.yaratilgan}>{sana(ariza.yaratilgan)}</time></dd></div>
      </dl>

      {ariza.tarix?.length > 0 && <Tarix tarix={ariza.tarix} />}

      {xato && <p className="xabar xabar--xato" role="alert">{xato}</p>}

      {ariza.status === 'narx_taklif' && (
        <NarxTaklifi ariza={ariza} ustamanmi={ustamanmi} band={band} amal={amal} />
      )}

      {!tugadi && (
        <div className="ariza__amallar">
          {ustamanmi && ariza.status === 'yangi' && (
            <NarxFormasi arizaId={ariza.id} band={band} yuborish={(body) => amal('narx-taklif', body)}
              izoh="Tavsif va rasmlarni ko'rib, ish narxini yozing. Mijoz rozi bo'lsa, ish boshlanadi." />
          )}
          {!ustamanmi && ariza.status === 'yangi' && (
            <p className="xira ariza__izoh">Usta arizani ko'rib narx taklif qiladi. Narxga rozi bo'lsangiz, ish boshlanadi.</p>
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

// Ariza "Narx taklif qilindi" holatida: mijoz rozi bo'ladi yoki rad etadi, usta esa narxni o'zgartira oladi
function NarxTaklifi({ ariza, ustamanmi, band, amal }) {
  const [rad, setRad] = useState(false)
  const [sabab, setSabab] = useState('')
  const [ozgartirish, setOzgartirish] = useState(false)

  return (
    <div className="taklif" role="region" aria-label="Narx taklifi">
      <p className="taklif__narx">
        <span>{ustamanmi ? 'Sizning taklifingiz' : 'Usta taklif qilgan narx'}</span>
        <strong>{somda(ariza.taklif_narx)}</strong>
      </p>
      {ariza.taklif_izoh && <p className="taklif__izoh">{ariza.taklif_izoh}</p>}

      {ustamanmi ? (
        ozgartirish ? (
          <NarxFormasi arizaId={ariza.id} band={band} boshlangich={ariza.taklif_narx} tugma="Yangi narxni yuborish"
            boshIzoh={ariza.taklif_izoh}
            yuborish={async (body) => (await amal('narx-taklif', body)) && setOzgartirish(false)}
            bekor={() => setOzgartirish(false)} />
        ) : (
          <div className="taklif__tugmalar">
            <p className="xira">Mijoz javobini kutyapsiz.</p>
            <button type="button" className="tugma tugma--matn" onClick={() => setOzgartirish(true)}>Narxni o'zgartirish</button>
          </div>
        )
      ) : rad ? (
        <form className="taklif__rad" onSubmit={async (e) => {
          e.preventDefault()
          if (await amal('narx-rad', { sabab: sabab.trim() })) setRad(false)
        }}>
          <label htmlFor={`sabab-${ariza.id}`}>Nega rozi emassiz? (ixtiyoriy, usta ko'radi)</label>
          <textarea id={`sabab-${ariza.id}`} rows={2} maxLength={400} value={sabab} onChange={(e) => setSabab(e.target.value)}
            placeholder="Masalan: qimmat, 300 000 so'mga kelisha olamizmi?" />
          <div className="taklif__tugmalar">
            <button type="submit" className="tugma tugma--xavfli" disabled={band}>Narxni rad etish</button>
            <button type="button" className="tugma tugma--matn" onClick={() => setRad(false)}>Ortga</button>
          </div>
        </form>
      ) : (
        <div className="taklif__tugmalar">
          <button type="button" className="tugma tugma--asosiy" disabled={band}
            onClick={() => amal('narx-rozi', { narx: ariza.taklif_narx })}>
            Roziman, ishni boshlasin
          </button>
          <button type="button" className="tugma tugma--chiziq" disabled={band} onClick={() => setRad(true)}>Rozi emasman</button>
        </div>
      )}
    </div>
  )
}

function NarxFormasi({ arizaId, band, yuborish, izoh, boshlangich, boshIzoh = '', tugma = 'Narx taklif qilish', bekor }) {
  const [narx, setNarx] = useState(boshlangich ? String(Math.round(Number(boshlangich))) : '')
  const [matn, setMatn] = useState(boshIzoh)
  const [xato, setXato] = useState('')

  const jonat = (e) => {
    e.preventDefault()
    if (!(Number(narx) > 0)) return setXato("Narxni so'mda kiriting.")
    setXato('')
    yuborish({ narx, izoh: matn.trim() })
  }

  return (
    <form className="narx-forma" onSubmit={jonat} noValidate>
      {izoh && <p className="xira narx-forma__izoh">{izoh}</p>}
      <div className="narx-forma__qator">
        <label className="sr-only" htmlFor={`narx-${arizaId}`}>Narx, so'm</label>
        <input id={`narx-${arizaId}`} type="number" inputMode="numeric" min="1" step="1000" placeholder="Narx, so'm"
          value={narx} onChange={(e) => setNarx(e.target.value)} aria-invalid={xato ? true : undefined} />
        <label className="sr-only" htmlFor={`izoh-${arizaId}`}>Izoh</label>
        <input id={`izoh-${arizaId}`} maxLength={1000} placeholder="Izoh (ixtiyoriy): material narxi ichida, 1 kunda bitadi"
          value={matn} onChange={(e) => setMatn(e.target.value)} />
      </div>
      {xato && <small className="maydon__xato" role="alert">{xato}</small>}
      <div className="taklif__tugmalar">
        <button type="submit" className="tugma tugma--asosiy" disabled={band}>{tugma}</button>
        {bekor && <button type="button" className="tugma tugma--matn" onClick={bekor}>Ortga</button>}
      </div>
    </form>
  )
}

const tarixNomi = (t) => {
  if (!t.eski_status) return 'Ariza yuborildi'
  if (t.eski_status === t.yangi_status) return "Narx o'zgartirildi"
  return `${t.eski_status_nomi} → ${t.yangi_status_nomi}`
}

function Tarix({ tarix }) {
  return (
    <details className="tarix">
      <summary>Ariza tarixi ({tarix.length})</summary>
      <ol className="tarix__royxat">
        {tarix.map((t) => (
          <li key={t.id} className={`tarix__qadam tarix__qadam--${t.yangi_status}`}>
            <span className="tarix__nomi">{tarixNomi(t)}</span>
            {t.izoh && <span className="tarix__izoh">{t.izoh}</span>}
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
