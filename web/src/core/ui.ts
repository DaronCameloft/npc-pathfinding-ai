/** Preferencias de interfaz que se recuerdan entre visitas (solo comodidad: la app funciona sin ellas). */

import { reactive, watch } from 'vue'

const CLAVE = 'arcadialabs.sidebar-compacta'

function leer(): boolean {
  try {
    return localStorage.getItem(CLAVE) === '1'
  } catch {
    return false
  }
}

export const ui = reactive({ compacta: leer() })

watch(
  () => ui.compacta,
  (valor) => {
    try {
      localStorage.setItem(CLAVE, valor ? '1' : '0')
    } catch {
      /* almacenamiento no disponible */
    }
  },
)

export const alternarSidebar = () => {
  ui.compacta = !ui.compacta
}
