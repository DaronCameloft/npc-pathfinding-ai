<script setup lang="ts">
import { computed, toRef } from 'vue'
import type { AlgoritmoInfo, Ejecucion, MapaDetalle, Posicion } from '../../core/types'
import AnimatedNumber from '../../shared/AnimatedNumber.vue'
import MapCanvas, { type Vista } from '../mapa/MapCanvas.vue'
import { useConteos } from '../pseudocodigo/useConteoLineas'

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
}>()
const emit = defineEmits<{ 'update:vista': [vista: Vista] }>()

const traza = computed(() => props.ejecucion.traza)
const idx = computed(() => Math.min(props.indice, props.ejecucion.traza.length))
const conteos = useConteos(traza, toRef(() => idx.value))
const terminado = computed(() => idx.value >= props.ejecucion.traza.length)
const encontrada = computed(() => props.ejecucion.estado === 'encontrada')

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
      <div>
        <dt>Expandidos</dt>
        <dd class="num">{{ conteos.expandidos.toLocaleString('es-PE') }}</dd>
      </div>
      <div>
        <dt>Costo</dt>
        <dd class="num">
          <template v-if="terminado && ejecucion.costo !== null"><AnimatedNumber :value="ejecucion.costo" :decimals="2" :duration="600" /></template>
          <template v-else>—</template>
        </dd>
      </div>
      <div>
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
  min-height: 150px;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(180deg, #efe4d0, #e6d8be);
  box-shadow: inset 0 0 0 1px rgba(60, 40, 20, 0.08);
}
dl { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 0; }
dl div { min-width: 0; padding: 7px 10px; border-radius: 12px; background: rgba(60, 40, 20, 0.045); }
dt { color: var(--ink-3); font-size: 10.5px; }
dd { margin: 1px 0 0; font-size: 14px; font-weight: 500; white-space: nowrap; }
dd.mono { font-size: 12px; padding-top: 2px; }
</style>
