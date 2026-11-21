// Reyting yorlig'i: hi-vis sariq — butun dizayndagi yagona yorqin rang
export default function Reyting({ qiymat, soni }) {
  if (qiymat === null || qiymat === undefined) {
    return <span className="reyting reyting--yoq">Hali baho yo'q</span>
  }
  return (
    <span className="reyting" role="img" aria-label={`Reyting ${Number(qiymat).toFixed(1)} / 5, ${soni} ta sharh`}>
      <span className="reyting__son" aria-hidden="true">{Number(qiymat).toFixed(1)}</span>
      <span className="reyting__soni" aria-hidden="true">{soni} sharh</span>
    </span>
  )
}

export function Yulduzlar({ baho }) {
  const b = Math.max(0, Math.min(5, Math.round(baho)))
  return (
    <span className="yulduzlar" role="img" aria-label={`${b} / 5`}>
      <span aria-hidden="true">{'★'.repeat(b)}<span className="yulduzlar__bosh">{'★'.repeat(5 - b)}</span></span>
    </span>
  )
}
