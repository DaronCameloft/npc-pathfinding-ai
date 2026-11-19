/**
 * Reproducción por pasos discretos para trazas cortas (decisiones de Kruskal,
 * caminos aumentantes, filas de la tabla de la mochila). A diferencia de
 * `usePlayback`, cada paso dura un tiempo fijo para que se pueda leer.
 */

import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'

export function usePasos(total: Ref<number>, msPorPaso: Ref<number> | number = 900) {
  const indice = ref(0)
  const reproduciendo = ref(false)
  let temporizador = 0

  const duracion = () => (typeof msPorPaso === 'number' ? msPorPaso : msPorPaso.value)
  const terminada = computed(() => indice.value >= total.value)

  function detener() {
    reproduciendo.value = false
    window.clearTimeout(temporizador)
  }
  function avanzar() {
    if (indice.value >= total.value) return detener()
    indice.value++
    temporizador = window.setTimeout(avanzar, duracion())
  }
  function reproducir() {
    if (!total.value) return
    if (terminada.value) indice.value = 0
    reproduciendo.value = true
    window.clearTimeout(temporizador)
    temporizador = window.setTimeout(avanzar, Math.min(300, duracion()))
  }
  const alternar = () => (reproduciendo.value ? detener() : reproducir())
  function irA(n: number) {
    detener()
    indice.value = Math.max(0, Math.min(total.value, n))
  }
  const paso = (n: number) => irA(indice.value + n)
  const reiniciar = () => irA(0)
  const alFinal = () => irA(total.value)

  watch(total, () => {
    detener()
    indice.value = 0
  })
  onBeforeUnmount(detener)

  return { indice, reproduciendo, terminada, reproducir, detener, alternar, irA, paso, reiniciar, alFinal }
}

export type Pasos = ReturnType<typeof usePasos>
