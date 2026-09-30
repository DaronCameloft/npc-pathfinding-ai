<script setup lang="ts">
/**
 * Nube de puntos de la verificación: cada punto es un escenario del benchmark.
 * Eje X = costo óptimo de la consulta; eje Y = nodos que expandió el algoritmo.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Evidencia } from '../../core/types'

const props = defineProps<{ puntos: Evidencia['puntos'] }>()

const COLORES = ['#4f8fc9', '#e3a52d', '#6a3fd8', '#2e8b57']
const M = { izq: 62, der: 18, arr: 14, aba: 46 }

const contenedor = ref<HTMLDivElement | null>(null)
const lienzo = ref<HTMLCanvasElement | null>(null)
const ocultos = ref(new Set<number>())
const cerca = ref<{ i: number; x: number; y: number } | null>(null)
let ancho = 0
let alto = 0
let observador: ResizeObserver | null = null

const dpr = () => Math.min(window.devicePixelRatio || 1, 2)
const fmt = (n: number) => n.toLocaleString('es-PE')

/** Cota superior «redonda» y paso de las marcas para un eje que arranca en 0. */
function escala(maximo: number): { tope: number; paso: number } {
  const bruto = maximo / 5
  const potencia = Math.pow(10, Math.floor(Math.log10(bruto)))
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * potencia).find((p) => p >= bruto) ?? bruto
  return { tope: Math.ceil(maximo / paso) * paso, paso }
}

const ejes = computed(() => ({
  x: escala(Math.max(...props.puntos.costo, 1)),
  y: escala(Math.max(...props.puntos.expandidos, 1)),
}))

const px = (valor: number) => M.izq + (valor / ejes.value.x.tope) * (ancho - M.izq - M.der)
const py = (valor: number) => alto - M.aba - (valor / ejes.value.y.tope) * (alto - M.arr - M.aba)

function dibujar() {
  const cv = lienzo.value
  if (!cv || !ancho) return
  const ctx = cv.getContext('2d')!
  const d = dpr()
  ctx.setTransform(d, 0, 0, d, 0, 0)
  ctx.clearRect(0, 0, ancho, alto)
  ctx.font = '11px Poppins, system-ui, sans-serif'
  ctx.textBaseline = 'middle'

  ctx.strokeStyle = 'rgba(27,25,21,0.07)'
  ctx.fillStyle = '#78736a'
  ctx.lineWidth = 1
  const { x, y } = ejes.value
  ctx.textAlign = 'right'
  for (let v = 0; v <= y.tope + 1e-9; v += y.paso) {
    const yy = Math.round(py(v)) + 0.5
    ctx.beginPath()
    ctx.moveTo(M.izq, yy)
    ctx.lineTo(ancho - M.der, yy)
    ctx.stroke()
    ctx.fillText(fmt(v), M.izq - 8, yy)
  }
  ctx.textAlign = 'center'
  for (let v = 0; v <= x.tope + 1e-9; v += x.paso) {
    const xx = Math.round(px(v)) + 0.5
    ctx.beginPath()
    ctx.moveTo(xx, M.arr)
    ctx.lineTo(xx, alto - M.aba)
    ctx.stroke()
    ctx.fillText(fmt(v), xx, alto - M.aba + 14)
  }
  ctx.fillStyle = '#47433b'
  ctx.fillText('Costo óptimo de la consulta', M.izq + (ancho - M.izq - M.der) / 2, alto - 10)
  ctx.save()
  ctx.translate(14, M.arr + (alto - M.arr - M.aba) / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillText('Nodos expandidos', 0, 0)
  ctx.restore()

  const { mapa, costo, expandidos } = props.puntos
  ctx.globalAlpha = 0.5
  for (let m = 0; m < props.puntos.mapas.length; m++) {
    if (ocultos.value.has(m)) continue
    ctx.fillStyle = COLORES[m % COLORES.length]
    ctx.beginPath()
    for (let i = 0; i < costo.length; i++) {
      if (mapa[i] !== m) continue
      const cx = px(costo[i])
      const cy = py(expandidos[i])
      ctx.moveTo(cx + 2.6, cy)
      ctx.arc(cx, cy, 2.6, 0, Math.PI * 2)
    }
    ctx.fill()
  }
  ctx.globalAlpha = 1

  if (cerca.value) {
    const i = cerca.value.i
    ctx.beginPath()
    ctx.arc(px(costo[i]), py(expandidos[i]), 6, 0, Math.PI * 2)
    ctx.lineWidth = 2
    ctx.strokeStyle = '#1b1915'
    ctx.stroke()
  }
}

function alMover(e: PointerEvent) {
  const caja = lienzo.value!.getBoundingClientRect()
  const x = e.clientX - caja.left
  const y = e.clientY - caja.top
  const { mapa, costo, expandidos } = props.puntos
  let mejor = -1
  let distancia = 14 * 14
  for (let i = 0; i < costo.length; i++) {
    if (ocultos.value.has(mapa[i])) continue
    const dx = px(costo[i]) - x
    const dy = py(expandidos[i]) - y
    const d2 = dx * dx + dy * dy
    if (d2 < distancia) {
      distancia = d2
      mejor = i
    }
  }
  cerca.value = mejor >= 0 ? { i: mejor, x, y } : null
  dibujar()
}

function alternar(m: number) {
  const siguiente = new Set(ocultos.value)
  if (!siguiente.delete(m)) siguiente.add(m)
  ocultos.value = siguiente
  cerca.value = null
}

function dimensionar() {
  const el = contenedor.value
  const cv = lienzo.value
  if (!el || !cv) return
  ancho = el.clientWidth
  alto = el.clientHeight
  cv.width = Math.round(ancho * dpr())
  cv.height = Math.round(alto * dpr())
  dibujar()
}

onMounted(() => {
  observador = new ResizeObserver(dimensionar)
  observador.observe(contenedor.value!)
  dimensionar()
})
onBeforeUnmount(() => observador?.disconnect())
watch([() => props.puntos, ocultos], dibujar)

const info = computed(() => {
  if (!cerca.value) return null
  const i = cerca.value.i
  const p = props.puntos
  return {
    mapa: p.mapas[p.mapa[i]],
    costo: p.costo[i].toFixed(2),
    expandidos: fmt(p.expandidos[i]),
    tiempo: p.tiempo_ms[i].toFixed(1),
  }
})
</script>

<template>
  <div class="dispersion">
    <ul class="leyenda" aria-label="Mapas">
      <li v-for="(nombre, m) in puntos.mapas" :key="nombre">
        <button type="button" :class="{ apagado: ocultos.has(m) }" :aria-pressed="!ocultos.has(m)" @click="alternar(m)">
          <i :style="{ background: COLORES[m % COLORES.length] }" />{{ nombre }}
        </button>
      </li>
    </ul>
    <div ref="contenedor" class="marco">
      <canvas
        ref="lienzo"
        role="img"
        aria-label="Nodos expandidos según el costo óptimo de cada uno de los 4 200 escenarios"
        @pointermove="alMover"
        @pointerleave="((cerca = null), dibujar())"
      />
      <div v-if="info && cerca" class="tip glass" :style="{ transform: `translate(${Math.min(cerca.x + 14, 9999)}px, ${cerca.y + 14}px)` }">
        <strong>{{ info.mapa }}</strong>
        <span class="num">costo {{ info.costo }} · {{ info.expandidos }} nodos · {{ info.tiempo }} ms</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dispersion { display: flex; flex-direction: column; gap: 10px; height: 100%; min-height: 0; }
.leyenda { display: flex; gap: 8px; margin: 0; padding: 0; list-style: none; flex-wrap: wrap; }
.leyenda button {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 12px 4px 9px;
  border-radius: 999px;
  background: var(--field);
  font-size: 12px;
  font-weight: 500;
  transition: opacity 0.25s, transform 0.35s var(--spring);
}
.leyenda button:active { transform: scale(0.94); }
.leyenda button.apagado { opacity: 0.45; }
.leyenda i { width: 9px; height: 9px; border-radius: 50%; }
.marco { position: relative; flex: 1; min-height: 240px; }
canvas { display: block; width: 100%; height: 100%; }
.tip {
  position: absolute;
  top: 0;
  left: 0;
  display: grid;
  gap: 1px;
  padding: 7px 11px;
  border-radius: 12px;
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
}
.tip span { color: var(--ink-3); font-size: 11px; }
</style>
