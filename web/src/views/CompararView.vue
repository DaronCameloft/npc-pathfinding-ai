<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { api, ErrorApi } from '../core/api'
import { motor } from '../core/motor'
import type { Ejecucion, Escenario, MapaDetalle } from '../core/types'
import PanelAlgoritmo, { type Resaltado, type Veredicto } from '../features/comparacion/PanelAlgoritmo.vue'
import ResumenComparacion from '../features/comparacion/ResumenComparacion.vue'
import type { Vista } from '../features/mapa/MapCanvas.vue'
import PlaybackDock from '../features/reproduccion/PlaybackDock.vue'
import { usePlayback, velocidadSugerida } from '../features/reproduccion/usePlayback'
import { alternarResaltado, ui } from '../core/ui'
import CasoSelector from '../shared/CasoSelector.vue'
import Icon from '../shared/Icon.vue'
import Segmented from '../shared/Segmented.vue'

const mapaClave = ref('den011d')
const caso = ref(375)
const escenario = ref<Escenario | null>(null)
const detalle = shallowRef<MapaDetalle | null>(null)
const ejecuciones = shallowRef<Ejecucion[]>([])
const vista = ref<Vista | null>(null)
const cargando = ref(true)
const zonaCompleta = ref<HTMLElement | null>(null)
const pantallaCompleta = ref(false)
const error = ref('')

const cacheMapas = new Map<string, MapaDetalle>()
let ticket = 0

const total = computed(() => Math.max(0, ...ejecuciones.value.map((e) => e.traza.length)))
const pb = usePlayback(total)

const opcionesMapa = computed(() =>
  motor.mapas.map((m) => ({ valor: m.nombre, etiqueta: m.nombre, detalle: `${(m.vertices / 1000).toFixed(1)}k` })),
)
const totalCasos = computed(() => motor.mapas.find((m) => m.nombre === mapaClave.value)?.escenarios ?? 0)

const filas = computed(() =>
  ejecuciones.value.flatMap((ejecucion) => {
    const info = motor.algoritmos.find((a) => a.clave === ejecucion.algoritmo)
    return info ? [{ info, ejecucion }] : []
  }),
)
const costoMinimo = computed(() => {
  const costos = ejecuciones.value.map((e) => e.costo).filter((c): c is number => c !== null)
  return costos.length ? Math.min(...costos) : null
})

/** Marca el mejor y el peor valor de una métrica (menor es mejor); si todos empatan, ninguno. */
function clasificar(valores: number[]): Veredicto[] {
  const mejor = Math.min(...valores)
  const peor = Math.max(...valores)
  const tol = 1e-5 * Math.max(1, Math.abs(mejor))
  if (peor - mejor <= tol) return valores.map(() => null)
  return valores.map((v) => (v - mejor <= tol ? 'mejor' : peor - v <= tol ? 'peor' : null))
}

const resaltados = computed<Record<string, Resaltado> | null>(() => {
  if (!ui.resaltarResultados || !filas.value.length) return null
  const f = filas.value
  const expandidos = clasificar(f.map((x) => x.ejecucion.metricas.nodos_expandidos))
  const costo = clasificar(f.map((x) => x.ejecucion.costo ?? Number.POSITIVE_INFINITY))
  return Object.fromEntries(f.map((x, i) => [x.info.clave, { expandidos: expandidos[i], costo: costo[i] }]))
})

async function ejecutar() {
  const mio = ++ticket
  cargando.value = true
  error.value = ''
  try {
    if (!cacheMapas.has(mapaClave.value)) cacheMapas.set(mapaClave.value, await api.mapa(mapaClave.value))
    const [pagina, resultados] = await Promise.all([
      api.escenarios(mapaClave.value, caso.value, 1),
      api.comparar({ mapa: mapaClave.value, caso: caso.value, traza: true }),
    ])
    if (mio !== ticket) return
    detalle.value = cacheMapas.get(mapaClave.value)!
    escenario.value = pagina.escenarios[0] ?? null
    vista.value = null
    ejecuciones.value = resultados
    await nextTick()
    pb.velocidad.value = velocidadSugerida(total.value)
    pb.reproducir()
  } catch (e) {
    if (mio === ticket) error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

watch([mapaClave, caso], ([nuevoMapa], [viejoMapa]) => {
  if (nuevoMapa !== viejoMapa) {
    caso.value = Math.floor((motor.mapas.find((m) => m.nombre === nuevoMapa)?.escenarios ?? 2) / 2)
  }
  void ejecutar()
})

function alternarPantallaCompleta() {
  if (document.fullscreenElement) void document.exitFullscreen()
  else void zonaCompleta.value?.requestFullscreen?.()
}
const alCambiarPantalla = () => {
  pantallaCompleta.value = document.fullscreenElement === zonaCompleta.value
}

function alTeclado(e: KeyboardEvent) {
  if ((e.target as HTMLElement).closest('input, select, textarea')) return
  if (!e.ctrlKey && !e.metaKey && !e.altKey && (e.key === 'f' || e.key === 'F')) { alternarPantallaCompleta(); return }
  if (e.code === 'Space') { e.preventDefault(); pb.alternar() }
  else if (e.key === 'ArrowRight') pb.paso(e.shiftKey ? 50 : 1)
  else if (e.key === 'ArrowLeft') pb.paso(e.shiftKey ? -50 : -1)
  else if (e.key === 'Home') pb.reiniciar()
  else if (e.key === 'End') pb.alFinal()
}
onMounted(() => {
  window.addEventListener('keydown', alTeclado)
  document.addEventListener('fullscreenchange', alCambiarPantalla)
  void ejecutar()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', alTeclado)
  document.removeEventListener('fullscreenchange', alCambiarPantalla)
  if (document.fullscreenElement) void document.exitFullscreen()
})
</script>

<template>
  <section class="comparar">
    <header class="cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo titulo">Comparar <em>cuatro caminos</em></h1>
        <p class="pagina-sub">La misma consulta, cuatro algoritmos: costo, celdas y tiempo.</p>
      </div>
      <div class="selectores">
        <CasoSelector v-model="caso" :total="totalCasos" />
        <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
        <button type="button" class="btn colorear" :class="{ activo: ui.resaltarResultados }" :aria-pressed="ui.resaltarResultados" title="Colorea el mejor (verde) y el peor (rojo) de expandidos y costo al terminar" @click="alternarResaltado">
          <span class="muestra" /> Resaltar
        </button>
        <button type="button" class="ic-btn" aria-label="Ver los cuatro algoritmos en pantalla completa" title="Ver los cuatro en pantalla completa (F)" @click="alternarPantallaCompleta">
          <Icon name="pantalla" :size="17" />
        </button>
      </div>
    </header>

    <div class="cuerpo">
      <div ref="zonaCompleta" class="izquierda" :class="{ completa: pantallaCompleta }">
        <div v-if="pantallaCompleta" class="barra-completa">
          <CasoSelector v-model="caso" :total="totalCasos" />
          <Segmented v-model="mapaClave" :opciones="opcionesMapa" etiqueta="Mapa" />
          <span v-if="escenario" class="pill">Óptimo publicado {{ escenario.optimo.toFixed(2) }}</span>
          <button type="button" class="btn colorear" :class="{ activo: ui.resaltarResultados }" :aria-pressed="ui.resaltarResultados" @click="alternarResaltado">
            <span class="muestra" /> Resaltar
          </button>
          <button type="button" class="ic-btn salir" aria-label="Salir de pantalla completa" title="Salir de pantalla completa (F)" @click="alternarPantallaCompleta">
            <Icon name="pantalla_salir" :size="17" />
          </button>
        </div>
        <div class="rejilla">
          <PanelAlgoritmo
            v-for="(f, i) in filas"
            :key="f.info.clave + mapaClave + caso"
            class="rise"
            :style="{ '--i': i + 1 }"
            :info="f.info"
            :ejecucion="f.ejecucion"
            :mapa="detalle!"
            :indice="pb.indice.value"
            :inicio="escenario!.inicio"
            :destino="escenario!.destino"
            :vista="vista"
            :costo-minimo="costoMinimo"
            :resaltado="resaltados?.[f.info.clave] ?? null"
            :zoom="i === 0"
            @update:vista="vista = $event"
          />
        </div>

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
      </div>

      <aside class="lateral">
        <ResumenComparacion
          v-if="filas.length"
          class="rise"
          style="--i: 5"
          :filas="filas"
          :optimo-publicado="escenario?.optimo ?? null"
        />
        <article class="card nota rise" style="--i: 6">
          <p>
            Los cuatro algoritmos reciben el mismo mapa, el mismo inicio y el mismo destino. La animación avanza por
            <strong>pasos de la traza</strong>: un algoritmo que termina antes en la línea de tiempo explora menos celdas.
          </p>
        </article>
      </aside>
    </div>

    <Transition name="fundido">
      <div v-if="cargando" class="velo"><span class="spinner" />{{ motor.estado === 'listo' ? 'Comparando los cuatro algoritmos…' : 'Despertando el motor…' }}</div>
    </Transition>
    <Transition name="fundido">
      <div v-if="error" class="error glass" role="alert">{{ error }}</div>
    </Transition>
  </section>
</template>

<style scoped>
.comparar { position: relative; display: flex; flex-direction: column; gap: 14px; height: 100%; min-height: 680px; }
.cabecera { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.titulo { margin-top: 2px; }
.selectores { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.ic-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: none;
  border-radius: 50%;
  background: #fff;
  border: 1px solid var(--line-strong);
  color: var(--ink-2);
  transition: background 0.2s, color 0.2s, transform 0.35s var(--spring);
}
.ic-btn:hover { background: #faf9f6; color: var(--ink); }
.ic-btn:active { transform: scale(0.9); }
.colorear { padding: 7px 14px; font-size: 13px; }
.colorear .muestra { width: 10px; height: 10px; border-radius: 50%; background: var(--ink-4); transition: background 0.3s; }
.colorear.activo .muestra { background: #6cbf3a; box-shadow: 9px 0 0 -1px #d9584a; margin-right: 9px; }
.barra-completa { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.barra-completa .salir { margin-left: auto; }
.izquierda.completa { padding: 20px 28px 22px; background: #fff; overflow: hidden; }
.izquierda.completa .rejilla { grid-template-rows: repeat(2, minmax(0, 1fr)); }
.izquierda.completa :deep(.lienzo) { min-height: 0; }

.cuerpo { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 18px; flex: 1; min-height: 0; }
.izquierda { display: flex; flex-direction: column; gap: 14px; min-height: 0; overflow: auto; }
.izquierda > :last-child { position: sticky; bottom: 0; flex: none; }
.rejilla { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(2, minmax(236px, 1fr)); gap: 14px; flex: 1; min-height: 0; }
.lateral { display: flex; flex-direction: column; gap: 14px; min-height: 0; overflow: auto; padding: 0 2px 2px 0; }
.lateral > * { flex: none; }
.nota { font-size: 12.5px; line-height: 1.55; color: var(--ink-2); }

.velo {
  position: absolute;
  inset: -8px;
  z-index: 5;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 12px;
  color: var(--ink-2);
  font-weight: 500;
  border-radius: 24px;
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
.error { position: absolute; left: 16px; right: 16px; bottom: 16px; z-index: 6; padding: 12px 16px; border-radius: 14px; color: #8c281c; font-weight: 500; }
.fundido-enter-active, .fundido-leave-active { transition: opacity 0.35s var(--ease-out); }
.fundido-enter-from, .fundido-leave-to { opacity: 0; }

@media (max-width: 1240px) {
  .cuerpo { grid-template-columns: 1fr; }
  .comparar { height: auto; }
  .rejilla { grid-template-rows: none; grid-auto-rows: 300px; }
  .lateral { overflow: visible; }
}
@media (max-width: 760px) {
  .rejilla { grid-template-columns: 1fr; }
}
</style>
