<script setup lang="ts">
/**
 * Kruskal: red de patrullaje entre puntos de interés. El motor calcula con A*
 * el costo de cada par y elige el árbol; aquí solo se reproducen sus decisiones.
 */
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { api, ErrorApi } from '../core/api'
import { cargarComplementarios, cargarMapa, motor } from '../core/motor'
import type { ComplementarioInfo, MapaDetalle, Posicion, RedPatrullaje, Tramo } from '../core/types'
import MapCanvas, { type Marcador, type Trazo } from '../features/mapa/MapCanvas.vue'
import PseudocodePanel from '../features/pseudocodigo/PseudocodePanel.vue'
import PasoAPaso from '../features/reproduccion/PasoAPaso.vue'
import { usePasos } from '../features/reproduccion/usePasos'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'
import Segmented from '../shared/Segmented.vue'

const COLOR_ARBOL = '#c0392b'
const COLOR_CICLO = '#e3a52d'
const COLOR_ACTUAL = '#6a3fd8'

const mapaClave = ref('den011d')
const cantidad = ref<'5' | '7' | '10'>('7')
const semilla = ref(2026)
const puntosPropios = ref<Posicion[] | null>(null)
const modoEditar = ref(false)
const verCandidatas = ref(true)

const detalle = shallowRef<MapaDetalle | null>(null)
const red = shallowRef<RedPatrullaje | null>(null)
const info = shallowRef<ComplementarioInfo | null>(null)
const cargando = ref(true)
const error = ref('')
let ticket = 0

const decisiones = computed(() => red.value?.decisiones ?? [])
const pasos = usePasos(computed(() => decisiones.value.length), 1100)

const opcionesMapa = computed(() =>
  motor.mapas.map((m) => ({ valor: m.nombre, etiqueta: m.nombre, detalle: `${(m.vertices / 1000).toFixed(1)}k` })),
)
const opcionesCantidad = [
  { valor: '5' as const, etiqueta: '5 puntos' },
  { valor: '7' as const, etiqueta: '7' },
  { valor: '10' as const, etiqueta: '10' },
]

async function calcular() {
  const mio = ++ticket
  cargando.value = true
  error.value = ''
  try {
    const [mapa, resultado, catalogo] = await Promise.all([
      cargarMapa(mapaClave.value),
      api.patrullaje({
        mapa: mapaClave.value,
        ...(puntosPropios.value ? { puntos: puntosPropios.value } : { cantidad: Number(cantidad.value), semilla: semilla.value }),
      }),
      cargarComplementarios(),
    ])
    if (mio !== ticket) return
    detalle.value = mapa
    info.value = catalogo.find((c) => c.clave === 'kruskal') ?? null
    red.value = resultado
    pasos.reiniciar()
    pasos.reproducir()
  } catch (e) {
    if (mio !== ticket) return
    error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

watch(mapaClave, () => {
  puntosPropios.value = null
  void calcular()
})
watch(cantidad, () => {
  puntosPropios.value = null
  void calcular()
})

function sortear() {
  puntosPropios.value = null
  semilla.value++
  void calcular()
}

function editarPunto(fila: number, col: number) {
  const mapa = detalle.value
  if (!mapa || !red.value || !'.G'.includes(mapa.filas[fila][col])) return
  const actuales = [...(puntosPropios.value ?? red.value.puntos)] as Posicion[]
  const radio = Math.max(2, Math.round(Math.max(mapa.alto, mapa.ancho) / 120))
  const cerca = actuales.findIndex((p) => Math.abs(p[0] - fila) <= radio && Math.abs(p[1] - col) <= radio)
  if (cerca >= 0) {
    if (actuales.length <= 2) return
    actuales.splice(cerca, 1)
  } else {
    if (actuales.length >= 10) return
    actuales.push([fila, col])
  }
  puntosPropios.value = actuales
  void calcular()
}

const nombre = (i: number) => `P${i + 1}`
const tramoDe = (desde: number, hasta: number): Tramo | undefined =>
  red.value?.candidatas.find((t) => t.desde === desde && t.hasta === hasta)

const vistas = computed(() => decisiones.value.slice(0, pasos.indice.value))
const actual = computed(() => (pasos.indice.value > 0 ? decisiones.value[pasos.indice.value - 1] : undefined))
const costoParcial = computed(() => vistas.value.reduce((s, d) => s + (d.aceptada ? d.costo : 0), 0))
const ahorro = computed(() => {
  const r = red.value
  return r && r.costo_candidatas > 0 ? (1 - r.costo_arbol / r.costo_candidatas) * 100 : 0
})

const trazos = computed<Trazo[]>(() => {
  const r = red.value
  if (!r) return []
  const capas: Trazo[] = []
  if (verCandidatas.value) {
    for (const t of r.candidatas) capas.push({ puntos: t.ruta, color: '#78736a', ancho: 1.2, alfa: 0.22 })
  }
  for (const d of vistas.value) {
    const t = tramoDe(d.desde, d.hasta)
    if (!t || d === actual.value) continue
    capas.push(d.aceptada
      ? { puntos: t.ruta, color: COLOR_ARBOL, ancho: 3.4 }
      : { puntos: t.ruta, color: COLOR_CICLO, ancho: 1.8, alfa: 0.75, punteado: true })
  }
  const a = actual.value
  const t = a && tramoDe(a.desde, a.hasta)
  if (a && t) {
    capas.push({ puntos: t.ruta, color: COLOR_ACTUAL, ancho: 9, alfa: 0.18 })
    capas.push({ puntos: t.ruta, color: a.aceptada ? COLOR_ACTUAL : COLOR_CICLO, ancho: 3.6, punteado: !a.aceptada })
  }
  return capas
})

const marcadores = computed<Marcador[]>(() => {
  const r = red.value
  if (!r) return []
  const a = actual.value
  return r.puntos.map((pos, i) => ({
    pos, color: '#1b1915', etiqueta: String(i + 1), resaltado: !!a && (a.desde === i || a.hasta === i),
  }))
})

const lineaActiva = computed(() => {
  if (!red.value) return 0
  if (pasos.indice.value === 0) return 1
  if (pasos.terminada.value) return 9
  return actual.value?.linea ?? 0
})
const conteos = computed(() => {
  const c: Record<number, number> = {}
  if (!red.value || pasos.indice.value === 0) return c
  const aceptadas = vistas.value.filter((d) => d.aceptada).length
  c[1] = 1
  c[2] = 1
  c[3] = vistas.value.length
  c[4] = vistas.value.length
  c[5] = aceptadas
  c[6] = vistas.value.length - aceptadas
  c[7] = vistas.value.length - aceptadas
  c[8] = vistas.value.length
  if (pasos.terminada.value) c[9] = 1
  return c
})

const fmt2 = (n: number) => n.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const narracion = computed(() => {
  const r = red.value
  if (!r) return ''
  if (pasos.indice.value === 0) {
    return `A* calculó el costo óptimo entre los ${r.puntos.length} puntos: ${r.candidatas.length} pares candidatos. Kruskal los recorre de menor a mayor costo.`
  }
  if (pasos.terminada.value) {
    const bosque = r.componentes > 1 ? ` Algunos puntos no tienen ruta entre sí: es un bosque de ${r.componentes} árboles.` : ''
    return `Red completa: ${r.arbol.length} tramos y costo ${fmt2(r.costo_arbol)}, frente a ${fmt2(r.costo_candidatas)} si se uniera cada par (${ahorro.value.toFixed(0)} % menos).${bosque}`
  }
  const d = actual.value!
  const par = `${nombre(d.desde)}–${nombre(d.hasta)} (costo ${fmt2(d.costo)})`
  return d.aceptada
    ? `${par}: sus extremos están en componentes distintas del UFDS, así que el tramo entra a la red y se unen.`
    : `${par}: ${nombre(d.desde)} y ${nombre(d.hasta)} ya están conectados por la red; este tramo cerraría un ciclo y se descarta.`
})

const estadoDe = (desde: number, hasta: number) => {
  const i = decisiones.value.findIndex((d) => d.desde === desde && d.hasta === hasta)
  if (i < 0) return { clase: 'omitida', texto: 'No se evalúa', indice: -1 }
  if (i >= pasos.indice.value) return { clase: 'pendiente', texto: 'Pendiente', indice: i }
  return decisiones.value[i].aceptada
    ? { clase: 'aceptada', texto: 'Entra', indice: i }
    : { clase: 'ciclo', texto: 'Ciclo', indice: i }
}

onMounted(calcular)
</script>

<template>
  <section class="lab">
    <header class="lab-cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo">Patrullaje <em>con Kruskal</em></h1>
        <p class="pagina-sub">La red más corta que conecta los puntos de interés: un árbol de expansión mínima sobre los costos de A*.</p>
      </div>
      <div class="lab-selectores">
        <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
        <Segmented v-model="cantidad" :opciones="opcionesCantidad" etiqueta="Puntos de interés" />
      </div>
    </header>

    <div class="lab-cuerpo">
      <article class="card lab-principal rise" style="--i: 1">
        <div class="lab-barra">
          <PasoAPaso :pasos="pasos" :total="decisiones.length" etiqueta="Arista" />
          <div class="lab-selectores">
            <button type="button" class="btn" :class="{ activo: verCandidatas }" :aria-pressed="verCandidatas" @click="verCandidatas = !verCandidatas">
              Candidatas
            </button>
            <button type="button" class="btn" @click="sortear"><Icon name="dado" :size="15" /> Sortear</button>
            <button type="button" class="btn" :class="{ activo: modoEditar }" :aria-pressed="modoEditar" @click="modoEditar = !modoEditar">
              <Icon name="bandera" :size="15" /> Editar puntos
            </button>
          </div>
        </div>
        <p v-if="modoEditar" class="lab-pista">Clic en una celda libre para agregar un punto (máximo 10); clic sobre un punto para quitarlo.</p>

        <div class="lab-lienzo">
          <ul class="lab-leyenda" aria-label="Leyenda">
            <li><i class="punto" style="background: #1b1915" />Punto de interés</li>
            <li><i style="background: #c0392b" />Red</li>
            <li style="color: #e3a52d"><i class="punteado" />Ciclo descartado</li>
            <li><i style="background: #6a3fd8" />Arista evaluada</li>
            <li v-if="verCandidatas"><i style="background: #78736a; opacity: 0.4" />Candidata (A*)</li>
          </ul>
          <MapCanvas
            v-if="detalle"
            :mapa="detalle"
            :trazos="trazos"
            :marcadores="marcadores"
            :interactivo="modoEditar"
            @celda="editarPunto"
          />
          <Transition name="lab-fundido">
            <div v-if="cargando" class="lab-velo">
              <span class="lab-spinner" />{{ motor.estado === 'listo' ? 'A* entre cada par de puntos…' : 'Despertando el motor…' }}
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
            <span class="badge-icon"><Icon name="red" :size="16" /></span>
            Red de patrullaje
            <span v-if="red && red.componentes > 1" class="pill pill-danger" style="margin-left: auto">Bosque de {{ red.componentes }}</span>
          </header>
          <div class="lab-grande">
            <strong class="display num"><AnimatedNumber :value="costoParcial" :decimals="2" /></strong>
            <small v-if="red">de {{ fmt2(red.costo_arbol) }}</small>
            <span v-if="red && pasos.terminada.value" class="pill pill-lime">{{ ahorro.toFixed(0) }} % menos que unir cada par</span>
          </div>
          <dl class="lab-datos">
            <div><dt>Puntos</dt><dd class="num">{{ red?.puntos.length ?? 0 }}</dd></div>
            <div><dt>Pares con ruta</dt><dd class="num">{{ red?.candidatas.length ?? 0 }}</dd></div>
            <div><dt title="Las búsquedas A* entre cada par">A*</dt><dd class="num">{{ (red?.tiempo_rutas_ms ?? 0).toFixed(0) }}<small> ms</small></dd></div>
            <div><dt title="Solo el algoritmo de Kruskal">Kruskal</dt><dd class="num">{{ (red?.tiempo_kruskal_ms ?? 0).toFixed(3) }}<small> ms</small></dd></div>
          </dl>
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

        <article v-if="red" class="card rise" style="--i: 4">
          <header class="card-title">
            <span class="badge-icon"><Icon name="resultados" :size="16" /></span>
            Aristas en orden de costo
          </header>
          <ol class="aristas">
            <li
              v-for="t in red.candidatas"
              :key="`${t.desde}-${t.hasta}`"
              :class="[estadoDe(t.desde, t.hasta).clase, { actual: actual && actual.desde === t.desde && actual.hasta === t.hasta }]"
            >
              <button type="button" :disabled="estadoDe(t.desde, t.hasta).indice < 0" @click="pasos.irA(estadoDe(t.desde, t.hasta).indice + 1)">
                <span class="par">{{ nombre(t.desde) }}–{{ nombre(t.hasta) }}</span>
                <span class="num costo">{{ fmt2(t.costo) }}</span>
                <span class="estado">{{ estadoDe(t.desde, t.hasta).texto }}</span>
              </button>
            </li>
          </ol>
          <p class="lab-nota">Kruskal se detiene al tener V − 1 aristas: las restantes no se evalúan.</p>
        </article>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.aristas { display: grid; gap: 4px; margin: 0 0 8px; padding: 0; list-style: none; }
.aristas button {
  display: grid; grid-template-columns: 1fr auto 86px; align-items: center; gap: 10px; width: 100%;
  padding: 6px 10px; border-radius: 10px; text-align: left; font-size: 12.5px; transition: background 0.2s;
}
.aristas button:hover:not(:disabled) { background: var(--field); }
.aristas button:disabled { cursor: default; }
.par { font-weight: 600; }
.costo { color: var(--ink-2); }
.estado { justify-self: end; padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 500; background: var(--field); color: var(--ink-3); }
.aceptada .estado { background: #f8dcd8; color: #8c281c; }
.ciclo .estado { background: var(--cream); color: #6b4c0d; }
.omitida { opacity: 0.45; }
.pendiente { opacity: 0.7; }
.actual button { background: var(--violet-soft); }
</style>
