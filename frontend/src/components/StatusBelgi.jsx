const MAVJUD = new Set(['yangi', 'qabul', 'bajarildi', 'bekor'])

export default function StatusBelgi({ status, nomi }) {
  return <span className={`status status--${MAVJUD.has(status) ? status : 'yangi'}`}>{nomi}</span>
}
