/** Conteos acumulados de la traza hasta el evento actual: por línea del pseudocódigo y por tipo. */

import { computed, type Ref } from 'vue'
import type { EventoBusqueda } from '../../core/types'

export interface Conteos {
  lineas: Record<number, number>
  expandidos: number
  frontera: number
}

export function useConteos(traza: Ref<EventoBusqueda[]>, indice: Ref<number>) {
  let lineas: Record<number, number> = {}
  let expandidos = 0
  let frontera = 0
  let aplicado = 0
  let fuente: EventoBusqueda[] = []

  return computed<Conteos>(() => {
    const tope = Math.min(indice.value, traza.value.length)
    if (fuente !== traza.value || tope < aplicado) {
      lineas = {}
      expandidos = frontera = aplicado = 0
      fuente = traza.value
    }
    for (let i = aplicado; i < tope; i++) {
      const e = fuente[i]
      lineas[e.linea] = (lineas[e.linea] ?? 0) + 1
      if (e.tipo === 'expandido') expandidos++
      else frontera++
    }
    aplicado = tope
    return { lineas: { ...lineas }, expandidos, frontera }
  })
}
