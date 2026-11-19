<script setup lang="ts">
/**
 * A* frente a D* Lite con obstáculos dinámicos. Un NPC avanza por su ruta y el
 * usuario bloquea o libera celdas en cualquier momento. Cada clic agrega un cambio
 * en el paso actual y vuelve a pedir POST /simular: la API no guarda estado y el
 * recorrido hasta ese paso se repite igual, así que la animación continúa sin saltos.
 * La web no calcula rutas: solo elige qué paso de la simulación mostrar.
 */
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { api, ErrorApi } from '../core/api'
import { cargarMapa, motor } from '../core/motor'
import type { CambioEnPaso, MapaDetalle, Planificacion, Posicion, ResultadoSimulacion } from '../core/types'
import MapCanvas, { type GrupoCeldas, type Trazo } from '../features/mapa/MapCanvas.vue'
import PseudocodePanel from '../features/pseudocodigo/PseudocodePanel.vue'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import CasoSelector from '../shared/CasoSelector.vue'
import Icon from '../shared/Icon.vue'
import Segmented from '../shared/Segmented.vue'

type Clave = 'astar' | 'dstar_lite'
const NOMBRE: Record<Clave, string> = { astar: 'A*', dstar_lite: 'D* Lite' }
const VELOCIDADES = [
  { valor: '3', etiqueta: 'Lento' },
  { valor: '7', etiqueta: 'Normal' },
  { valor: '16', etiqueta: 'Rápido' },
] as const

const mapaClave = ref('den011d')
const caso = ref(124)
const guia = ref<Clave>('dstar_lite')
const velocidad = ref<'3' | '7' | '16'>('7')
const verBusqueda = ref(true)
const cambios = ref<CambioEnPaso[]>([])

const detalle = shallowRef<MapaDetalle | null>(null)
const resultado = shallowRef<ResultadoSimulacion | null>(null)
const t = ref(0)
const reproduciendo = ref(false)
const cargando = ref(true)
const error = ref('')
let ticket = 0
let reloj = 0

const totalCasos = computed(() => motor.mapas.find((m) => m.nombre === mapaClave.value)?.escenarios ?? 0)
const opcionesMapa = computed(() =>
  motor.mapas.map((m) => ({ valor: m.nombre, etiqueta: m.nombre, detalle: `${(m.vertices / 1000).toFixed(1)}k` })),
)
const opcionesGuia = [
  { valor: 'dstar_lite' as const, etiqueta: 'Sigue a D* Lite' },
  { valor: 'astar' as const, etiqueta: 'Sigue a A*' },
]
const otro = computed<Clave>(() => (guia.value === 'astar' ? 'dstar_lite' : 'astar'))
const infoDStar = computed(() => motor.algoritmos.find((a) => a.clave === 'dstar_lite'))

/* ── Reproducción ─────────────────────────────────────────────────────────── */

const ultimo = computed(() => Math.max(0, (resultado.value?.recorrido.length ?? 1) - 1))
const terminado = computed(() => !!resultado.value && t.value >= ultimo.value)

function detener() {
  reproduciendo.value = false
  window.clearInterval(reloj)
}
function reproducir() {
  if (!resultado.value) return
  if (terminado.value) t.value = 0
  detener()
  reproduciendo.value = true
  reloj = window.setInterval(() => {
    if (t.value >= ultimo.value) return detener()
    t.value++
  }, 1000 / Number(velocidad.value))
}
const alternar = () => (reproduciendo.value ? detener() : reproducir())
watch(velocidad, () => reproduciendo.value && reproducir())
onBeforeUnmount(detener)

/* ── Consulta al motor ────────────────────────────────────────────────────── */

async function simular({ seguir = false, desde = 0 } = {}) {
  const mio = ++ticket
  const continuar = seguir && reproduciendo.value
  detener()
  cargando.value = true
  error.value = ''
  try {
    const [mapa, datos] = await Promise.all([
      cargarMapa(mapaClave.value),
      api.simular({
        mapa: mapaClave.value, caso: caso.value, algoritmos: [guia.value, otro.value],
        cambios: cambios.value, traza: verBusqueda.value,
      }),
    ])
    if (mio !== ticket) return
    detalle.value = mapa
    resultado.value = datos
    t.value = Math.min(desde, datos.recorrido.length - 1)
    if (continuar || !seguir) reproducir()
  } catch (e) {
    if (mio !== ticket) return
    error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

function reiniciar() {
  cambios.value = []
  void simular()
}
watch([mapaClave, caso, guia], ([nuevoMapa], [viejoMapa]) => {
  if (nuevoMapa !== viejoMapa) caso.value = Math.floor((motor.mapas.find((m) => m.nombre === nuevoMapa)?.escenarios ?? 2) / 2)
  reiniciar()
})
watch(verBusqueda, () => void simular({ seguir: true, desde: t.value }))

/* ── Estado en el paso t ──────────────────────────────────────────────────── */

const npc = computed<Posicion | null>(() => resultado.value?.recorrido[t.value] ?? null)

/** Obstáculos vigentes en el paso t, según los cambios enviados. */
const bloqueadas = computed<Posicion[]>(() => {
  const celdas = new Map<string, Posicion>()
  for (const c of cambios.value) {
    if (c.paso > t.value) continue
    for (const p of c.bloquear) celdas.set(`${p[0]},${p[1]}`, p)
    for (const p of c.liberar) celdas.delete(`${p[0]},${p[1]}`)
  }
  return [...celdas.values()]
})

/** Última planificación de un algoritmo hecha en el paso t o antes. */
function vigente(clave: string): Planificacion | undefined {
  const historial = resultado.value?.historial ?? []
  let plan: Planificacion | undefined
  for (const p of historial) if (p.algoritmo === clave && p.paso <= t.value) plan = p
  return plan
}

/** Recálculos agrupados por paso: uno por cambio de obstáculos, con A* y D* Lite juntos. */
const recalculos = computed(() => {
  const grupos = new Map<number, Partial<Record<Clave, Planificacion>>>()
  for (const p of resultado.value?.historial ?? []) {
    if (p.motivo !== 'obstaculos') continue
    const g = grupos.get(p.paso) ?? {}
    g[p.algoritmo as Clave] = p
    grupos.set(p.paso, g)
  }
  return [...grupos.entries()].map(([paso, planes], i) => ({ n: i + 1, paso, ...planes }))
})
const hechos = computed(() => recalculos.value.filter((r) => r.paso <= t.value))
const actual = computed(() => hechos.value[hechos.value.length - 1])

const acumulado = (clave: Clave, campo: 'nodos_expandidos' | 'tiempo_ms') =>
  hechos.value.reduce((suma, r) => suma + (r[clave]?.metricas[campo] ?? 0), 0)
const expandidosA = computed(() => acumulado('astar', 'nodos_expandidos'))
const expandidosD = computed(() => acumulado('dstar_lite', 'nodos_expandidos'))
const tiempoA = computed(() => acumulado('astar', 'tiempo_ms'))
const tiempoD = computed(() => acumulado('dstar_lite', 'tiempo_ms'))
const factor = computed(() => (expandidosA.value / Math.max(1, expandidosD.value)))

const costoVigente = (clave: Clave) => vigente(clave)?.costo ?? null
const coinciden = computed(() => {
  const a = costoVigente('astar')
  const d = costoVigente('dstar_lite')
  return a === null || d === null ? a === d : Math.abs(a - d) < 1e-6
})
const sinRuta = computed(() => vigente(guia.value)?.estado === 'sin_ruta')

/* ── Capas del mapa ───────────────────────────────────────────────────────── */

const trazos = computed<Trazo[]>(() => {
  const r = resultado.value
  if (!r) return []
  const capas: Trazo[] = [{ puntos: r.recorrido.slice(0, t.value + 1), color: '#2e8b57', ancho: 2.4, alfa: 0.55 }]
  const delOtro = vigente(otro.value)
  if (delOtro?.ruta.length) capas.push({ puntos: delOtro.ruta, color: '#6a3fd8', ancho: 2, alfa: 0.7, punteado: true })
  const plan = vigente(guia.value)
  if (plan?.ruta.length) {
    const restante = plan.ruta.slice(Math.max(0, t.value - plan.paso))
    capas.push({ puntos: restante, color: '#c0392b', ancho: 7, alfa: 0.2 })
    capas.push({ puntos: restante, color: '#c0392b', ancho: 2.8 })
  }
  return capas
})

const expandidas = (plan?: Planificacion) => (plan?.traza ?? []).filter((e) => e.tipo === 'expandido').map((e) => e.posicion)
const grupos = computed<GrupoCeldas[]>(() => {
  if (!verBusqueda.value) return []
  const r = actual.value
  if (r) {
    return [
      { posiciones: expandidas(r.astar), color: 'rgba(156, 195, 222, 0.85)' },
      { posiciones: expandidas(r.dstar_lite), color: 'rgba(106, 63, 216, 0.85)' },
    ]
  }
  return []
})

/* ── Interacción ──────────────────────────────────────────────────────────── */

function alternarCelda(fila: number, col: number) {
  const r = resultado.value
  const mapa = detalle.value
  if (!r || !mapa || !'.G'.includes(mapa.filas[fila][col])) return
  const igual = (p: Posicion | null) => !!p && p[0] === fila && p[1] === col
  if (igual(npc.value) || igual(r.destino)) return
  const bloqueada = bloqueadas.value.some(igual)
  aplicarCambio(bloqueada ? { liberar: [[fila, col]] } : { bloquear: [[fila, col]] })
}

function aplicarCambio(cambio: { bloquear?: Posicion[]; liberar?: Posicion[] }) {
  const paso = t.value
  const previos = cambios.value.filter((c) => c.paso < paso)
  const aqui = cambios.value.find((c) => c.paso === paso) ?? { paso, bloquear: [], liberar: [] }
  const clave = (p: Posicion) => `${p[0]},${p[1]}`
  const fuera = new Set([...(cambio.bloquear ?? []), ...(cambio.liberar ?? [])].map(clave))
  const mezcla: CambioEnPaso = {
    paso,
    bloquear: [...aqui.bloquear.filter((p) => !fuera.has(clave(p))), ...(cambio.bloquear ?? [])],
    liberar: [...aqui.liberar.filter((p) => !fuera.has(clave(p))), ...(cambio.liberar ?? [])],
  }
  cambios.value = [...previos, mezcla]
  void simular({ seguir: true, desde: paso })
}

/** Atajo para la exposición: bloquea una celda de la ruta, unos pasos por delante del NPC. */
function bloquearAdelante() {
  const plan = vigente(guia.value)
  if (!plan) return
  const restante = plan.ruta.slice(Math.max(0, t.value - plan.paso))
  if (restante.length < 3) return
  aplicarCambio({ bloquear: [restante[Math.min(6, restante.length - 2)]] })
}
function liberarTodo() {
  if (bloqueadas.value.length) aplicarCambio({ liberar: bloqueadas.value })
}
function irA(paso: number) {
  detener()
  t.value = paso
}

/* ── Textos ───────────────────────────────────────────────────────────────── */

const fmt = (n: number) => n.toLocaleString('es-PE')
const fmt2 = (n: number | null) => (n === null ? '—' : n.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }))

const narracion = computed(() => {
  const r = resultado.value
  if (!r) return ''
  if (sinRuta.value) return 'El destino quedó aislado: ningún algoritmo encuentra ruta. Libera una celda para que el NPC continúe.'
  const rec = actual.value
  if (!rec) {
    return t.value === 0
      ? 'Los dos algoritmos planifican la misma ruta inicial. Haz clic en el mapa para bloquear una celda (otra vez para liberarla) mientras el NPC avanza.'
      : 'El NPC sigue la ruta. Bloquea una celda delante de él para obligarlo a replanificar.'
  }
  const a = rec.astar?.metricas.nodos_expandidos ?? 0
  const d = rec.dstar_lite?.metricas.nodos_expandidos ?? 0
  const afectada = rec.astar?.ruta_afectada || rec.dstar_lite?.ruta_afectada
  const base = `Recálculo ${rec.n} en el paso ${rec.paso}: A* repite la búsqueda desde cero (${fmt(a)} celdas); D* Lite repara solo lo afectado (${fmt(d)} celdas).`
  return afectada ? base : `${base} El cambio no tocaba la ruta vigente, por eso D* Lite casi no trabaja.`
})

const lineaActiva = computed(() => {
  const rec = actual.value
  if (rec && t.value - rec.paso < 3) return 14
  return terminado.value && resultado.value?.llegado ? 0 : 16
})
const conteos = computed<Record<number, number>>(() => {
  const n = hechos.value.length
  const c: Record<number, number> = {}
  if (n) c[13] = c[14] = c[15] = n
  return c
})

onMounted(() => void simular())
</script>

<template>
  <section class="lab">
    <header class="lab-cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo">Simulación <em>A* contra D* Lite</em></h1>
        <p class="pagina-sub">Un NPC avanza y tú cambias el mapa. Los dos algoritmos replanifican desde la misma celda ante el mismo cambio.</p>
      </div>
      <div class="lab-selectores">
        <CasoSelector v-model="caso" :total="totalCasos" />
        <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
      </div>
    </header>

    <div class="lab-cuerpo">
      <article class="card lab-principal rise" style="--i: 1">
        <div class="lab-barra">
          <div class="lab-selectores">
            <button type="button" class="play" :aria-label="reproduciendo ? 'Pausar' : 'Reproducir'" @click="alternar">
              <Icon :name="reproduciendo ? 'pausa' : 'play'" :size="17" :stroke="2" />
            </button>
            <button type="button" class="btn" @click="reiniciar"><Icon name="reiniciar" :size="15" /> Reiniciar</button>
            <span class="pill num">Paso {{ t }} / {{ ultimo }}</span>
            <Segmented v-model="velocidad" :opciones="[...VELOCIDADES]" etiqueta="Velocidad" />
          </div>
          <div class="lab-selectores">
            <button type="button" class="btn" :disabled="terminado || cargando" @click="bloquearAdelante">
              <Icon name="bloquear" :size="15" /> Bloquear adelante
            </button>
            <button v-if="bloqueadas.length" type="button" class="btn" @click="liberarTodo">Liberar {{ bloqueadas.length }}</button>
            <button type="button" class="btn" :class="{ activo: verBusqueda }" :aria-pressed="verBusqueda" @click="verBusqueda = !verBusqueda">
              Celdas procesadas
            </button>
          </div>
        </div>

        <div class="lab-lienzo">
          <ul class="lab-leyenda" aria-label="Leyenda">
            <li><i class="punto" style="background: #2e8b57" />NPC</li>
            <li><i style="background: #c0392b" />Ruta de {{ NOMBRE[guia] }}</li>
            <li style="color: #6a3fd8"><i class="punteado" />Ruta de {{ NOMBRE[otro] }}</li>
            <li v-if="verBusqueda"><i class="celda" style="background: #9cc3de" />A* recalcula</li>
            <li v-if="verBusqueda"><i class="celda" style="background: #6a3fd8" />D* Lite repara</li>
            <li><i class="celda" style="background: rgba(58, 36, 120, 0.9)" />Obstáculo</li>
          </ul>
          <MapCanvas
            v-if="detalle && resultado"
            :mapa="detalle"
            :inicio="npc"
            :destino="resultado.destino"
            :bloqueadas="bloqueadas"
            :trazos="trazos"
            :grupos="grupos"
            interactivo
            @celda="alternarCelda"
          />
          <Transition name="lab-fundido">
            <div v-if="cargando" class="lab-velo">
              <span class="lab-spinner" />{{ motor.estado === 'listo' ? 'Replanificando…' : 'Despertando el motor…' }}
            </div>
          </Transition>
          <Transition name="lab-fundido">
            <div v-if="error" class="lab-error glass" role="alert">{{ error }}</div>
          </Transition>
        </div>

        <p class="lab-narracion" aria-live="polite">{{ narracion }}</p>
      </article>

      <aside class="lab-lateral">
        <article class="card lab-metricas rise" style="--i: 2">
          <header class="card-title">
            <span class="badge-icon"><Icon name="metricas" :size="16" /></span>
            Trabajo al replanificar
            <span class="pill" :class="coinciden ? 'pill-lime' : 'pill-danger'" style="margin-left: auto">
              {{ coinciden ? 'Mismo costo' : 'Costos distintos' }}
            </span>
          </header>
          <Segmented v-model="guia" :opciones="opcionesGuia" etiqueta="Algoritmo que sigue el NPC" />
          <div class="duelo">
            <div class="lado a">
              <span class="eyebrow">A* · recálculo completo</span>
              <strong class="display num"><AnimatedNumber :value="expandidosA" /></strong>
              <small class="num">celdas · {{ tiempoA.toFixed(1) }} ms · costo {{ fmt2(costoVigente('astar')) }}</small>
            </div>
            <div class="lado d">
              <span class="eyebrow">D* Lite · incremental</span>
              <strong class="display num"><AnimatedNumber :value="expandidosD" /></strong>
              <small class="num">celdas · {{ tiempoD.toFixed(1) }} ms · costo {{ fmt2(costoVigente('dstar_lite')) }}</small>
            </div>
          </div>
          <p class="lab-nota">
            <template v-if="hechos.length">
              En {{ hechos.length }} {{ hechos.length === 1 ? 'recálculo' : 'recálculos' }}, D* Lite procesó
              <strong>{{ factor >= 10 ? factor.toFixed(0) : factor.toFixed(1) }} veces menos celdas</strong> que A*.
            </template>
            <template v-else>Suma de celdas procesadas en los recálculos (la planificación inicial no cuenta).</template>
            Los tiempos los mide el motor y excluyen red y animación.
          </p>
        </article>

        <article class="card rise" style="--i: 3">
          <header class="card-title">
            <span class="badge-icon"><Icon name="resultados" :size="16" /></span>
            Recálculos
          </header>
          <p v-if="!recalculos.length" class="lab-nota">Aún no hay cambios de obstáculos.</p>
          <table v-else class="recalculos">
            <thead><tr><th>#</th><th>Paso</th><th>A*</th><th>D* Lite</th><th>Costo</th></tr></thead>
            <tbody>
              <tr
                v-for="r in recalculos"
                :key="r.paso"
                :class="{ actual: actual && actual.paso === r.paso, futuro: r.paso > t }"
                @click="irA(r.paso)"
              >
                <td class="num">{{ r.n }}</td>
                <td class="num">{{ r.paso }}</td>
                <td class="num">{{ fmt(r.astar?.metricas.nodos_expandidos ?? 0) }}</td>
                <td class="num fuerte">{{ fmt(r.dstar_lite?.metricas.nodos_expandidos ?? 0) }}</td>
                <td class="num">{{ r.dstar_lite?.estado === 'sin_ruta' ? 'sin ruta' : fmt2(r.dstar_lite?.costo ?? null) }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <PseudocodePanel
          v-if="infoDStar"
          class="rise"
          style="--i: 4"
          :nombre="infoDStar.nombre"
          :lineas="infoDStar.pseudocodigo"
          :activa="lineaActiva"
          :conteos="conteos"
        />
      </aside>
    </div>
  </section>
</template>

<style scoped>
.play { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; background: var(--ink); color: #fff; transition: transform 0.3s var(--spring); }
.play:active { transform: scale(0.9); }
.duelo { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.lado { display: grid; gap: 4px; padding: 12px 14px; border-radius: 16px; }
.lado.a { background: #dcebf7; }
.lado.d { background: var(--violet-soft); }
.lado strong { font-size: 34px; font-weight: 400; line-height: 1.05; letter-spacing: -0.03em; }
.lado small { color: var(--ink-3); font-size: 11px; }
.recalculos { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.recalculos th { padding: 4px 8px 6px; color: var(--ink-3); font-size: 10.5px; font-weight: 500; text-align: right; border-bottom: 1px solid var(--line); }
.recalculos td { padding: 6px 8px; text-align: right; }
.recalculos th:first-child, .recalculos td:first-child { text-align: left; }
.recalculos tbody tr { cursor: pointer; transition: background 0.2s; }
.recalculos tbody tr:hover { background: var(--field); }
.recalculos tr.actual { background: var(--violet-soft); }
.recalculos tr.futuro { opacity: 0.45; }
.fuerte { color: var(--violet); font-weight: 600; }
</style>
