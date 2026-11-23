import { useState } from 'react'

import { api } from '../api/client'

// Ustani sevimlilarga qo'shish / olib tashlash. Holat darhol o'zgaradi (optimistik),
// server xato qaytarsa eski holatga qaytadi.
export default function SevimliTugma({ ustaId, sevimli, ozgardi, ixcham = false }) {
  const [band, setBand] = useState(false)
  const [xato, setXato] = useState('')

  const bos = async () => {
    if (band) return
    const yangi = !sevimli
    setBand(true)
    setXato('')
    ozgardi?.(yangi)
    try {
      await api(`/ustalar/${ustaId}/sevimli/`, { method: yangi ? 'POST' : 'DELETE' })
    } catch (e) {
      ozgardi?.(!yangi)
      setXato(e.message)
    } finally {
      setBand(false)
    }
  }

  const yorliq = sevimli ? 'Sevimlilardan olib tashlash' : 'Sevimlilarga qo\'shish'
  return (
    <span className="sevimli">
      <button
        type="button"
        className={`sevimli__tugma${sevimli ? ' sevimli__tugma--faol' : ''}${ixcham ? ' sevimli__tugma--ixcham' : ''}`}
        aria-pressed={sevimli}
        aria-label={ixcham ? yorliq : undefined}
        title={yorliq}
        disabled={band}
        onClick={bos}
      >
        <span aria-hidden="true">{sevimli ? '♥' : '♡'}</span>
        {!ixcham && <span>{sevimli ? 'Saqlangan' : 'Saqlash'}</span>}
      </button>
      {xato && <small className="sevimli__xato" role="alert">{xato}</small>}
    </span>
  )
}
