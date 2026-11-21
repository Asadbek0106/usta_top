// Backend sahifa hajmi bilan bir xil bo'lishi kerak (apps/core/pagination.py → page_size = 20)
export const SAHIFA_HAJMI = 20

export default function Sahifalash({ sahifa, jami, hajm = SAHIFA_HAJMI, ozgartir }) {
  const sahifalar = Math.ceil(jami / hajm)
  if (sahifalar <= 1) return null
  return (
    <nav className="sahifalash" aria-label="Sahifalar">
      <button type="button" className="tugma tugma--chiziq" disabled={sahifa <= 1} onClick={() => ozgartir(sahifa - 1)}>
        Oldingi
      </button>
      <span aria-current="page">{sahifa} / {sahifalar}</span>
      <button type="button" className="tugma tugma--chiziq" disabled={sahifa >= sahifalar} onClick={() => ozgartir(sahifa + 1)}>
        Keyingi
      </button>
    </nav>
  )
}
