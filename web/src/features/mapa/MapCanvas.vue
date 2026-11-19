<script setup lang="ts">
/**
 * Mapa en Canvas. Un píxel del lienzo de trabajo = una celda del mapa:
 * el terreno y la exploración viven en lienzos fuera de pantalla de ancho × alto
 * y se escalan sin suavizar, así reproducir miles de eventos cuesta un fillRect cada uno.
 * Solo dibuja: no calcula rutas.
 */
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import Icon from '../../shared/Icon.vue'
import type { EventoBusqueda, MapaDetalle, Posicion } from '../../core/types'

export interface Vista {
  k: number
  x: number
  y: number
}
/** Capas de dibujo para vistas que no son una búsqueda (patrullaje, pasillo). */
export interface Trazo {
  puntos: Posicion[]
  color: string
  /** Grosor en píxeles de pantalla. */
  ancho?: number
  alfa?: number
  punteado?: boolean
}
export interface GrupoCeldas {
  posiciones: Posicion[]
  color: string
  /** Dibuja una cruz blanca encima (celdas cerradas). */
  cruz?: boolean
}
export interface Marcador {
  pos: Posicion
  color: string
  etiqueta?: string
  /** Aro de resalte alrededor del marcador. */
  resaltado?: boolean
}
export type Zona = [number, number, number, number]

export interface InfoCelda {
  fila: number
  col: number
  terreno: string
  estado: 0 | 1 | 2
  g: number
  h: number
}

const props = withDefaults(
  defineProps<{
    mapa: MapaDetalle
    traza?: EventoBusqueda[]
    indice?: number
    ruta?: Posicion[]
    mostrarRuta?: boolean
    inicio?: Posicion | null
    destino?: Posicion | null
    bloqueadas?: Posicion[]
    interactivo?: boolean
    vista?: Vista | null
    compacto?: boolean
    trazos?: Trazo[]
    grupos?: GrupoCeldas[]
    marcadores?: Marcador[]
    /** Rectángulo [fila0, col0, fila1, col1] que se resalta; lo de afuera se atenúa. */
    zona?: Zona | null
  }>(),
  {
    traza: () => [], indice: 0, ruta: () => [], mostrarRuta: false, bloqueadas: () => [],
    trazos: () => [], grupos: () => [], marcadores: () => [], zona: null,
  },
)
const emit = defineEmits<{
  celda: [fila: number, col: number]
  hover: [info: InfoCelda | null, x: number, y: number]
  'update:vista': [vista: Vista]
}>()

const COLOR_TERRENO: Record<string, string> = {
  '.': '#ffffff', G: '#ffffff', '@': '#bdb4a3', O: '#bdb4a3', T: '#bccbaa', S: '#cfcb9f', W: '#b5cfe0',
}
const COLOR_EXPANDIDO = '#9cc3de'
const COLOR_FRONTERA = '#f6c46b'
const COLOR_RUTA = '#c0392b'
const COLOR_INICIO = '#2e8b57'

const contenedor = ref<HTMLDivElement | null>(null)
const lienzo = ref<HTMLCanvasElement | null>(null)
const ancho = ref(0)
const alto = ref(0)
const local = shallowRef<Vista | null>(null)
const progresoRuta = ref(0)

let terreno: HTMLCanvasElement | null = null
let exploracion: HTMLCanvasElement | null = null
let ctxExploracion: CanvasRenderingContext2D | null = null
let estado = new Uint8Array(0)
let gCelda = new Float32Array(0)
let hCelda = new Float32Array(0)
let aplicado = 0
let pendiente = 0
let animacionRuta = 0

const dpr = () => Math.min(window.devicePixelRatio || 1, 2)

function ajustada(): Vista {
  const k = Math.min(ancho.value / props.mapa.ancho, alto.value / props.mapa.alto) * 0.97
  return { k, x: (ancho.value - props.mapa.ancho * k) / 2, y: (alto.value - props.mapa.alto * k) / 2 }
}
const kMinimo = computed(() => ajustada().k * 0.7)

/** Mientras el usuario no haya movido la vista, el mapa se reajusta solo al cambiar el tamaño del marco. */
let manual = false

function fijarVista(v: Vista, usuario = false) {
  if (usuario) manual = true
  local.value = v
  emit('update:vista', v)
  pedirDibujo()
}
function ajustar() {
  manual = false
  fijarVista(ajustada())
}
/** Encuadra un rectángulo de celdas (por ejemplo, la zona de un pasillo). */
function enfocar(f0: number, c0: number, f1: number, c1: number, margen = 6) {
  if (!ancho.value || !alto.value) return
  const w = Math.abs(c1 - c0) + 1 + margen * 2
  const h = Math.abs(f1 - f0) + 1 + margen * 2
  const k = Math.min(48, ancho.value / w, alto.value / h)
  const cx = (Math.min(c0, c1) + Math.max(c0, c1) + 1) / 2
  const cy = (Math.min(f0, f1) + Math.max(f0, f1) + 1) / 2
  fijarVista({ k, x: ancho.value / 2 - cx * k, y: alto.value / 2 - cy * k }, true)
}
defineExpose({ ajustar, enfocar })

/* ── Capas fuera de pantalla ─────────────────────────────────────────────── */

function construirTerreno() {
  const { ancho: w, alto: h, filas } = props.mapa
  terreno = document.createElement('canvas')
  terreno.width = w
  terreno.height = h
  const ctx = terreno.getContext('2d')!
  const imagen = ctx.createImageData(w, h)
  const rgb: Record<string, [number, number, number]> = {}
  for (const [simbolo, hex] of Object.entries(COLOR_TERRENO)) {
    rgb[simbolo] = [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)]
  }
  for (let f = 0; f < h; f++) {
    for (let c = 0; c < w; c++) {
      const [r, g, b] = rgb[filas[f][c]] ?? rgb['@']
      const o = (f * w + c) * 4
      imagen.data[o] = r
      imagen.data[o + 1] = g
      imagen.data[o + 2] = b
      imagen.data[o + 3] = 255
    }
  }
  ctx.putImageData(imagen, 0, 0)
  exploracion = document.createElement('canvas')
  exploracion.width = w
  exploracion.height = h
  ctxExploracion = exploracion.getContext('2d')!
  estado = new Uint8Array(w * h)
  gCelda = new Float32Array(w * h)
  hCelda = new Float32Array(w * h)
  aplicado = 0
}

function reiniciarExploracion() {
  ctxExploracion?.clearRect(0, 0, props.mapa.ancho, props.mapa.alto)
  estado.fill(0)
  aplicado = 0
}

function aplicarEventos(hasta: number) {
  const ctx = ctxExploracion
  if (!ctx) return
  const w = props.mapa.ancho
  const tope = Math.min(hasta, props.traza.length)
  if (tope < aplicado) reiniciarExploracion()
  for (let i = aplicado; i < tope; i++) {
    const e = props.traza[i]
    const idx = e.posicion[0] * w + e.posicion[1]
    gCelda[idx] = e.g ?? Number.POSITIVE_INFINITY
    hCelda[idx] = e.h
    if (e.tipo === 'expandido') {
      estado[idx] = 2
      ctx.fillStyle = COLOR_EXPANDIDO
    } else if (estado[idx] < 2) {
      estado[idx] = 1
      ctx.fillStyle = COLOR_FRONTERA
    } else {
      continue
    }
    ctx.fillRect(e.posicion[1], e.posicion[0], 1, 1)
  }
  aplicado = tope
}

/* ── Dibujo ──────────────────────────────────────────────────────────────── */

function pedirDibujo() {
  if (pendiente) return
  pendiente = requestAnimationFrame(() => {
    pendiente = 0
    dibujar()
  })
}

function marca(ctx: CanvasRenderingContext2D, pos: Posicion, color: string, radio: number, k: number, hueco = false) {
  ctx.beginPath()
  ctx.arc(pos[1] + 0.5, pos[0] + 0.5, radio, 0, Math.PI * 2)
  ctx.fillStyle = hueco ? '#fffaf0' : color
  ctx.fill()
  ctx.lineWidth = Math.max(0.25, 2 / k)
  ctx.strokeStyle = hueco ? color : '#fffaf0'
  ctx.stroke()
}

function dibujar() {
  const cv = lienzo.value
  const v = local.value
  if (!cv || !v || !terreno || !exploracion) return
  const ctx = cv.getContext('2d')!
  const d = dpr()
  ctx.setTransform(d, 0, 0, d, 0, 0)
  ctx.clearRect(0, 0, ancho.value, alto.value)
  ctx.translate(v.x, v.y)
  ctx.scale(v.k, v.k)
  ctx.imageSmoothingEnabled = v.k < 1

  ctx.drawImage(terreno, 0, 0)
  ctx.drawImage(exploracion, 0, 0)

  if (v.k >= 9) {
    ctx.lineWidth = 1 / v.k
    ctx.strokeStyle = 'rgba(27, 25, 21, 0.07)'
    ctx.beginPath()
    const c0 = Math.max(0, Math.floor(-v.x / v.k))
    const c1 = Math.min(props.mapa.ancho, Math.ceil((ancho.value - v.x) / v.k))
    const f0 = Math.max(0, Math.floor(-v.y / v.k))
    const f1 = Math.min(props.mapa.alto, Math.ceil((alto.value - v.y) / v.k))
    for (let c = c0; c <= c1; c++) { ctx.moveTo(c, f0); ctx.lineTo(c, f1) }
    for (let f = f0; f <= f1; f++) { ctx.moveTo(c0, f); ctx.lineTo(c1, f) }
    ctx.stroke()
  }

  // zona resaltada: se atenúa lo que queda afuera
  if (props.zona) {
    const [za, zb, zc, zd] = props.zona
    const f0 = Math.min(za, zc), f1 = Math.max(za, zc) + 1
    const c0 = Math.min(zb, zd), c1 = Math.max(zb, zd) + 1
    const W = props.mapa.ancho, H = props.mapa.alto
    ctx.fillStyle = 'rgba(246, 246, 243, 0.72)'
    ctx.fillRect(0, 0, W, f0)
    ctx.fillRect(0, f1, W, H - f1)
    ctx.fillRect(0, f0, c0, f1 - f0)
    ctx.fillRect(c1, f0, W - c1, f1 - f0)
    ctx.lineWidth = Math.max(0.2, 2 / v.k)
    ctx.strokeStyle = '#6a3fd8'
    ctx.setLineDash([6 / v.k, 4 / v.k])
    ctx.strokeRect(c0, f0, c1 - c0, f1 - f0)
    ctx.setLineDash([])
  }

  // grupos de celdas (entradas, salidas, corte…)
  for (const grupo of props.grupos) {
    ctx.fillStyle = grupo.color
    for (const [f, c] of grupo.posiciones) ctx.fillRect(c, f, 1, 1)
    if (grupo.cruz && v.k >= 5) {
      ctx.strokeStyle = 'rgba(255,255,255,.9)'
      ctx.lineWidth = 1.4 / v.k
      ctx.beginPath()
      for (const [f, c] of grupo.posiciones) {
        ctx.moveTo(c + 0.25, f + 0.25); ctx.lineTo(c + 0.75, f + 0.75)
        ctx.moveTo(c + 0.75, f + 0.25); ctx.lineTo(c + 0.25, f + 0.75)
      }
      ctx.stroke()
    }
  }

  // celdas bloqueadas por el usuario
  if (props.bloqueadas.length) {
    ctx.fillStyle = 'rgba(58, 36, 120, 0.9)'
    for (const [f, c] of props.bloqueadas) ctx.fillRect(c, f, 1, 1)
    if (v.k >= 6) {
      ctx.strokeStyle = 'rgba(255,255,255,.75)'
      ctx.lineWidth = 1.4 / v.k
      ctx.beginPath()
      for (const [f, c] of props.bloqueadas) {
        ctx.moveTo(c + 0.25, f + 0.25); ctx.lineTo(c + 0.75, f + 0.75)
        ctx.moveTo(c + 0.75, f + 0.25); ctx.lineTo(c + 0.25, f + 0.75)
      }
      ctx.stroke()
    }
  }

  // trazos (tramos de patrullaje, caminos de flujo…)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  for (const t of props.trazos) {
    if (t.puntos.length < 2) continue
    ctx.beginPath()
    ctx.moveTo(t.puntos[0][1] + 0.5, t.puntos[0][0] + 0.5)
    for (let i = 1; i < t.puntos.length; i++) ctx.lineTo(t.puntos[i][1] + 0.5, t.puntos[i][0] + 0.5)
    ctx.globalAlpha = t.alfa ?? 1
    ctx.lineWidth = Math.max(0.35, (t.ancho ?? 2.4) / v.k)
    ctx.strokeStyle = t.color
    ctx.setLineDash(t.punteado ? [5 / v.k, 4 / v.k] : [])
    ctx.stroke()
  }
  ctx.setLineDash([])
  ctx.globalAlpha = 1

  // ruta final, dibujada progresivamente
  if (props.ruta.length > 1 && progresoRuta.value > 0) {
    const pasos = Math.max(1, Math.floor((props.ruta.length - 1) * progresoRuta.value))
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    for (const [ancho_, alfa, color] of [[Math.max(1.3, 7 / v.k), 0.22, COLOR_RUTA], [Math.max(0.5, 2.8 / v.k), 1, COLOR_RUTA]] as const) {
      ctx.beginPath()
      ctx.moveTo(props.ruta[0][1] + 0.5, props.ruta[0][0] + 0.5)
      for (let i = 1; i <= pasos; i++) ctx.lineTo(props.ruta[i][1] + 0.5, props.ruta[i][0] + 0.5)
      ctx.globalAlpha = alfa
      ctx.lineWidth = ancho_
      ctx.strokeStyle = color
      ctx.stroke()
    }
    ctx.globalAlpha = 1
  }

  // nodo que se está expandiendo
  const actual = props.indice > 0 ? props.traza[Math.min(props.indice, props.traza.length) - 1] : undefined
  if (actual && !props.mostrarRuta) {
    ctx.beginPath()
    ctx.arc(actual.posicion[1] + 0.5, actual.posicion[0] + 0.5, Math.max(1.4, 7 / v.k), 0, Math.PI * 2)
    ctx.lineWidth = Math.max(0.3, 2.2 / v.k)
    ctx.strokeStyle = '#6a3fd8'
    ctx.stroke()
  }

  const r = Math.max(1.1, 6.5 / v.k)
  if (props.inicio) marca(ctx, props.inicio, COLOR_INICIO, r, v.k)
  if (props.destino) marca(ctx, props.destino, '#1d1a16', r, v.k, true)

  // marcadores numerados
  const rm = Math.max(1.6, 10 / v.k)
  for (const m of props.marcadores) {
    if (m.resaltado) {
      ctx.beginPath()
      ctx.arc(m.pos[1] + 0.5, m.pos[0] + 0.5, rm * 1.55, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(106, 63, 216, 0.18)'
      ctx.fill()
    }
    marca(ctx, m.pos, m.color, rm, v.k)
    if (m.etiqueta) {
      ctx.fillStyle = '#fff'
      ctx.font = `600 ${rm * 1.15}px Poppins, system-ui, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(m.etiqueta, m.pos[1] + 0.5, m.pos[0] + 0.55)
    }
  }
}

function animarRuta(hacia: number) {
  cancelAnimationFrame(animacionRuta)
  if (hacia === 0) {
    progresoRuta.value = 0
    pedirDibujo()
    return
  }
  const duracion = Math.min(1600, 420 + props.ruta.length * 7)
  const t0 = performance.now()
  const paso = (ahora: number) => {
    const t = Math.min(1, (ahora - t0) / duracion)
    progresoRuta.value = 1 - Math.pow(1 - t, 3)
    dibujar()
    if (t < 1) animacionRuta = requestAnimationFrame(paso)
  }
  animacionRuta = requestAnimationFrame(paso)
}

/* ── Interacción ─────────────────────────────────────────────────────────── */

function celdaEn(px: number, py: number): [number, number] | null {
  const v = local.value
  if (!v) return null
  const c = Math.floor((px - v.x) / v.k)
  const f = Math.floor((py - v.y) / v.k)
  return c >= 0 && f >= 0 && c < props.mapa.ancho && f < props.mapa.alto ? [f, c] : null
}

function alRueda(e: WheelEvent) {
  e.preventDefault()
  const v = local.value
  if (!v) return
  const caja = lienzo.value!.getBoundingClientRect()
  const px = e.clientX - caja.left
  const py = e.clientY - caja.top
  const k = Math.min(48, Math.max(kMinimo.value, v.k * Math.exp(-e.deltaY * 0.0016)))
  const s = k / v.k
  fijarVista({ k, x: px - (px - v.x) * s, y: py - (py - v.y) * s }, true)
}

let arrastre: { x: number; y: number; vx: number; vy: number; movido: boolean } | null = null

function alBajar(e: PointerEvent) {
  const v = local.value
  if (!v) return
  lienzo.value!.setPointerCapture(e.pointerId)
  arrastre = { x: e.clientX, y: e.clientY, vx: v.x, vy: v.y, movido: false }
}
function alMover(e: PointerEvent) {
  const caja = lienzo.value!.getBoundingClientRect()
  const px = e.clientX - caja.left
  const py = e.clientY - caja.top
  if (arrastre) {
    const dx = e.clientX - arrastre.x
    const dy = e.clientY - arrastre.y
    if (Math.abs(dx) + Math.abs(dy) > 4) arrastre.movido = true
    if (arrastre.movido && local.value) fijarVista({ ...local.value, x: arrastre.vx + dx, y: arrastre.vy + dy }, true)
    return
  }
  const celda = celdaEn(px, py)
  if (!celda) return emit('hover', null, px, py)
  const idx = celda[0] * props.mapa.ancho + celda[1]
  emit('hover', {
    fila: celda[0], col: celda[1], terreno: props.mapa.filas[celda[0]][celda[1]],
    estado: estado[idx] as 0 | 1 | 2, g: gCelda[idx], h: hCelda[idx],
  }, px, py)
}
function alSoltar(e: PointerEvent) {
  if (arrastre && !arrastre.movido && props.interactivo) {
    const caja = lienzo.value!.getBoundingClientRect()
    const celda = celdaEn(e.clientX - caja.left, e.clientY - caja.top)
    if (celda) emit('celda', celda[0], celda[1])
  }
  arrastre = null
}

/* ── Ciclo de vida ───────────────────────────────────────────────────────── */

let observador: ResizeObserver | null = null

function dimensionar() {
  const el = contenedor.value
  const cv = lienzo.value
  if (!el || !cv) return
  const primera = ancho.value === 0
  const d = dpr()
  ancho.value = el.clientWidth
  alto.value = el.clientHeight
  cv.width = Math.round(ancho.value * d)
  cv.height = Math.round(alto.value * d)
  if (primera || !local.value) fijarVista(props.vista ?? ajustada())
  else if (!manual) fijarVista(ajustada())
  else pedirDibujo()
}

onMounted(() => {
  construirTerreno()
  observador = new ResizeObserver(dimensionar)
  observador.observe(contenedor.value!)
  dimensionar()
  aplicarEventos(props.indice)
  if (props.mostrarRuta) animarRuta(1)
})
onBeforeUnmount(() => {
  observador?.disconnect()
  cancelAnimationFrame(pendiente)
  cancelAnimationFrame(animacionRuta)
})

watch(() => props.mapa, () => {
  construirTerreno()
  local.value = null
  manual = false
  dimensionar()
})
watch(() => props.traza, () => {
  reiniciarExploracion()
  aplicarEventos(props.indice)
  pedirDibujo()
})
watch(() => props.indice, (n) => {
  aplicarEventos(n)
  pedirDibujo()
})
watch(() => props.vista, (v) => {
  if (v && v !== local.value) {
    local.value = v
    pedirDibujo()
  }
})
watch(() => props.mostrarRuta, (m) => animarRuta(m ? 1 : 0))
watch(() => props.ruta, () => {
  if (props.mostrarRuta) animarRuta(1)
  else pedirDibujo()
})
watch(() => [props.inicio, props.destino, props.bloqueadas], pedirDibujo, { deep: true })
watch(() => [props.trazos, props.grupos, props.marcadores, props.zona], pedirDibujo)

function zoom(factor: number) {
  const v = local.value
  if (!v) return
  const cx = ancho.value / 2
  const cy = alto.value / 2
  const k = Math.min(48, Math.max(kMinimo.value, v.k * factor))
  const s = k / v.k
  fijarVista({ k, x: cx - (cx - v.x) * s, y: cy - (cy - v.y) * s }, true)
}
</script>

<template>
  <div ref="contenedor" class="mapa" :class="{ interactivo, compacto }">
    <canvas
      ref="lienzo"
      @wheel="alRueda"
      @pointerdown="alBajar"
      @pointermove="alMover"
      @pointerup="alSoltar"
      @pointerleave="emit('hover', null, 0, 0)"
    />
    <div class="zoom glass" role="group" aria-label="Zoom">
      <button type="button" aria-label="Acercar" @click="zoom(1.5)"><Icon name="zoom_mas" :size="15" /></button>
      <button type="button" aria-label="Alejar" @click="zoom(1 / 1.5)"><Icon name="zoom_menos" :size="15" /></button>
      <button type="button" aria-label="Ajustar al marco" @click="ajustar"><Icon name="ajustar" :size="15" /></button>
    </div>
  </div>
</template>

<style scoped>
.mapa {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  touch-action: none;
}
canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
}
.interactivo canvas { cursor: crosshair; }
canvas:active { cursor: grabbing; }
.zoom {
  position: absolute;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  padding: 4px;
  border-radius: 14px;
}
.compacto .zoom { display: none; }
.zoom button {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  color: var(--ink-2);
  transition: background 0.2s, transform 0.3s var(--spring);
}
.zoom button:hover { background: rgba(27, 25, 21, 0.06); }
.zoom button:active { transform: scale(0.88); }
</style>
