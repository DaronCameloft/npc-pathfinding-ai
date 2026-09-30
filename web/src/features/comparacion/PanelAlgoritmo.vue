<script setup lang="ts">
import { computed, toRef } from 'vue'
import type { AlgoritmoInfo, Ejecucion, MapaDetalle, Posicion } from '../../core/types'
import AnimatedNumber from '../../shared/AnimatedNumber.vue'
import MapCanvas, { type Vista } from '../mapa/MapCanvas.vue'
import { useConteos } from '../pseudocodigo/useConteoLineas'

export type Veredicto = 'mejor' | 'peor' | null
export interface Resaltado {
  expandidos: Veredicto
  costo: Veredicto
}

const props = defineProps<{
  info: AlgoritmoInfo
  ejecucion: Ejecucion
  mapa: MapaDetalle
  indice: number
  inicio: Posicion
  destino: Posicion
  vista: Vista | null
  costoMinimo: number | null
  zoom: boolean
  /** Mejor/peor de expandidos y costo frente a los demás; null desactiva el resaltado. */
  resaltado?: Resaltado | null
}>()
const emit = defineEmits<{ 'update:vista': [vista: Vista] }>()

const traza = computed(() => props.ejecucion.traza)
const idx = computed(() => Math.min(props.indice, props.ejecucion.traza.length))
const conteos = useConteos(traza, toRef(() => idx.value))
const terminado = computed(() => idx.value >= props.ejecucion.traza.length)
const encontrada = computed(() => props.ejecucion.estado === 'encontrada')

/** Solo se colorea cuando este algoritmo terminó: el resultado se «revela» al final. */
const clase = (metrica: 'expandidos' | 'costo') => (terminado.value && props.resaltado ? props.resaltado[metrica] : null)

const veredicto = computed(() => {
  if (!terminado.value) return { texto: 'Explorando…', clase: 'pill-sky' }
  if (!encontrada.value) return { texto: 'Sin ruta', clase: 'pill-danger' }
  const costo = props.ejecucion.costo ?? 0
  const minimo = props.costoMinimo ?? costo
  if (costo - minimo < 1e-5) return { texto: 'Ruta óptima', clase: 'pill-lime' }
  return { texto: `+${(((costo - minimo) / minimo) * 100).toFixed(1)} % de costo`, clase: 'pill-gold' }
})
</script>

<template>
  <article class="card panel">
    <header>
      <h3 class="display">{{ info.nombre }}</h3>
      <span class="pill" :class="veredicto.clase">{{ veredicto.texto }}</span>
    </header>
    <div class="lienzo">
      <MapCanvas
        :mapa="mapa"
        :traza="traza"
        :indice="idx"
        :ruta="ejecucion.ruta"
        :mostrar-ruta="terminado && encontrada"
        :inicio="inicio"
        :destino="destino"
        :vista="vista"
        :compacto="!zoom"
        @update:vista="emit('update:vista', $event)"
      />
    </div>
    <dl>
      <div :class="clase('expandidos')">
        <dt>Expandidos</dt>
        <dd class="num">{{ conteos.expandidos.toLocaleString('es-PE') }}</dd>
      </div>
      <div :class="clase('costo')">
        <dt>Costo</dt>
        <dd class="num">
          <template v-if="terminado && ejecucion.costo !== null"><AnimatedNumber :value="ejecucion.costo" :decimals="2" :duration="600" /></template>
          <template v-else>—</template>
        </dd>
      </div>
      <div class="complejidad" :class="{ fija: !!resaltado }">
        <dt>Complejidad</dt>
        <dd class="mono">{{ info.complejidad }}</dd>
      </div>
    </dl>
  </article>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 10px; min-height: 0; padding: 14px 16px 14px; }
header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
h3 { font-size: 21px; }
.lienzo {
  flex: 1;
  min-height: 96px;
  overflow: hidden;
  border-radius: 14px;
  background: var(--field);
}
dl { display: grid; grid-template-columns: 1.25fr 1.25fr 0.9fr; gap: 8px; margin: 0; }
dl div { min-width: 0; padding: 7px 10px; border-radius: 12px; background: var(--field); transition: background 0.6s var(--ease-out), color 0.6s; }
dl div.mejor { background: #e3f6a8; }
dl div.mejor dt { color: #4a5b12; }
dl div.peor { background: #f9d9d4; color: #8c281c; }
dl div.peor dt { color: #a8483c; }
dt { color: var(--ink-3); font-size: 10.5px; }
dd { margin: 1px 0 0; font-size: 16px; font-weight: 600; white-space: nowrap; }
dd.mono { font-size: 12px; font-weight: 500; padding-top: 3px; }
/* La complejidad es teórica, no un resultado de esta consulta: color fijo y discreto. */
dl div.fija { background: var(--violet-soft); }
dl div.fija dt { color: #6f55b3; }
dl div.fija dd { color: #4a3592; }
</style>
