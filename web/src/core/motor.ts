/**
 * Estado del motor (la API). En Render gratis el servicio se duerme tras ~15 min:
 * la primera petición puede tardar, y la interfaz debe decir «despertando el motor».
 */

import { reactive } from 'vue'
import { api } from './api'
import type { AlgoritmoInfo, MapaResumen } from './types'

export type EstadoMotor = 'conectando' | 'despertando' | 'listo' | 'sin_conexion'

export const motor = reactive({
  estado: 'conectando' as EstadoMotor,
  version: '',
  latenciaMs: 0,
  algoritmos: [] as AlgoritmoInfo[],
  mapas: [] as MapaResumen[],
})

let conectando: Promise<void> | null = null

/** Conecta con el motor y carga el catálogo. Reintenta mientras el servicio despierta. */
export function conectarMotor(): Promise<void> {
  conectando ??= (async () => {
    const inicio = performance.now()
    const aviso = setTimeout(() => {
      if (motor.estado === 'conectando') motor.estado = 'despertando'
    }, 1800)
    for (let intento = 0; intento < 12; intento++) {
      try {
        const salud = await api.health()
        motor.version = salud.version
        motor.latenciaMs = Math.round(performance.now() - inicio)
        ;[motor.algoritmos, motor.mapas] = await Promise.all([api.algoritmos(), api.mapas()])
        motor.estado = 'listo'
        clearTimeout(aviso)
        return
      } catch {
        motor.estado = 'despertando'
        await new Promise((resolver) => setTimeout(resolver, 2500))
      }
    }
    clearTimeout(aviso)
    motor.estado = 'sin_conexion'
    conectando = null
  })()
  return conectando
}

export function reintentarConexion(): Promise<void> {
  conectando = null
  motor.estado = 'conectando'
  return conectarMotor()
}
