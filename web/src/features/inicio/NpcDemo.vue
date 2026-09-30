<script setup lang="ts">
/**
 * La esencia del proyecto en una animación: un NPC sigue la ruta de A*, aparece un obstáculo y
 * replanifica desde donde está. Los datos (ruta y traza de cada búsqueda) los generó el motor
 * con `engine/tools/web/generar_demo.py`; aquí solo se reproducen.
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import demo from './demoNpc.json'

type Evento = [number, number, number]

const filas: string[] = demo.filas
const H = filas.length
const W = filas[0].length
const ruta1 = demo.primera.ruta as [number, number][]
const ruta2 = demo.segunda.ruta as [number, number][]
const traza1 = demo.primera.traza as Evento[]
const traza2 = demo.segunda.traza as Evento[]
const K = demo.indice_npc
const bloqueo = demo.bloqueo as [number, number]
const meta = demo.destino as [number, number]

const paso2d = (a: [number, number], b: [number, number]) => (a[0] !== b[0] && a[1] !== b[1] ? Math.SQRT2 : 1)
const COSTO_CAMINADO = ruta1.slice(1, K + 1).reduce((suma, p, i) => suma + paso2d(ruta1[i], p), 0)

/* ── Línea de tiempo (ms) ────────────────────────────────────────────────── */
const DUR = {
  intro: 500,
  explora1: 2600,
  traza1: 900,
  camina1: (K / 7) * 1000,
  cae: 900,
  explora2: 2300,
  traza2: 900,
  camina2: ((ruta2.length - 1) / 9) * 1000,
  fin: 2200,
}
const FASES = ['intro', 'explora1', 'traza1', 'camina1', 'cae', 'explora2', 'traza2', 'camina2', 'fin'] as const
type Fase = (typeof FASES)[number]
const INICIO_FASE = {} as Record<Fase, number>
let acumulado = 0
for (const f of FASES) {
  INICIO_FASE[f] = acumulado
  acumulado += DUR[f]
}
const CICLO = acumulado

const PASOS = [
  { etiqueta: 'Explora', fases: ['intro', 'explora1'] },
  { etiqueta: 'Traza la ruta', fases: ['traza1', 'camina1'] },
  { etiqueta: 'Aparece un obstáculo', fases: ['cae'] },
  { etiqueta: 'Recalcula', fases: ['explora2', 'traza2', 'camina2', 'fin'] },
]

const contenedor = ref<HTMLDivElement | null>(null)
const lienzo = ref<HTMLCanvasElement | null>(null)
const paso = ref(0)
const explorados = ref(0)
const costo = ref(demo.primera.costo)
let ancho = 0
let alto = 0
let cuadro = 0
let inicio = 0
let fondo: HTMLCanvasElement | null = null
let celda = 20
let ox = 0
let oy = 0

const reducirMovimiento = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
const dpr = () => Math.min(window.devicePixelRatio || 1, 2)

const suave = (x: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3)
const clamp01 = (x: number) => Math.min(1, Math.max(0, x))

function faseEn(t: number): { fase: Fase; p: number } {
  for (let i = FASES.length - 1; i >= 0; i--) {
    const f = FASES[i]
    if (t >= INICIO_FASE[f]) return { fase: f, p: clamp01((t - INICIO_FASE[f]) / DUR[f]) }
  }
  return { fase: 'intro', p: 0 }
}

function rect(ctx: CanvasRenderingContext2D, f: number, c: number, color: string, margen = 1.2, radio = 4, escala = 1) {
  const s = (celda - margen * 2) * escala
  const x = ox + c * celda + (celda - s) / 2
  const y = oy + f * celda + (celda - s) / 2
  ctx.beginPath()
  ctx.roundRect(x, y, s, s, radio * Math.min(1, celda / 22))
  ctx.fillStyle = color
  ctx.fill()
}

function construirFondo() {
  fondo = document.createElement('canvas')
  fondo.width = Math.round(ancho * dpr())
  fondo.height = Math.round(alto * dpr())
  const ctx = fondo.getContext('2d')!
  ctx.scale(dpr(), dpr())
  for (let f = 0; f < H; f++) {
    for (let c = 0; c < W; c++) rect(ctx, f, c, filas[f][c] === '@' ? '#cdc5b2' : '#f3f1ec')
  }
}

function dimensionar() {
  const el = contenedor.value
  const cv = lienzo.value
  if (!el || !cv) return
  ancho = el.clientWidth
  alto = el.clientHeight
  cv.width = Math.round(ancho * dpr())
  cv.height = Math.round(alto * dpr())
  celda = Math.min(ancho / W, alto / H)
  ox = (ancho - celda * W) / 2
  oy = (alto - celda * H) / 2
  construirFondo()
}

function centro(p: [number, number]): [number, number] {
  return [ox + (p[1] + 0.5) * celda, oy + (p[0] + 0.5) * celda]
}

/** Punto interpolado sobre una ruta según cuántas celdas se ha avanzado (puede ser fraccionario). */
function sobreRuta(ruta: [number, number][], avance: number): [number, number] {
  const i = Math.min(ruta.length - 1, Math.floor(avance))
  const j = Math.min(ruta.length - 1, i + 1)
  const a = centro(ruta[i])
  const b = centro(ruta[j])
  const u = avance - i
  return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]
}

function trazarRuta(ctx: CanvasRenderingContext2D, ruta: [number, number][], hasta: number, desde = 0, alfa = 1) {
  if (hasta <= desde || alfa <= 0) return
  const fin = Math.min(ruta.length - 1, hasta)
  ctx.save()
  ctx.globalAlpha = alfa
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#c0392b'
  ctx.lineWidth = Math.max(3, celda * 0.3)
  ctx.beginPath()
  const p0 = sobreRuta(ruta, desde)
  ctx.moveTo(p0[0], p0[1])
  for (let i = Math.ceil(desde + 0.0001); i < fin; i++) {
    const p = centro(ruta[i])
    ctx.lineTo(p[0], p[1])
  }
  const pf = sobreRuta(ruta, fin)
  ctx.lineTo(pf[0], pf[1])
  ctx.stroke()
  ctx.restore()
}

function dibujarExploracion(ctx: CanvasRenderingContext2D, traza: Evento[], n: number, alfa: number) {
  if (alfa <= 0) return
  const estado = new Map<number, number>()
  for (let i = 0; i < Math.min(n, traza.length); i++) {
    const [f, c, t] = traza[i]
    const clave = f * W + c
    if (t === 1 || !estado.has(clave)) estado.set(clave, t)
  }
  ctx.save()
  ctx.globalAlpha = alfa
  estado.forEach((t, clave) => rect(ctx, Math.floor(clave / W), clave % W, t === 1 ? '#a8cbe4' : '#f6c46b'))
  ctx.restore()
}

function dibujarNpc(ctx: CanvasRenderingContext2D, x: number, y: number, tiempo: number, camina: boolean, salto = 0) {
  const s = celda * 0.82
  const rebote = camina ? Math.abs(Math.sin(tiempo / 90)) * celda * 0.16 : 0
  const cy = y - rebote - salto
  ctx.save()
  ctx.fillStyle = 'rgba(27,25,21,0.12)'
  ctx.beginPath()
  ctx.ellipse(x, y + s * 0.45, s * 0.42, s * 0.14, 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.roundRect(x - s / 2, cy - s / 2, s, s, s * 0.28)
  ctx.fillStyle = '#1b1915'
  ctx.fill()
  ctx.fillStyle = '#fffdf6'
  const ojo = s * 0.11
  ctx.beginPath()
  ctx.arc(x - s * 0.17, cy - s * 0.05, ojo, 0, Math.PI * 2)
  ctx.arc(x + s * 0.17, cy - s * 0.05, ojo, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()
}

function dibujar(ahora: number) {
  const cv = lienzo.value
  if (!cv || !fondo) return
  const ctx = cv.getContext('2d')!
  const t = reducirMovimiento ? CICLO - 1 : (ahora - inicio) % CICLO
  const { fase, p } = faseEn(t)

  ctx.setTransform(dpr(), 0, 0, dpr(), 0, 0)
  ctx.clearRect(0, 0, ancho, alto)
  ctx.drawImage(fondo, 0, 0, ancho, alto)

  // exploración
  let vistos = 0
  if (fase === 'intro') vistos = 0
  else if (fase === 'explora1') {
    vistos = Math.floor(p * traza1.length)
    dibujarExploracion(ctx, traza1, vistos, 1)
  } else if (fase === 'traza1' || fase === 'camina1' || fase === 'cae') {
    vistos = traza1.length
    dibujarExploracion(ctx, traza1, vistos, 1)
  } else {
    // la primera exploración se desvanece cuando empieza el replanteo
    const desvanece = fase === 'explora2' ? 1 - suave(p * 3) : 0
    dibujarExploracion(ctx, traza1, traza1.length, desvanece)
    if (fase === 'explora2') vistos = Math.floor(p * traza2.length)
    else vistos = traza2.length
    dibujarExploracion(ctx, traza2, vistos, 1)
  }

  // inicio y destino
  const [ix, iy] = centro(ruta1[0])
  ctx.beginPath()
  ctx.arc(ix, iy, celda * 0.3, 0, Math.PI * 2)
  ctx.fillStyle = '#2e8b57'
  ctx.fill()
  const [mx, my] = centro(meta)
  const pulso = 1 + 0.12 * Math.sin(ahora / 260)
  ctx.beginPath()
  ctx.arc(mx, my, celda * 0.34 * pulso, 0, Math.PI * 2)
  ctx.fillStyle = '#fffdf6'
  ctx.fill()
  ctx.lineWidth = Math.max(2, celda * 0.11)
  ctx.strokeStyle = '#1b1915'
  ctx.stroke()

  // rutas
  let npc: [number, number] = centro(ruta1[0])
  let camina = false
  if (fase === 'traza1') trazarRuta(ctx, ruta1, suave(p) * (ruta1.length - 1))
  if (fase === 'camina1' || fase === 'cae') {
    trazarRuta(ctx, ruta1, ruta1.length - 1)
    const avance = fase === 'camina1' ? p * K : K
    npc = sobreRuta(ruta1, avance)
    camina = fase === 'camina1'
  }
  if (fase === 'explora2') {
    trazarRuta(ctx, ruta1, K, 0)
    trazarRuta(ctx, ruta1, ruta1.length - 1, K, 1 - suave(p * 4))
    npc = centro(ruta1[K])
  }
  if (fase === 'traza2' || fase === 'camina2' || fase === 'fin') {
    trazarRuta(ctx, ruta1, K, 0)
    trazarRuta(ctx, ruta2, fase === 'traza2' ? suave(p) * (ruta2.length - 1) : ruta2.length - 1)
    if (fase === 'traza2') npc = centro(ruta2[0])
    else if (fase === 'camina2') {
      npc = sobreRuta(ruta2, p * (ruta2.length - 1))
      camina = true
    } else npc = centro(ruta2[ruta2.length - 1])
  }

  // obstáculo que cae
  if (INICIO_FASE[fase] >= INICIO_FASE.cae) {
    const q = fase === 'cae' ? p : 1
    const caida = 1 - suave(q / 0.55)
    const rebote = q > 0.55 ? Math.sin(((q - 0.55) / 0.45) * Math.PI) * 0.12 : 0
    const [bx, by] = centro(bloqueo)
    ctx.save()
    ctx.globalAlpha = Math.min(1, q * 4)
    ctx.translate(0, -caida * celda * 4)
    ctx.beginPath()
    const s = celda * (0.94 + rebote)
    ctx.roundRect(bx - s / 2, by - s / 2, s, s, celda * 0.2)
    ctx.fillStyle = '#6a3fd8'
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,.85)'
    ctx.lineWidth = Math.max(1.5, celda * 0.08)
    ctx.beginPath()
    const d = s * 0.22
    ctx.moveTo(bx - d, by - d)
    ctx.lineTo(bx + d, by + d)
    ctx.moveTo(bx + d, by - d)
    ctx.lineTo(bx - d, by + d)
    ctx.stroke()
    ctx.restore()
    if (fase === 'cae' && q > 0.5) {
      const onda = (q - 0.5) / 0.5
      ctx.beginPath()
      ctx.arc(bx, by, celda * (0.6 + onda * 1.6), 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(106,63,216,${0.5 * (1 - onda)})`
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }

  dibujarNpc(ctx, npc[0], npc[1], ahora, camina, fase === 'fin' ? Math.abs(Math.sin(p * 9)) * celda * 0.3 * (1 - p) : 0)

  // panel de estado
  const actual = PASOS.findIndex((s) => (s.fases as readonly string[]).includes(fase))
  if (paso.value !== actual) paso.value = actual
  const total = fase.endsWith('2') || fase === 'fin' ? traza1.length + vistos : vistos
  if (explorados.value !== total) explorados.value = total
  const c = INICIO_FASE[fase] >= INICIO_FASE.explora2 ? COSTO_CAMINADO + demo.segunda.costo : demo.primera.costo
  if (costo.value !== c) costo.value = c
}

function bucle(ahora: number) {
  dibujar(ahora)
  cuadro = requestAnimationFrame(bucle)
}

let observador: ResizeObserver | null = null
onMounted(() => {
  dimensionar()
  observador = new ResizeObserver(() => {
    dimensionar()
    dibujar(performance.now())
  })
  observador.observe(contenedor.value!)
  inicio = performance.now()
  if (reducirMovimiento) dibujar(inicio)
  else cuadro = requestAnimationFrame(bucle)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(cuadro)
  observador?.disconnect()
})

const textoPaso = computed(
  () =>
    [
      'A* mira primero las celdas que parecen más cerca del destino.',
      'Con la ruta más barata, el NPC empieza a caminar.',
      'Un obstáculo bloquea el pasillo: la ruta ya no sirve.',
      'Recalcula desde donde está, sin volver a empezar.',
    ][paso.value] ?? '',
)
</script>

<template>
  <div class="demo">
    <div ref="contenedor" class="escena">
      <canvas ref="lienzo" role="img" aria-label="Un NPC sigue la ruta de A*, aparece un obstáculo y replanifica" />
    </div>
    <ol class="pasos" aria-label="Fases de la demostración">
      <li v-for="(s, i) in PASOS" :key="s.etiqueta" :class="{ activo: i === paso, hecho: i < paso }">
        <span class="n num">{{ i + 1 }}</span>{{ s.etiqueta }}
      </li>
    </ol>
    <div class="pie">
      <p class="frase" aria-live="off">{{ textoPaso }}</p>
      <dl class="datos num">
        <div><dt>Celdas exploradas</dt><dd>{{ explorados }}</dd></div>
        <div><dt>Costo</dt><dd>{{ costo.toFixed(2) }}</dd></div>
      </dl>
    </div>
  </div>
</template>

<style scoped>
.demo { display: flex; flex-direction: column; gap: 12px; flex: 1; min-height: 0; }
.escena { flex: 1; min-height: 180px; }
canvas { display: block; width: 100%; height: 100%; }
.pasos { display: flex; gap: 8px; margin: 0; padding: 0; list-style: none; flex-wrap: wrap; }
.pasos li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 6px;
  border-radius: 999px;
  background: var(--field);
  color: var(--ink-3);
  font-size: 12px;
  font-weight: 500;
  transition: background 0.4s var(--ease-out), color 0.4s, transform 0.5s var(--spring);
}
.pasos .n {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  font-size: 11px;
  transition: background 0.3s, color 0.3s;
}
.pasos li.activo { background: var(--ink); color: #fff; transform: scale(1.04); }
.pasos li.activo .n { background: var(--cream); color: var(--ink); }
.pasos li.hecho { color: var(--ink-2); }
.pie { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.frase { flex: 1; min-width: 220px; color: var(--ink-3); font-size: 12.5px; }
.datos { display: flex; gap: 8px; margin: 0; }
.datos div { padding: 5px 12px; border-radius: 12px; background: var(--field); }
.datos dt { color: var(--ink-3); font-size: 10px; }
.datos dd { margin: 0; font-size: 14px; font-weight: 600; }
</style>
