import { useEffect } from 'react'

const ASOSIY = 'Usta'

// Brauzer tabidagi sarlavha: tarix, xatcho'plar va ekran o'quvchilar uchun har sahifada o'zi
export function useSarlavha(matn) {
  useEffect(() => {
    document.title = matn ? `${matn} — ${ASOSIY}` : `${ASOSIY} — uyingiz uchun ishonchli usta`
  }, [matn])
}
