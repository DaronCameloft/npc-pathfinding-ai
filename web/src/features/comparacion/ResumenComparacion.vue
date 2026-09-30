<script setup lang="ts">
import { computed } from 'vue'
import type { AlgoritmoInfo, Ejecucion } from '../../core/types'
import Icon from '../../shared/Icon.vue'

const props = defineProps<{
  filas: { info: AlgoritmoInfo; ejecucion: Ejecucion }[]
  optimoPublicado: number | null
}>()

interface Barra {
  clave: string
  nombre: string
  valor: number
  texto: string
  destacada: boolean
}

function barras(extraer: (e: Ejecucion) => number, formato: (n: number) => string): Barra[] {
  const max = Math.max(...props.filas.map((f) => extraer(f.ejecucion)), 1e-9)
  return props.filas.map((f) => ({
    clave: f.info.clave,
    nombre: f.info.nombre.replace(/ \(.*\)/, '').replace('Voraz primero el mejor', 'Voraz'),
    valor: (extraer(f.ejecucion) / max) * 100,
    texto: formato(extraer(f.ejecucion)),
    destacada: f.info.clave === 'astar',
  }))
}

const grupos = computed(() => [
  { titulo: 'Nodos expandidos', nota: 'menos es mejor', barras: barras((e) => e.metricas.nodos_expandidos, (n) => n.toLocaleString('es-PE')) },
  { titulo: 'Costo de la ruta', nota: 'menos es mejor', barras: barras((e) => e.costo ?? 0, (n) => n.toFixed(2)) },
  { titulo: 'Tiempo del motor', nota: 'ms · descriptivo', barras: barras((e) => e.metricas.tiempo_ms, (n) => `${n.toFixed(1)} ms`) },
])

const por = (clave: string) => props.filas.find((f) => f.info.clave === clave)?.ejecucion

/** Frase que resume la comparación, construida solo con datos medidos. */
const veredicto = computed(() => {
  const a = por('astar')
  const d = por('dijkstra')
  const v = por('voraz')
  const frases: string[] = []
  if (a && d && a.costo !== null && d.costo !== null) {
    const veces = d.metricas.nodos_expandidos / a.metricas.nodos_expandidos
    frases.push(
      Math.abs(a.costo - d.costo) < 1e-5
        ? `A* iguala el costo óptimo de Dijkstra (${a.costo.toFixed(2)}) expandiendo ${veces.toFixed(1)} veces menos celdas.`
        : `A* costó ${a.costo.toFixed(2)} y Dijkstra ${d.costo.toFixed(2)}.`,
    )
  }
  if (a && v && a.costo !== null && v.costo !== null && v.costo - a.costo > 1e-5) {
    frases.push(
      `Voraz explora solo ${v.metricas.nodos_expandidos.toLocaleString('es-PE')} celdas, pero su ruta cuesta ${(((v.costo - a.costo) / a.costo) * 100).toFixed(1)} % más.`,
    )
  }
  return frases
})
</script>

<template>
  <article class="card resumen">
    <header class="card-title">
      <span class="badge-icon"><Icon name="resultados" :size="16" /></span>
      Resumen
      <span v-if="optimoPublicado !== null" class="pill nombre">Óptimo publicado {{ optimoPublicado.toFixed(2) }}</span>
    </header>

    <section v-for="g in grupos" :key="g.titulo" class="grupo">
      <p class="grupo-titulo"><strong>{{ g.titulo }}</strong> <span class="muted">{{ g.nota }}</span></p>
      <ul>
        <li v-for="b in g.barras" :key="b.clave" :class="{ destacada: b.destacada }">
          <span class="et">{{ b.nombre }}</span>
          <span class="pista"><i :style="{ width: `${Math.max(2, b.valor)}%` }" /></span>
          <span class="val num">{{ b.texto }}</span>
        </li>
      </ul>
    </section>

    <div v-if="veredicto.length" class="veredicto">
      <Icon name="chispa" :size="16" />
      <p>{{ veredicto.join(' ') }}</p>
    </div>
  </article>
</template>

<style scoped>
.resumen { display: flex; flex-direction: column; gap: 14px; }
.nombre { margin-left: auto; font-family: var(--font-ui); font-size: 11.5px; }
.grupo-titulo { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; font-size: 12.5px; }
.grupo-titulo span { font-size: 11px; }
ul { display: grid; gap: 5px; margin: 0; padding: 0; list-style: none; }
li { display: grid; grid-template-columns: 62px 1fr 64px; align-items: center; gap: 10px; font-size: 12px; color: var(--ink-2); }
.val { text-align: right; font-size: 11.5px; }
.pista { height: 8px; border-radius: 999px; background: var(--field); overflow: hidden; }
.pista i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--ink-4);
  animation: crecer 1s var(--ease-out) both;
  transform-origin: left;
}
li.destacada .pista i { background: var(--gold); }
li.destacada { color: var(--ink); font-weight: 600; }
@keyframes crecer { from { transform: scaleX(0); } }
.veredicto {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--cream);
  color: #5b4310;
  font-size: 13px;
  line-height: 1.5;
}
.veredicto svg { flex: none; margin-top: 2px; }
</style>
