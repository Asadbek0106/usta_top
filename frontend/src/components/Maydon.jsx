import { Children, cloneElement, isValidElement } from 'react'

// Forma maydoni: yorliq, kiritish elementi va backend qaytargan xato bir joyda.
// Ichidagi input'ga id, aria-invalid va aria-describedby avtomatik qo'shiladi —
// ekran o'quvchi xato matnini maydon bilan birga o'qiydi.
export default function Maydon({ nomi, yorliq, xatolar, xato: tashqiXato, children, izoh }) {
  const xato = tashqiXato ?? xatolar?.[nomi]
  const izohId = `${nomi}-izoh`
  const xatoId = `${nomi}-xato`
  const tasvir = xato ? xatoId : izoh ? izohId : undefined

  const bola = Children.only(children)
  const element = isValidElement(bola)
    ? cloneElement(bola, {
      id: bola.props.id ?? nomi,
      'aria-invalid': xato ? true : undefined,
      'aria-describedby': tasvir,
    })
    : bola

  return (
    <div className={`maydon${xato ? ' maydon--xato' : ''}`}>
      <label htmlFor={bola.props?.id ?? nomi}>{yorliq}</label>
      {element}
      {izoh && !xato && <small id={izohId} className="maydon__izoh">{izoh}</small>}
      {xato && <small id={xatoId} className="maydon__xato">{[xato].flat().join(' ')}</small>}
    </div>
  )
}

export function UmumiyXato({ xatolar }) {
  const matn = xatolar?.detail || xatolar?.non_field_errors
  if (!matn) return null
  return <p className="xabar xabar--xato" role="alert">{[matn].flat().join(' ')}</p>
}
