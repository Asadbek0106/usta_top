export default function Yuklanmoqda({ matn = 'Yuklanmoqda…' }) {
  return (
    <p className="holat" role="status" aria-live="polite">
      <span className="aylana" aria-hidden="true" />
      {matn}
    </p>
  )
}

export function XatoBlok({ xato, qaytaUrinish }) {
  if (!xato) return null
  return (
    <div className="xabar xabar--xato" role="alert">
      <span>{xato.message || String(xato)}</span>
      {qaytaUrinish && (
        <button type="button" className="tugma tugma--matn" onClick={qaytaUrinish}>Qayta urinish</button>
      )}
    </div>
  )
}
