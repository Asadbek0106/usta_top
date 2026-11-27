import { useState } from 'react'

import { somda } from './utils'
import Yuklanmoqda, { XatoBlok } from './Yuklanmoqda'
import { useSorov } from '../hooks/useSorov'

const KORSATKICHLAR = {
  arizalar: { nomi: 'Arizalar', format: (v) => `${v} ta` },
  daromad: { nomi: 'Daromad', format: somda },
}

// Ustaning shaxsiy statistikasi: asosiy raqamlar, oylar bo'yicha grafik va baholar taqsimoti
export default function Statistika() {
  const { data: s, xato, qaytaYukla } = useSorov('/ustalar/men/statistika/')

  if (xato) return <section className="statistika"><h2>Statistika</h2><XatoBlok xato={xato} qaytaUrinish={qaytaYukla} /></section>
  if (!s) return <section className="statistika"><h2>Statistika</h2><Yuklanmoqda /></section>

  return (
    <section className="statistika" aria-labelledby="statistika-sarlavha">
      <h2 id="statistika-sarlavha">Statistika</h2>
      <div className="stat-kartalar">
        <StatKarta nomi="Jami arizalar" qiymat={s.jami_arizalar} izoh={`Shu oy: ${s.shu_oy.arizalar}`} />
        <StatKarta nomi="Bajarilgan" qiymat={s.holatlar.bajarildi} izoh={`Jarayonda: ${s.holatlar.yangi + (s.holatlar.narx_taklif ?? 0) + s.holatlar.qabul}`} />
        <StatKarta nomi="Daromad" qiymat={somda(s.daromad)} izoh={`Shu oy: ${somda(s.shu_oy.daromad)}`} />
        <StatKarta
          nomi="Bajarish ulushi"
          qiymat={s.bajarish_foizi === null ? '—' : `${s.bajarish_foizi}%`}
          izoh={`Bekor qilingan: ${s.holatlar.bekor}`}
        />
      </div>

      <div className="statistika__ustunlar">
        <OylarGrafigi oylar={s.oylar} />
        <Baholar baholar={s.baholar} reyting={s.reyting} soni={s.sharhlar_soni} />
      </div>

      {s.kategoriyalar.length > 1 && (
        <p className="xira statistika__kategoriyalar">
          Eng ko'p so'ralgan: {s.kategoriyalar.slice(0, 3).map((k) => `${k.nomi} (${k.soni})`).join(', ')}
        </p>
      )}
    </section>
  )
}

function StatKarta({ nomi, qiymat, izoh }) {
  return (
    <div className="stat-karta">
      <p className="stat-karta__nomi">{nomi}</p>
      <p className="stat-karta__qiymat">{qiymat}</p>
      {izoh && <p className="stat-karta__izoh">{izoh}</p>}
    </div>
  )
}

function OylarGrafigi({ oylar }) {
  const [korsatkich, setKorsatkich] = useState('arizalar')
  const { nomi, format } = KORSATKICHLAR[korsatkich]
  const eng = Math.max(...oylar.map((o) => o[korsatkich]), 0)

  return (
    <figure className="grafik">
      <div className="grafik__tepa">
        <figcaption>{nomi}, oxirgi {oylar.length} oy</figcaption>
        <div className="tablar" role="group" aria-label="Ko'rsatkich">
          {Object.entries(KORSATKICHLAR).map(([kalit, k]) => (
            <button key={kalit} type="button" aria-pressed={korsatkich === kalit}
              className={`chip chip--kichik${korsatkich === kalit ? ' chip--tanlangan' : ''}`} onClick={() => setKorsatkich(kalit)}>
              {k.nomi}
            </button>
          ))}
        </div>
      </div>

      {eng === 0 ? (
        <p className="xira grafik__bosh">Bu davrda ma'lumot yo'q.</p>
      ) : (
        <ol className="grafik__ustunlar">
          {oylar.map((o) => {
            const qiymat = o[korsatkich]
            const matn = format(qiymat)
            return (
              <li key={o.oy} className="grafik__oy" tabIndex={0}
                aria-label={`${o.nomi} ${o.oy.slice(0, 4)}: ${matn}, bajarilgan ${o.bajarildi} ta`}>
                <span className="grafik__maydon" aria-hidden="true">
                  <span className="grafik__ustun" style={{ height: `${(qiymat / eng) * 100}%` }} />
                </span>
                <span className="grafik__yorliq" aria-hidden="true">{o.nomi}</span>
                <span className="grafik__tooltip" role="tooltip">
                  <b>{o.nomi} {o.oy.slice(0, 4)}</b>
                  <span>{matn}</span>
                  <span className="xira">Bajarilgan: {o.bajarildi} ta</span>
                </span>
              </li>
            )
          })}
        </ol>
      )}

      <details className="grafik__jadval">
        <summary>Jadval ko'rinishida</summary>
        <table className="jadval">
          <thead><tr><th scope="col">Oy</th><th scope="col">Arizalar</th><th scope="col">Bajarilgan</th><th scope="col">Daromad</th></tr></thead>
          <tbody>
            {oylar.map((o) => (
              <tr key={o.oy}><td>{o.nomi} {o.oy.slice(0, 4)}</td><td>{o.arizalar}</td><td>{o.bajarildi}</td><td>{somda(o.daromad)}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  )
}

function Baholar({ baholar, reyting, soni }) {
  const eng = Math.max(...Object.values(baholar), 0)
  return (
    <figure className="baholar">
      <figcaption>
        Baholar {reyting !== null && <span className="xira">· o'rtacha {reyting.toFixed(1)}, {soni} ta sharh</span>}
      </figcaption>
      {soni === 0 ? (
        <p className="xira grafik__bosh">Hali baho qo'yilmagan.</p>
      ) : (
        <ul className="baholar__royxat">
          {[5, 4, 3, 2, 1].map((b) => (
            <li key={b} aria-label={`${b} yulduz: ${baholar[b]} ta`}>
              <span className="baholar__baho" aria-hidden="true">{b} ★</span>
              <span className="baholar__chiziq" aria-hidden="true">
                <span style={{ width: eng ? `${(baholar[b] / eng) * 100}%` : 0 }} />
              </span>
              <span className="baholar__soni" aria-hidden="true">{baholar[b]}</span>
            </li>
          ))}
        </ul>
      )}
    </figure>
  )
}
