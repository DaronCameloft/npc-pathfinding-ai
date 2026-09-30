/**
 * Reloj de animación sobre una traza. Es independiente de `tiempo_ms`, que es lo que
 * midió el motor: aquí solo se decide cuántos eventos se muestran por segundo.
 */

import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'

export interface Velocidad {
  etiqueta: string
  eventosPorSegundo: number
}

export const VELOCIDADES: Velocidad[] = [
  { etiqueta: '0.5×', eventosPorSegundo: 40 },
  { etiqueta: '1×', eventosPorSegundo: 120 },
  { etiqueta: '3×', eventosPorSegundo: 360 },
  { etiqueta: '10×', eventosPorSegundo: 1200 },
  { etiqueta: '30×', eventosPorSegundo: 3600 },
  { etiqueta: '100×', eventosPorSegundo: 12000 },
]

/** Velocidad con la que una traza completa dura unos 20 s. */
export function velocidadSugerida(total: number): number {
  const objetivo = total / 20
  let mejor = 1
  VELOCIDADES.forEach((v, i) => {
    if (Math.abs(v.eventosPorSegundo - objetivo) < Math.abs(VELOCIDADES[mejor].eventosPorSegundo - objetivo)) mejor = i
  })
  return Math.max(1, mejor)
}

export function usePlayback(total: Ref<number>) {
  const posicion = ref(0)
  const reproduciendo = ref(false)
  const velocidad = ref(1)
  let cuadro = 0
  let ultimo = 0

  const indice = computed(() => Math.min(total.value, Math.floor(posicion.value)))
  const terminada = computed(() => total.value > 0 && indice.value >= total.value)
  const progreso = computed(() => (total.value ? posicion.value / total.value : 0))

  function tick(ahora: number) {
    const dt = Math.min(0.1, (ahora - ultimo) / 1000)
    ultimo = ahora
    posicion.value = Math.min(total.value, posicion.value + dt * VELOCIDADES[velocidad.value].eventosPorSegundo)
    if (posicion.value >= total.value) {
      reproduciendo.value = false
      return
    }
    cuadro = requestAnimationFrame(tick)
  }

  function reproducir() {
    if (!total.value) return
    if (terminada.value) posicion.value = 0
    reproduciendo.value = true
    ultimo = performance.now()
    cancelAnimationFrame(cuadro)
    cuadro = requestAnimationFrame(tick)
  }
  function pausar() {
    reproduciendo.value = false
    cancelAnimationFrame(cuadro)
  }
  const alternar = () => (reproduciendo.value ? pausar() : reproducir())
  function irA(n: number) {
    posicion.value = Math.max(0, Math.min(total.value, n))
  }
  function paso(n = 1) {
    pausar()
    irA(Math.floor(posicion.value) + n)
  }
  function reiniciar() {
    pausar()
    posicion.value = 0
  }
  function alFinal() {
    pausar()
    posicion.value = total.value
  }

  watch(total, () => {
    pausar()
    posicion.value = 0
  })
  onBeforeUnmount(pausar)

  return { indice, posicion, reproduciendo, velocidad, terminada, progreso, reproducir, pausar, alternar, irA, paso, reiniciar, alFinal }
}
