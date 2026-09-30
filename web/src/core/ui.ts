/** Preferencias de interfaz que se recuerdan entre visitas (solo comodidad: la app funciona sin ellas). */

import { reactive, watch } from 'vue'

const CLAVE_SIDEBAR = 'arcadialabs.sidebar-compacta'
const CLAVE_PANEL = 'arcadialabs.panel-explorar'
const CLAVE_COLOR = 'arcadialabs.resaltar-resultados'

function leer(clave: string, porDefecto: boolean): boolean {
  try {
    const valor = localStorage.getItem(clave)
    return valor === null ? porDefecto : valor === '1'
  } catch {
    return porDefecto
  }
}

function guardar(clave: string, valor: boolean) {
  try {
    localStorage.setItem(clave, valor ? '1' : '0')
  } catch {
    /* almacenamiento no disponible */
  }
}

export const ui = reactive({
  compacta: leer(CLAVE_SIDEBAR, false),
  /** Pseudocódigo y métricas de la pantalla Explorar. */
  panelLateral: leer(CLAVE_PANEL, true),
  /** Prueba: colorea en Comparar el mejor (verde) y el peor (rojo) resultado de cada métrica. */
  resaltarResultados: leer(CLAVE_COLOR, true),
})

watch(() => ui.compacta, (valor) => guardar(CLAVE_SIDEBAR, valor))
watch(() => ui.panelLateral, (valor) => guardar(CLAVE_PANEL, valor))
watch(() => ui.resaltarResultados, (valor) => guardar(CLAVE_COLOR, valor))

export const alternarSidebar = () => {
  ui.compacta = !ui.compacta
}
export const alternarResaltado = () => {
  ui.resaltarResultados = !ui.resaltarResultados
}
export const alternarPanel = () => {
  ui.panelLateral = !ui.panelLateral
}
