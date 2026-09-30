<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from 'vue'
import { api, ErrorApi } from '../core/api'
import { motor } from '../core/motor'
import type { Evidencia } from '../core/types'
import Dispersion from '../features/resultados/Dispersion.vue'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'

const CLAVE = 'astar'
const evidencia = shallowRef<Evidencia | null>(null)
const cargando = ref(true)
const error = ref('')
const copiado = ref(false)

const COMANDO = `npc-nav verificar --algoritmo ${CLAVE}`

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    evidencia.value = await api.evidencia(CLAVE)
  } catch (e) {
    error.value = e instanceof ErrorApi ? e.message : 'No se pudo cargar la evidencia.'
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

const fmt = (n: number) => n.toLocaleString('es-PE')
const fecha = computed(() =>
  evidencia.value
    ? new Date(evidencia.value.fecha_utc).toLocaleDateString('es-PE', { day: 'numeric', month: 'long', year: 'numeric' })
    : '',
)
const errorMaximo = computed(() => (evidencia.value?.error_maximo != null ? evidencia.value.error_maximo.toExponential(2) : '—'))
const optimos = computed(() => evidencia.value?.mapas.reduce((suma, m) => suma + m.optimos, 0) ?? 0)

async function copiar() {
  try {
    await navigator.clipboard.writeText(COMANDO)
    copiado.value = true
    setTimeout(() => (copiado.value = false), 1600)
  } catch {
    /* portapapeles no disponible */
  }
}
</script>

<template>
  <section class="resultados">
    <header class="rise" style="--i: 0">
      <h1 class="display pagina-titulo">Resultados <em>de la verificación</em></h1>
      <p class="pagina-sub">A* contra los 4 200 óptimos publicados del benchmark: la evidencia que respalda las cifras del informe.</p>
    </header>

    <div v-if="cargando" class="estado-carga card">
      <span class="spinner" />{{ motor.estado === 'listo' ? 'Cargando la evidencia…' : 'Despertando el motor…' }}
    </div>
    <div v-else-if="error" class="estado-carga card" role="alert">
      {{ error }} <button type="button" class="btn" @click="cargar">Reintentar</button>
    </div>

    <div v-else-if="evidencia" class="bento">
      <article class="kpi c-sky rise" style="--i: 1">
        <span class="eyebrow">Escenarios verificados</span>
        <strong class="display num"><AnimatedNumber :value="evidencia.total_casos" /></strong>
        <p>{{ evidencia.mapas.length }} mapas de Dragon Age: Origins</p>
      </article>
      <article class="kpi c-lime rise" style="--i: 2">
        <span class="eyebrow">Con el costo óptimo</span>
        <strong class="display num"><AnimatedNumber :value="optimos" /><small> / {{ fmt(evidencia.total_casos) }}</small></strong>
        <p>{{ evidencia.fallidos }} fallidos</p>
      </article>
      <article class="kpi c-lilac rise" style="--i: 3">
        <span class="eyebrow">Error máximo</span>
        <strong class="display num">{{ errorMaximo }}</strong>
        <p>tolerancia {{ evidencia.tolerancia_absoluta.toExponential(0) }}</p>
      </article>
      <article class="kpi c-cream rise" style="--i: 4">
        <span class="eyebrow">Verificado el</span>
        <strong class="display fecha">{{ fecha }}</strong>
        <p>Python {{ evidencia.entorno.python }}</p>
      </article>

      <article class="card grafico rise" style="--i: 5">
        <header class="card-title">
          <span class="badge-icon"><Icon name="resultados" :size="16" /></span>
          Esfuerzo según la distancia
          <span class="pill nombre">{{ evidencia.algoritmo }}</span>
        </header>
        <p class="muted leyenda-texto">Cada punto es un escenario: cuanto más lejos está el destino, más nodos expande el algoritmo.</p>
        <div class="area"><Dispersion :puntos="evidencia.puntos" /></div>
      </article>

      <article class="card metodo rise" style="--i: 6">
        <header class="card-title">
          <span class="badge-icon"><Icon name="chip" :size="16" /></span>
          Cómo se midió
        </header>
        <p class="texto">{{ evidencia.criterio }}</p>
        <p class="texto muted">{{ evidencia.medicion }}</p>
        <dl class="entorno">
          <div><dt>Sistema</dt><dd>{{ evidencia.entorno.plataforma }}</dd></div>
          <div><dt>Procesador</dt><dd>{{ evidencia.entorno.procesador }}</dd></div>
        </dl>
        <div class="comando">
          <code class="mono">{{ COMANDO }}</code>
          <button type="button" class="btn" :aria-label="'Copiar el comando'" @click="copiar">
            <Icon :name="copiado ? 'check' : 'codigo'" :size="14" />{{ copiado ? 'Copiado' : 'Copiar' }}
          </button>
        </div>
      </article>

      <article class="card tabla rise" style="--i: 7">
        <header class="card-title">
          <span class="badge-icon"><Icon name="comparar" :size="16" /></span>
          Detalle por mapa
        </header>
        <div class="desplazable">
          <table>
            <thead>
              <tr>
                <th>Mapa</th>
                <th>Vértices</th>
                <th>Aristas</th>
                <th>Regiones</th>
                <th>Escenarios</th>
                <th>Óptimos</th>
                <th>Error máx.</th>
                <th>Nodos (mediana)</th>
                <th>Tiempo (mediana)</th>
                <th>Tiempo (p95)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in evidencia.mapas" :key="m.mapa">
                <th scope="row">{{ m.mapa }}<small>{{ m.alto }}×{{ m.ancho }}</small></th>
                <td class="num">{{ fmt(m.vertices) }}</td>
                <td class="num">{{ fmt(m.aristas) }}</td>
                <td class="num">{{ fmt(m.componentes) }}</td>
                <td class="num">{{ fmt(m.escenarios) }}</td>
                <td class="num"><span class="pill pill-lime">{{ fmt(m.optimos) }}</span></td>
                <td class="num">{{ m.error_maximo != null ? m.error_maximo.toExponential(1) : '—' }}</td>
                <td class="num">{{ fmt(Math.round(m.nodos_expandidos_mediana)) }}</td>
                <td class="num">{{ m.tiempo_mediana_ms.toFixed(1) }} ms</td>
                <td class="num">{{ m.tiempo_p95_ms.toFixed(1) }} ms</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="pie muted">
          Los tiempos son descriptivos: se midieron con una sola ejecución por escenario en el equipo indicado y no
          demuestran rendimiento en tiempo real ni una ventaja frente a otro algoritmo.
        </p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.resultados { display: flex; flex-direction: column; gap: 18px; padding-bottom: 8px; }
.bento { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 16px; }

.c-sky { background: #dcebf7; }
.c-lilac { background: #e9e2fa; }
.c-lime { background: #e7f7ae; }
.c-cream { background: var(--cream); }
.kpi { grid-column: span 3; display: grid; gap: 2px; padding: 18px 22px; border-radius: var(--r-lg); }
.kpi .eyebrow { color: rgba(27, 25, 21, 0.55); }
.kpi strong { font-size: 42px; font-weight: 400; line-height: 1.1; letter-spacing: -0.03em; }
.kpi strong small { font-size: 18px; color: rgba(27, 25, 21, 0.5); letter-spacing: 0; }
.kpi .fecha { font-size: 27px; line-height: 1.4; }
.kpi p { font-size: 12.5px; color: rgba(27, 25, 21, 0.68); }

.grafico { grid-column: span 8; display: flex; flex-direction: column; gap: 6px; min-height: 420px; }
.nombre { margin-left: auto; font-family: var(--font-ui); font-size: 11.5px; }
.leyenda-texto { font-size: 12.5px; }
.area { flex: 1; min-height: 300px; margin-top: 6px; }

.metodo { grid-column: span 4; display: flex; flex-direction: column; gap: 10px; }
.texto { font-size: 12.8px; line-height: 1.6; color: var(--ink-2); }
.texto.muted { color: var(--ink-3); }
.entorno { display: grid; gap: 8px; margin: 2px 0 0; }
.entorno div { padding: 8px 12px; border-radius: 12px; background: var(--field); }
.entorno dt { color: var(--ink-3); font-size: 10.5px; }
.entorno dd { margin: 1px 0 0; font-size: 12.5px; font-weight: 500; overflow-wrap: anywhere; }
.comando { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: auto; padding: 8px 8px 8px 14px; border-radius: 14px; background: var(--ink); color: #f3f1ec; }
.comando code { font-size: 11.5px; overflow-wrap: anywhere; }
.comando .btn { padding: 6px 12px; font-size: 12px; color: var(--ink); flex: none; }

.tabla { grid-column: span 12; display: flex; flex-direction: column; gap: 12px; }
.desplazable { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12.8px; }
th, td { padding: 11px 14px; text-align: right; white-space: nowrap; }
thead th { color: var(--ink-3); font-size: 11px; font-weight: 500; border-bottom: 1px solid var(--line); }
tbody tr + tr > * { border-top: 1px solid var(--line); }
th:first-child, td:first-child { text-align: left; }
tbody th { font-weight: 600; }
tbody th small { display: block; color: var(--ink-3); font-size: 11px; font-weight: 400; }
.pie { font-size: 12px; line-height: 1.5; }

.estado-carga { display: flex; align-items: center; gap: 14px; padding: 22px 24px; color: var(--ink-2); font-weight: 500; }
.spinner { width: 22px; height: 22px; border: 3px solid var(--line-strong); border-top-color: var(--violet); border-radius: 50%; animation: girar 0.8s linear infinite; }
@keyframes girar { to { transform: rotate(360deg); } }

@media (max-width: 1180px) {
  .kpi { grid-column: span 6; }
  .grafico, .metodo { grid-column: span 12; }
}
</style>
