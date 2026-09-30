<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { api, ErrorApi } from '../core/api'
import { motor } from '../core/motor'
import type { Ejecucion, Escenario, MapaDetalle, Posicion } from '../core/types'
import MapCanvas, { type InfoCelda } from '../features/mapa/MapCanvas.vue'
import { narrar } from '../features/pseudocodigo/narracion'
import PseudocodePanel from '../features/pseudocodigo/PseudocodePanel.vue'
import { useConteos } from '../features/pseudocodigo/useConteoLineas'
import PlaybackDock from '../features/reproduccion/PlaybackDock.vue'
import { usePlayback, velocidadSugerida } from '../features/reproduccion/usePlayback'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'
import CasoSelector from '../shared/CasoSelector.vue'
import Segmented from '../shared/Segmented.vue'
import { alternarPanel, ui } from '../core/ui'

const mapaClave = ref('den011d')
const caso = ref(375)
const algoritmo = ref('astar')
const escenario = ref<Escenario | null>(null)
const detalle = shallowRef<MapaDetalle | null>(null)
const ejecucion = shallowRef<Ejecucion | null>(null)
const bloqueadas = ref<Posicion[]>([])
const modoBloqueo = ref(false)
const tarjeta = ref<HTMLElement | null>(null)
const pantallaCompleta = ref(false)
const cargando = ref(true)
const error = ref('')
const hover = ref<{ info: InfoCelda; x: number; y: number } | null>(null)

const cacheMapas = new Map<string, MapaDetalle>()
let ticket = 0

const traza = computed(() => ejecucion.value?.traza ?? [])
const total = computed(() => traza.value.length)
const pb = usePlayback(total)
const conteos = useConteos(traza, pb.indice)

const infoAlgoritmo = computed(() => motor.algoritmos.find((a) => a.clave === algoritmo.value))
const opcionesMapa = computed(() =>
  motor.mapas.map((m) => ({ valor: m.nombre, etiqueta: m.nombre, detalle: `${(m.vertices / 1000).toFixed(1)}k` })),
)
const opcionesAlgoritmo = computed(() => motor.algoritmos.map((a) => ({ valor: a.clave, etiqueta: a.nombre.replace(/ \(.*\)/, '').replace('Voraz primero el mejor', 'Voraz') })))
const totalCasos = computed(() => motor.mapas.find((m) => m.nombre === mapaClave.value)?.escenarios ?? 0)

const eventoActual = computed(() => (pb.indice.value > 0 ? traza.value[pb.indice.value - 1] : undefined))
const terminada = computed(() => !!ejecucion.value && pb.indice.value >= total.value && total.value > 0)

const lineaActiva = computed(() => {
  const lineas = infoAlgoritmo.value?.pseudocodigo ?? []
  if (terminada.value) {
    const patron = ejecucion.value?.estado === 'encontrada' ? /es el destino/ : /SIN_RUTA/
    return lineas.find((l) => patron.test(l.texto))?.numero ?? 0
  }
  return eventoActual.value?.linea ?? 0
})

const narracion = computed(() => {
  const e = ejecucion.value
  if (e && terminada.value) {
    return e.estado === 'encontrada'
      ? `Ruta encontrada: ${e.ruta.length - 1} pasos y costo ${e.costo?.toLocaleString('es-PE', { maximumFractionDigits: 4 })}. Se reconstruye siguiendo los padres desde el destino.`
      : 'No existe ruta entre el inicio y el destino con los obstáculos actuales.'
  }
  return narrar(algoritmo.value, eventoActual.value)
})

const comparacionOptimo = computed(() => {
  const e = ejecucion.value
  if (!e || e.costo === null || !escenario.value || bloqueadas.value.length) return null
  const dif = e.costo - escenario.value.optimo
  if (Math.abs(dif) < 1e-5) return { texto: 'Igual al óptimo publicado', clase: 'pill-lime' }
  return { texto: `+${((dif / escenario.value.optimo) * 100).toFixed(1)} % sobre el óptimo`, clase: 'pill-gold' }
})

const TERRENO: Record<string, string> = { '.': 'Transitable', G: 'Transitable', '@': 'Muro', O: 'Muro', T: 'Árbol', S: 'Pantano', W: 'Agua' }

async function cargarDetalle(nombre: string) {
  if (!cacheMapas.has(nombre)) cacheMapas.set(nombre, await api.mapa(nombre))
  return cacheMapas.get(nombre)!
}

async function ejecutar(modo: 'reproducir' | 'final') {
  const mio = ++ticket
  cargando.value = true
  error.value = ''
  try {
    const [mapa, pagina] = await Promise.all([
      cargarDetalle(mapaClave.value),
      api.escenarios(mapaClave.value, caso.value, 1),
    ])
    if (mio !== ticket) return
    detalle.value = mapa
    escenario.value = pagina.escenarios[0] ?? null
    const resultado = await api.buscar({
      mapa: mapaClave.value, caso: caso.value, algoritmo: algoritmo.value, traza: true,
      bloqueadas: bloqueadas.value,
    })
    if (mio !== ticket) return
    ejecucion.value = resultado
    await nextTick()
    if (modo === 'final') pb.alFinal()
    else {
      pb.velocidad.value = velocidadSugerida(resultado.traza.length)
      pb.reproducir()
    }
  } catch (e) {
    if (mio !== ticket) return
    error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

watch([mapaClave, caso, algoritmo], ([nuevoMapa], [viejoMapa, viejoCaso]) => {
  if (nuevoMapa !== viejoMapa) {
    caso.value = Math.floor((motor.mapas.find((m) => m.nombre === nuevoMapa)?.escenarios ?? 2) / 2)
  }
  if (nuevoMapa !== viejoMapa || caso.value !== viejoCaso) bloqueadas.value = []
  void ejecutar('reproducir')
})

function alternarBloqueo(fila: number, col: number) {
  const mapa = detalle.value
  const escena = escenario.value
  if (!mapa || !escena) return
  if (!'.G'.includes(mapa.filas[fila][col])) return
  const esExtremo = (p: Posicion) => p[0] === fila && p[1] === col
  if (esExtremo(escena.inicio) || esExtremo(escena.destino)) return
  const i = bloqueadas.value.findIndex(esExtremo)
  bloqueadas.value = i >= 0 ? bloqueadas.value.filter((_, j) => j !== i) : [...bloqueadas.value, [fila, col]]
  void ejecutar('final')
}
function limpiarBloqueos() {
  bloqueadas.value = []
  void ejecutar('final')
}

function alHover(info: InfoCelda | null, x: number, y: number) {
  hover.value = info ? { info, x, y } : null
}

function alternarPantallaCompleta() {
  if (document.fullscreenElement) void document.exitFullscreen()
  else void tarjeta.value?.requestFullscreen?.()
}
const alCambiarPantalla = () => {
  pantallaCompleta.value = document.fullscreenElement === tarjeta.value
}

function alTeclado(e: KeyboardEvent) {
  if ((e.target as HTMLElement).closest('input, select, textarea')) return
  if (e.ctrlKey || e.metaKey || e.altKey) return
  if (e.key === 'f' || e.key === 'F') { alternarPantallaCompleta(); return }
  if (e.key === 'p' || e.key === 'P') { alternarPanel(); return }
  if (e.code === 'Space') { e.preventDefault(); pb.alternar() }
  else if (e.key === 'ArrowRight') pb.paso(e.shiftKey ? 50 : 1)
  else if (e.key === 'ArrowLeft') pb.paso(e.shiftKey ? -50 : -1)
  else if (e.key === 'Home') pb.reiniciar()
  else if (e.key === 'End') pb.alFinal()
}

onMounted(() => {
  window.addEventListener('keydown', alTeclado)
  document.addEventListener('fullscreenchange', alCambiarPantalla)
  void ejecutar('reproducir')
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', alTeclado)
  document.removeEventListener('fullscreenchange', alCambiarPantalla)
  if (document.fullscreenElement) void document.exitFullscreen()
})

const costoTexto = computed(() => ejecucion.value?.costo ?? 0)
const fmt = (n: number) => n.toLocaleString('es-PE')
const mensajeCarga = computed(() => (motor.estado === 'listo' ? 'Calculando en el motor…' : 'Despertando el motor…'))
</script>

<template>
  <section class="explorar">
    <header class="cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo titulo">Explorar <em>paso a paso</em></h1>
        <p class="pagina-sub">Un algoritmo, celda por celda, con su pseudocódigo en vivo.</p>
      </div>
      <div class="selectores">
        <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
        <Segmented v-model="algoritmo" :opciones="opcionesAlgoritmo" etiqueta="Algoritmo" />
      </div>
    </header>

    <div class="cuerpo" :class="{ 'sin-panel': !ui.panelLateral }">
      <article ref="tarjeta" class="card mapa-card rise" :class="{ completa: pantallaCompleta }" style="--i: 1">
        <div class="mapa-top">
          <CasoSelector v-model="caso" :total="totalCasos" />
          <Segmented v-if="pantallaCompleta" v-model="algoritmo" :opciones="opcionesAlgoritmo" etiqueta="Algoritmo" />

          <ul v-if="!ui.panelLateral || pantallaCompleta" class="resumen-corto num" aria-label="Resumen de la búsqueda">
            <li><span>Costo</span>{{ (ejecucion?.costo ?? 0).toFixed(2) }}</li>
            <li><span>Expandidos</span>{{ fmt(conteos.expandidos) }}</li>
            <li v-if="lineaActiva"><span>Línea</span>{{ lineaActiva }}</li>
          </ul>

          <div class="acciones">
            <button
              type="button"
              class="ic-btn"
              :class="{ activo: ui.panelLateral }"
              :aria-pressed="ui.panelLateral"
              :aria-label="ui.panelLateral ? 'Ocultar pseudocódigo y métricas' : 'Mostrar pseudocódigo y métricas'"
              :title="(ui.panelLateral ? 'Ocultar' : 'Mostrar') + ' pseudocódigo y métricas (P)'"
              @click="alternarPanel"
            >
              <Icon name="panel_der" :size="17" />
            </button>
            <button
              type="button"
              class="ic-btn"
              :aria-label="pantallaCompleta ? 'Salir de pantalla completa' : 'Mapa en pantalla completa'"
              :title="(pantallaCompleta ? 'Salir de pantalla completa' : 'Mapa en pantalla completa') + ' (F)'"
              @click="alternarPantallaCompleta"
            >
              <Icon :name="pantallaCompleta ? 'pantalla_salir' : 'pantalla'" :size="17" />
            </button>
            <button v-if="bloqueadas.length" type="button" class="btn ligero" @click="limpiarBloqueos">Quitar {{ bloqueadas.length }}</button>
            <button type="button" class="btn" :class="{ activo: modoBloqueo }" :aria-pressed="modoBloqueo" @click="modoBloqueo = !modoBloqueo">
              <Icon name="bloquear" :size="15" /> Bloquear celdas
            </button>
          </div>
        </div>

        <div class="lienzo">
          <ul class="leyenda" aria-label="Leyenda">
            <li><i style="background: var(--trace-inicio)" />Inicio</li>
            <li><i class="hueco" />Destino</li>
            <li><i style="background: var(--trace-frontera)" />Frontera</li>
            <li><i style="background: var(--trace-expandido)" />Expandido</li>
            <li><i style="background: var(--trace-ruta)" />Ruta</li>
          </ul>

          <MapCanvas
            v-if="detalle"
            :mapa="detalle"
            :traza="traza"
            :indice="pb.indice.value"
            :ruta="ejecucion?.ruta ?? []"
            :mostrar-ruta="terminada && ejecucion?.estado === 'encontrada'"
            :inicio="escenario?.inicio"
            :destino="escenario?.destino"
            :bloqueadas="bloqueadas"
            :interactivo="modoBloqueo"
            @celda="alternarBloqueo"
            @hover="alHover"
          />
          <Transition name="fundido">
            <div v-if="cargando" class="velo"><span class="spinner" />{{ mensajeCarga }}</div>
          </Transition>
          <Transition name="fundido">
            <div v-if="error" class="error glass" role="alert">{{ error }}</div>
          </Transition>
          <div v-if="hover" class="tip glass" :style="{ transform: `translate(${hover.x + 16}px, ${hover.y + 16}px)` }">
            <strong class="num">({{ hover.info.fila }}, {{ hover.info.col }})</strong>
            <span>{{ TERRENO[hover.info.terreno] }}<template v-if="hover.info.estado"> · {{ hover.info.estado === 2 ? 'Expandida' : 'En la frontera' }}</template></span>
            <span v-if="hover.info.estado" class="num mono">g {{ hover.info.g.toFixed(2) }} · h {{ hover.info.h.toFixed(2) }} · f {{ (hover.info.g + hover.info.h).toFixed(2) }}</span>
          </div>
        </div>

        <p class="narracion" aria-live="polite">
          {{ narracion }}
        </p>

        <PlaybackDock
          :reproduciendo="pb.reproduciendo.value"
          :indice="pb.indice.value"
          :total="total"
          :velocidad="pb.velocidad.value"
          :deshabilitado="!total"
          @alternar="pb.alternar"
          @paso="pb.paso"
          @reiniciar="pb.reiniciar"
          @final="pb.alFinal"
          @buscar="pb.irA"
          @velocidad="pb.velocidad.value = $event"
        />
      </article>

      <aside class="lateral" :aria-hidden="!ui.panelLateral" :inert="!ui.panelLateral">
        <PseudocodePanel
          v-if="infoAlgoritmo"
          class="rise"
          style="--i: 2"
          :nombre="infoAlgoritmo.nombre"
          :lineas="infoAlgoritmo.pseudocodigo"
          :activa="lineaActiva"
          :conteos="conteos.lineas"
        />

        <article class="card metricas rise" style="--i: 3">
          <header class="card-title">
            <span class="badge-icon"><Icon name="metricas" :size="16" /></span>
            Métricas
          </header>
          <div class="costo">
            <span class="eyebrow">Costo de la ruta</span>
            <div class="costo-valor">
              <strong class="display num"><AnimatedNumber :value="costoTexto" :decimals="2" /></strong>
              <span v-if="ejecucion?.estado === 'sin_ruta'" class="pill pill-danger">Sin ruta</span>
              <span v-else-if="comparacionOptimo" class="pill" :class="comparacionOptimo.clase">{{ comparacionOptimo.texto }}</span>
              <span v-else-if="bloqueadas.length" class="pill pill-violet">{{ bloqueadas.length }} bloqueadas</span>
            </div>
          </div>
          <dl class="datos">
            <div><dt>Expandidos</dt><dd class="num">{{ fmt(conteos.expandidos) }}</dd></div>
            <div><dt>Descubiertos</dt><dd class="num">{{ fmt(ejecucion?.metricas.nodos_descubiertos ?? 0) }}</dd></div>
            <div><dt>Frontera máx.</dt><dd class="num">{{ fmt(ejecucion?.metricas.max_frontera ?? 0) }}</dd></div>
            <div><dt title="Lo mide el motor: excluye la animación, la red y la traza">Motor</dt><dd class="num">{{ (ejecucion?.metricas.tiempo_ms ?? 0).toFixed(1) }}<small> ms</small></dd></div>
          </dl>
        </article>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.explorar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: 100%;
  min-height: 640px;
}
.cabecera { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.titulo { margin-top: 2px; }
.selectores { display: flex; gap: 12px; flex-wrap: wrap; }

.cuerpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  column-gap: 18px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns 0.6s var(--ease-out), column-gap 0.6s var(--ease-out);
}
.cuerpo.sin-panel { grid-template-columns: minmax(0, 1fr) 0px; column-gap: 0; }
.sin-panel .lateral { opacity: 0; transform: translateX(28px); pointer-events: none; overflow: hidden; }
.mapa-card { display: flex; flex-direction: column; gap: 12px; min-height: 0; padding: 16px 18px 16px; }
.mapa-top { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.leyenda { position: absolute; left: 12px; bottom: 12px; z-index: 2; display: flex; gap: 12px; margin: 0; padding: 7px 12px; list-style: none; font-size: 11.5px; color: var(--ink-2); flex-wrap: wrap; border-radius: 12px; background: #fff; border: 1px solid var(--line); }
.leyenda li { display: flex; align-items: center; gap: 6px; }
.leyenda i { width: 10px; height: 10px; border-radius: 50%; }
.leyenda i.hueco { background: #fffaf0; border: 2px solid var(--ink); }

.acciones { display: flex; align-items: center; gap: 8px; }
.ic-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #fff;
  border: 1px solid var(--line-strong);
  color: var(--ink-2);
  transition: background 0.2s, color 0.2s, transform 0.35s var(--spring);
}
.ic-btn:hover { background: #faf9f6; color: var(--ink); }
.ic-btn:active { transform: scale(0.9); }
.ic-btn.activo { background: var(--ink); color: #fff; border-color: transparent; }
.resumen-corto { display: flex; gap: 8px; margin: 0 auto 0 0; padding: 0; list-style: none; }
.resumen-corto li { display: flex; align-items: baseline; gap: 6px; padding: 5px 12px; border-radius: 999px; background: var(--field); font-size: 13px; font-weight: 600; }
.resumen-corto span { color: var(--ink-3); font-size: 11px; font-weight: 400; }
.mapa-card.completa { padding: 20px 28px 22px; border-radius: 0; border: 0; background: #fff; }
.mapa-card.completa .lienzo { min-height: 0; }
.btn { padding: 7px 14px; font-size: 13px; }
.btn.ligero { color: var(--ink-3); }
.btn.activo { background: var(--violet); color: #fff; border-color: transparent; }

.lienzo {
  position: relative;
  flex: 1;
  min-height: 260px;
  overflow: hidden;
  border-radius: var(--r-md);
  background: var(--field);
}
.velo {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 12px;
  color: var(--ink-2);
  font-weight: 500;
  background: rgba(255, 255, 255, 0.78);
}
.spinner {
  width: 26px;
  height: 26px;
  border: 3px solid var(--line-strong);
  border-top-color: var(--violet);
  border-radius: 50%;
  animation: girar 0.8s linear infinite;
}
@keyframes girar { to { transform: rotate(360deg); } }
.error { position: absolute; left: 16px; right: 16px; bottom: 16px; padding: 12px 16px; border-radius: 14px; color: #8c281c; font-weight: 500; }
.tip {
  position: absolute;
  top: 0;
  left: 0;
  display: grid;
  gap: 1px;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 12px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 3;
}
.tip .mono { font-size: 11px; color: var(--ink-3); }

.narracion { min-height: 44px; margin: 0 6px; color: var(--ink-2); font-size: 13.5px; line-height: 1.5; }
.texto-enter-active { transition: opacity 0.25s var(--ease-out), transform 0.25s var(--ease-out); }
.texto-leave-active { transition: opacity 0.1s; }
.texto-enter-from { opacity: 0; transform: translateY(5px); }
.texto-leave-to { opacity: 0; }
.fundido-enter-active, .fundido-leave-active { transition: opacity 0.35s var(--ease-out); }
.fundido-enter-from, .fundido-leave-to { opacity: 0; }

.lateral { display: flex; flex-direction: column; gap: 18px; min-height: 0; overflow: auto; padding: 0 2px 2px 0; transition: opacity 0.35s var(--ease-out), transform 0.6s var(--ease-out); }
.lateral > * { flex: none; }
.metricas { display: flex; flex-direction: column; gap: 14px; }
.costo-valor { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.costo-valor strong { font-size: 40px; font-weight: 400; line-height: 1; letter-spacing: -0.03em; }
.datos { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 0; }
.datos div { padding: 8px 10px; border-radius: 12px; background: var(--field); min-width: 0; }
.datos dt { color: var(--ink-3); font-size: 10.5px; white-space: nowrap; }
.datos dd { margin: 2px 0 0; font-size: 15px; font-weight: 500; white-space: nowrap; }
.datos small { font-size: 10.5px; font-weight: 400; color: var(--ink-4); }
.nota { font-size: 11.5px; line-height: 1.45; }

@media (max-width: 1180px) {
  .cuerpo, .cuerpo.sin-panel { grid-template-columns: 1fr; row-gap: 18px; }
  .sin-panel .lateral { display: none; }
  .explorar { height: auto; }
  .lienzo { min-height: 420px; }
  .lateral { overflow: visible; }
}
</style>
