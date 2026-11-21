import { Component } from 'react'

// Render vaqtidagi kutilmagan xato butun ilovani oq ekranga aylantirmasligi uchun.
// `kalit` o'zgarsa (boshqa sahifaga o'tilsa) xato holati tozalanadi.
export default class XatoChegarasi extends Component {
  state = { xato: null, kalit: this.props.kalit }

  static getDerivedStateFromError(xato) {
    return { xato }
  }

  static getDerivedStateFromProps(props, state) {
    if (props.kalit !== state.kalit) return { xato: null, kalit: props.kalit }
    return null
  }

  componentDidCatch(xato, info) {
    console.error('Sahifada xato:', xato, info.componentStack)
  }

  render() {
    if (!this.state.xato) return this.props.children
    return (
      <div className="bosh" role="alert">
        <h1>Nimadir noto'g'ri ketdi</h1>
        <p>Sahifani ko'rsatishda xato yuz berdi. Sahifani yangilab ko'ring.</p>
        <button type="button" className="tugma tugma--asosiy" onClick={() => window.location.reload()}>
          Sahifani yangilash
        </button>
      </div>
    )
  }
}
