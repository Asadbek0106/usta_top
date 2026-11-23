import { sana } from './utils'

// Ustaning sharhga yozgan ochiq javobi: sharh ostida, alohida blokda
export default function UstaJavobi({ matn, vaqt }) {
  return (
    <div className="usta-javobi">
      <p className="usta-javobi__sarlavha">
        Ustaning javobi{vaqt && <> · <time dateTime={vaqt}>{sana(vaqt)}</time></>}
      </p>
      <p>{matn}</p>
    </div>
  )
}
