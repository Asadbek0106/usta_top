import { useCallback, useEffect, useState } from 'react'

import { api, bekorQilinganmi } from '../api/client'

// GET so'rov uchun umumiy hook.
// - yol yoki params o'zgarsa eski so'rov bekor qilinadi (AbortController), shuning uchun
//   sekin kelgan eski javob yangisining ustiga yozilib qolmaydi (race condition yo'q)
// - qayta yuklashda eski ma'lumot ekranda qoladi, faqat `yangilanmoqda` true bo'ladi
// - yol null bo'lsa so'rov yuborilmaydi
export function useSorov(yol, params) {
  // Parametrlar satrga aylantiriladi: har renderda yangi obyekt bo'lsa ham so'rov takrorlanmaydi
  const qs = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v !== '' && v !== null && v !== undefined),
  ).toString()
  const [versiya, setVersiya] = useState(0)
  const kalit = yol === null ? null : `${yol}?${qs}#${versiya}`

  // `kalit` — qaysi so'rovning javobi saqlanganini bildiradi. Joriy kalit bilan mos kelmasa,
  // demak yangi so'rov ketyapti: yuklanish holati alohida state'siz, shu solishtirishdan chiqadi
  const [holat, setHolat] = useState({ data: null, xato: null, kalit: null })

  useEffect(() => {
    if (kalit === null) return undefined
    const boshqaruv = new AbortController()
    api(yol, { params: Object.fromEntries(new URLSearchParams(qs)), signal: boshqaruv.signal })
      .then((data) => setHolat({ data, xato: null, kalit }))
      .catch((xato) => {
        if (!bekorQilinganmi(xato)) setHolat((h) => ({ ...h, xato, kalit }))
      })
    return () => boshqaruv.abort()
  }, [kalit, yol, qs])

  // Amaldan keyin ro'yxatni qayta so'ramasdan, javob bilan qo'lda yangilash uchun
  const ozgartir = useCallback((fn) => setHolat((h) => ({ ...h, data: typeof fn === 'function' ? fn(h.data) : fn })), [])
  const qaytaYukla = useCallback(() => setVersiya((v) => v + 1), [])

  const yuklanmoqda = kalit !== null && holat.kalit !== kalit
  return {
    data: holat.data,
    xato: yuklanmoqda ? null : holat.xato,
    yuklanmoqda,
    // Birinchi yuklash emas, bor ma'lumotni yangilash ketyapti
    yangilanmoqda: yuklanmoqda && holat.data !== null,
    ozgartir,
    qaytaYukla,
  }
}
