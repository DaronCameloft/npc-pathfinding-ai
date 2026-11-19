<script setup lang="ts">
/**
 * Edmonds-Karp sobre una zona del mapa: cuántos NPC cruzan a la vez sin compartir
 * celdas (flujo máximo) y qué celdas cierran el paso (corte mínimo). El motor
 * resuelve todo; aquí se reproducen los caminos aumentantes.
 */
import { computed, nextTick, onMounted, ref, shallowRef, watch } from 'vue'
import { api, ErrorApi } from '../core/api'
import { cargarComplementarios, cargarMapa, motor } from '../core/motor'
import type { AnalisisPasillo, ComplementarioInfo, Direccion, MapaDetalle, Posicion } from '../core/types'
import MapCanvas, { type GrupoCeldas, type Trazo, type Zona } from '../features/mapa/MapCanvas.vue'
import PseudocodePanel from '../features/pseudocodigo/PseudocodePanel.vue'
import PasoAPaso from '../features/reproduccion/PasoAPaso.vue'
import { usePasos } from '../features/reproduccion/usePasos'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'
import Segmented from '../shared/Segmented.vue'

const LADO_MAXIMO = 64
/** Zonas con un cuello de botella claro, halladas recorriendo cada mapa con el motor. */
const SUGERIDAS: Record<string, { zona: Zona; direccion: Direccion }> = {
  den011d: { zona: [24, 156, 71, 203], direccion: 'vertical' },
  brc100d: { zona: [276, 228, 323, 275], direccion: 'horizontal' },
  brc201d: { zona: [96, 24, 143, 71], direccion: 'horizontal' },
}
const COLORES = ['#2e8b57', '#2a5b7c', '#6a3fd8', '#b7791f', '#1b8a8a', '#a33d6b', '#5a6b1f', '#3a4fb0']

const mapaClave = ref('den011d')
const direccion = ref<Direccion>('vertical')
const zona = ref<Zona>(SUGERIDAS.den011d.zona)
const bloqueadas = ref<Posicion[]>([])
const modo = ref<'ver' | 'zona' | 'bloquear'>('ver')
const esquina = ref<Posicion | null>(null)

const detalle = shallowRef<MapaDetalle | null>(null)
const analisis = shallowRef<AnalisisPasillo | null>(null)
const info = shallowRef<ComplementarioInfo | null>(null)
const lienzo = ref<InstanceType<typeof MapCanvas> | null>(null)
const cargando = ref(true)
const error = ref('')
let ticket = 0

const aumentos = computed(() => analisis.value?.aumentos ?? [])
const pasos = usePasos(computed(() => aumentos.value.length), 1300)

const opcionesMapa = computed(() =>
  motor.mapas.map((m) => ({ valor: m.nombre, etiqueta: m.nombre, detalle: `${(m.vertices / 1000).toFixed(1)}k` })),
)
const opcionesDireccion = [
  { valor: 'horizontal' as const, etiqueta: 'Izquierda → derecha' },
  { valor: 'vertical' as const, etiqueta: 'Arriba → abajo' },
]

async function calcular(enfocar = false) {
  const mio = ++ticket
  cargando.value = true
  error.value = ''
  try {
    const [mapa, resultado, catalogo] = await Promise.all([
      cargarMapa(mapaClave.value),
      api.pasillo({ mapa: mapaClave.value, zona: zona.value, direccion: direccion.value, bloqueadas: bloqueadas.value }),
      cargarComplementarios(),
    ])
    if (mio !== ticket) return
    detalle.value = mapa
    info.value = catalogo.find((c) => c.clave === 'edmonds_karp') ?? null
    analisis.value = resultado
    pasos.reiniciar()
    pasos.reproducir()
    if (enfocar) {
      await nextTick()
      lienzo.value?.enfocar(...zona.value)
    }
  } catch (e) {
    if (mio !== ticket) return
    error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

/** Al cambiar de mapa también cambia la dirección sugerida: no hay que calcular dos veces. */
let porCambioDeMapa = false

watch(mapaClave, (nombre) => {
  const sugerida = SUGERIDAS[nombre] ?? SUGERIDAS.den011d
  porCambioDeMapa = true
  void nextTick(() => (porCambioDeMapa = false))
  zona.value = sugerida.zona
  direccion.value = sugerida.direccion
  bloqueadas.value = []
  void calcular(true)
})
watch(direccion, () => {
  if (porCambioDeMapa) return
  bloqueadas.value = []
  void calcular()
})

const dentro = (f: number, c: number) => {
  const [f0, c0, f1, c1] = zona.value
  return f >= f0 && f <= f1 && c >= c0 && c <= c1
}

function alClic(fila: number, col: number) {
  const mapa = detalle.value
  if (!mapa) return
  if (modo.value === 'zona') {
    if (!esquina.value) {
      esquina.value = [fila, col]
      return
    }
    const [fa, ca] = esquina.value
    const limitar = (a: number, b: number) => (b >= a ? Math.min(b, a + LADO_MAXIMO - 1) : Math.max(b, a - LADO_MAXIMO + 1))
    const f1 = limitar(fa, fila)
    const c1 = limitar(ca, col)
    zona.value = [Math.min(fa, f1), Math.min(ca, c1), Math.max(fa, f1), Math.max(ca, c1)]
    esquina.value = null
    modo.value = 'ver'
    bloqueadas.value = []
    void calcular(true)
    return
  }
  if (modo.value === 'bloquear') {
    if (!'.G'.includes(mapa.filas[fila][col]) || !dentro(fila, col)) return
    const i = bloqueadas.value.findIndex((p) => p[0] === fila && p[1] === col)
    bloqueadas.value = i >= 0 ? bloqueadas.value.filter((_, j) => j !== i) : [...bloqueadas.value, [fila, col]]
    void calcular()
  }
}

function alternarModo(nuevo: 'zona' | 'bloquear') {
  modo.value = modo.value === nuevo ? 'ver' : nuevo
  esquina.value = null
}

function cerrarCorte() {
  const a = analisis.value
  if (!a?.corte.length) return
  bloqueadas.value = [...bloqueadas.value, ...a.corte]
  void calcular()
}
function reabrir() {
  bloqueadas.value = []
  void calcular()
}

const actual = computed(() => (pasos.indice.value > 0 ? aumentos.value[pasos.indice.value - 1] : undefined))

/** Un aumento que pasa por celdas de caminos anteriores redirige flujo por aristas inversas. */
const redirige = computed(() => {
  const i = pasos.indice.value
  if (i < 2 || !actual.value) return false
  const previas = new Set(aumentos.value.slice(0, i - 1).flatMap((a) => a.celdas.map((p) => `${p[0]},${p[1]}`)))
  return actual.value.celdas.some((p) => previas.has(`${p[0]},${p[1]}`))
})

const trazos = computed<Trazo[]>(() => {
  const a = analisis.value
  if (!a) return []
  if (pasos.terminada.value) {
    return a.caminos.map((camino, i) => ({ puntos: camino, color: COLORES[i % COLORES.length], ancho: 3.2 }))
  }
  const capas: Trazo[] = aumentos.value
    .slice(0, Math.max(0, pasos.indice.value - 1))
    .map((au) => ({ puntos: au.celdas, color: '#78736a', ancho: 2, alfa: 0.45 }))
  if (actual.value) {
    capas.push({ puntos: actual.value.celdas, color: '#6a3fd8', ancho: 10, alfa: 0.16 })
    capas.push({ puntos: actual.value.celdas, color: '#6a3fd8', ancho: 3.4 })
  }
  return capas
})

const grupos = computed<GrupoCeldas[]>(() => {
  const a = analisis.value
  if (!a) return []
  const capas: GrupoCeldas[] = [
    { posiciones: a.entradas, color: 'rgba(46, 139, 87, 0.45)' },
    { posiciones: a.salidas, color: 'rgba(27, 25, 21, 0.28)' },
  ]
  if (pasos.terminada.value && a.corte.length) capas.push({ posiciones: a.corte, color: '#c0392b', cruz: true })
  return capas
})

const zonaVisible = computed<Zona | null>(() => {
  if (modo.value === 'zona' && esquina.value) return [esquina.value[0], esquina.value[1], esquina.value[0], esquina.value[1]]
  return zona.value
})

const lineaActiva = computed(() => {
  if (!analisis.value) return 0
  if (pasos.terminada.value) return 9
  return pasos.indice.value === 0 ? 1 : 8
})
const conteos = computed(() => {
  const i = pasos.indice.value
  const c: Record<number, number> = {}
  if (!analisis.value || i === 0) return c
  const fin = pasos.terminada.value ? 1 : 0
  c[1] = 1
  c[2] = i + fin
  c[3] = i + fin
  for (const n of [5, 6, 7, 8]) c[n] = i
  if (fin) {
    c[4] = 1
    c[9] = 1
    c[10] = 1
  }
  return c
})

const narracion = computed(() => {
  const a = analisis.value
  if (!a) return ''
  if (modo.value === 'zona') return esquina.value ? 'Ahora la esquina opuesta (máximo 64 celdas por lado).' : 'Clic en una esquina de la nueva zona.'
  if (pasos.indice.value === 0) {
    return `La zona tiene ${a.celdas.toLocaleString('es-PE')} celdas libres. Cada una admite un solo NPC (capacidad 1); entran ${a.entradas.length} por el borde verde y salen ${a.salidas.length} por el opuesto.`
  }
  if (pasos.terminada.value) {
    if (!a.flujo_maximo) return 'Ningún NPC puede cruzar: no queda camino entre los dos bordes.'
    return `Flujo máximo: ${a.flujo_maximo} NPC a la vez. El último BFS ya no llega a la salida; lo que alcanzó define el corte mínimo: ${a.corte.length} celdas (en rojo) que, bloqueadas, cierran el pasillo.`
  }
  const base = `Camino aumentante ${pasos.indice.value}: el BFS halló el camino más corto en la red residual (${actual.value!.celdas.length} celdas). Flujo = ${actual.value!.flujo}.`
  return redirige.value ? `${base} Pasa por celdas de un camino anterior: el flujo se redirige por aristas inversas.` : base
})

onMounted(() => calcular(true))
</script>

<template>
  <section class="lab">
    <header class="lab-cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo">Pasillo <em>con Edmonds-Karp</em></h1>
        <p class="pagina-sub">Cuántos NPC cruzan una zona a la vez sin chocar, y qué celdas bastan para cerrarla (flujo máximo = corte mínimo).</p>
      </div>
      <div class="lab-selectores">
        <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
        <Segmented v-model="direccion" :opciones="opcionesDireccion" etiqueta="Dirección" />
      </div>
    </header>

    <div class="lab-cuerpo">
      <article class="card lab-principal rise" style="--i: 1">
        <div class="lab-barra">
          <PasoAPaso :pasos="pasos" :total="aumentos.length" etiqueta="Aumento" />
          <div class="lab-selectores">
            <button v-if="bloqueadas.length" type="button" class="btn" @click="reabrir">Reabrir ({{ bloqueadas.length }})</button>
            <button v-else type="button" class="btn" :disabled="!analisis?.corte.length" @click="cerrarCorte">
              <Icon name="candado" :size="15" /> Cerrar el corte
            </button>
            <button type="button" class="btn" :class="{ activo: modo === 'bloquear' }" @click="alternarModo('bloquear')">
              <Icon name="bloquear" :size="15" /> Bloquear
            </button>
            <button type="button" class="btn" :class="{ activo: modo === 'zona' }" @click="alternarModo('zona')">
              <Icon name="ajustar" :size="15" /> Elegir zona
            </button>
          </div>
        </div>

        <div class="lab-lienzo">
          <ul class="lab-leyenda" aria-label="Leyenda">
            <li><i class="celda" style="background: rgba(46, 139, 87, 0.55)" />Entrada</li>
            <li><i class="celda" style="background: rgba(27, 25, 21, 0.35)" />Salida</li>
            <li><i style="background: #6a3fd8" />Camino aumentante</li>
            <li><i class="celda" style="background: #c0392b" />Corte mínimo</li>
            <li><i class="celda" style="background: rgba(58, 36, 120, 0.9)" />Bloqueada</li>
          </ul>
          <MapCanvas
            v-if="detalle"
            ref="lienzo"
            :mapa="detalle"
            :zona="zonaVisible"
            :trazos="trazos"
            :grupos="grupos"
            :bloqueadas="bloqueadas"
            :interactivo="modo !== 'ver'"
            @celda="alClic"
          />
          <Transition name="lab-fundido">
            <div v-if="cargando" class="lab-velo">
              <span class="lab-spinner" />{{ motor.estado === 'listo' ? 'Calculando el flujo…' : 'Despertando el motor…' }}
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
            <span class="badge-icon"><Icon name="flujo" :size="16" /></span>
            Capacidad del pasillo
            <span v-if="bloqueadas.length" class="pill pill-violet" style="margin-left: auto">{{ bloqueadas.length }} bloqueadas</span>
          </header>
          <div class="lab-grande">
            <strong class="display num"><AnimatedNumber :value="pasos.terminada.value ? (analisis?.flujo_maximo ?? 0) : (actual?.flujo ?? 0)" /></strong>
            <small>NPC a la vez</small>
            <span v-if="analisis && pasos.terminada.value" class="pill" :class="analisis.flujo_maximo ? 'pill-danger' : 'pill-lime'">
              {{ analisis.flujo_maximo ? `Corte de ${analisis.corte.length} celdas` : 'Pasillo cerrado' }}
            </span>
          </div>
          <dl class="lab-datos">
            <div><dt>Celdas</dt><dd class="num">{{ (analisis?.celdas ?? 0).toLocaleString('es-PE') }}</dd></div>
            <div><dt>Entradas</dt><dd class="num">{{ analisis?.entradas.length ?? 0 }}</dd></div>
            <div><dt>Salidas</dt><dd class="num">{{ analisis?.salidas.length ?? 0 }}</dd></div>
            <div><dt title="Solo Edmonds-Karp, medido en el motor">Motor</dt><dd class="num">{{ (analisis?.tiempo_ms ?? 0).toFixed(1) }}<small> ms</small></dd></div>
          </dl>
          <p class="lab-nota">
            Cada celda se divide en entrada y salida unidas por una arista de capacidad 1. Por el teorema de Menger, el flujo
            máximo es el número de caminos sin celdas en común, y el corte mínimo tiene exactamente ese tamaño.
          </p>
        </article>

        <PseudocodePanel
          v-if="info"
          class="rise"
          style="--i: 3"
          :nombre="info.nombre"
          :lineas="info.pseudocodigo"
          :activa="lineaActiva"
          :conteos="conteos"
        />
      </aside>
    </div>
  </section>
</template>
