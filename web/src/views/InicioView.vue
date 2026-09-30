<script setup lang="ts">
import { computed } from 'vue'
import { motor } from '../core/motor'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'

const vertices = computed(() => motor.mapas.reduce((suma, m) => suma + m.vertices, 0))
const escenarios = computed(() => motor.mapas.reduce((suma, m) => suma + m.escenarios, 0))

const pasos = [
  { n: '01', titulo: 'Elige un mapa y un caso', texto: 'Tres mapas reales de Dragon Age: Origins y 4 200 consultas con costo óptimo publicado.', ruta: '/explorar', icono: 'explorar' },
  { n: '02', titulo: 'Mira al algoritmo pensar', texto: 'El pseudocódigo se ilumina línea a línea mientras el mapa se explora celda por celda.', ruta: '/explorar', icono: 'codigo' },
  { n: '03', titulo: 'Compara y decide', texto: 'BFS, Dijkstra, voraz y A* sobre la misma consulta: costo, nodos expandidos y tiempo.', ruta: '/comparar', icono: 'comparar' },
]
</script>

<template>
  <section class="inicio">
    <article class="hero rise" style="--i: 0">
      <div class="hero-texto">
        <p class="eyebrow">ArcadiaLabs · Complejidad Algorítmica</p>
        <h1 class="display">Encuentra el camino,<br /><em>entiende el algoritmo.</em></h1>
        <p class="lead">
          Un laboratorio visual para NPCs que navegan mapas reales: compara búsquedas, sigue cada decisión
          y comprueba por qué A* es el equilibrio entre costo y esfuerzo.
        </p>
        <div class="cta">
          <RouterLink to="/explorar" class="btn btn-dark">Explorar el caso 375 <Icon name="flecha" :size="16" /></RouterLink>
          <RouterLink to="/comparar" class="btn">Comparar algoritmos</RouterLink>
        </div>
      </div>

      <svg class="hilo" viewBox="0 0 420 300" fill="none" aria-hidden="true">
        <defs>
          <pattern id="malla" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="1.5" cy="1.5" r="1.1" fill="rgba(27,25,21,.18)" />
          </pattern>
        </defs>
        <rect width="420" height="300" fill="url(#malla)" />
        <path class="muro" d="M70 245h100M205 245h125v-75M100 92h85M40 58h34M232 150v40M330 128h50V92M120 215h40" />
        <path class="camino" d="M40 250V205L85 160H150L200 110H270V70L320 40H380" />
        <circle cx="40" cy="250" r="9" fill="#2e8b57" stroke="#fffaf0" stroke-width="3" />
        <circle class="meta" cx="380" cy="40" r="9" fill="#fffaf0" stroke="#1d1a16" stroke-width="3" />
      </svg>
    </article>

    <div class="cifras">
      <article class="card cifra rise" style="--i: 1">
        <span class="eyebrow">Mapas</span>
        <strong class="display num"><AnimatedNumber :value="motor.mapas.length" /></strong>
        <p class="muted"><AnimatedNumber :value="vertices" /> vértices en total</p>
      </article>
      <article class="card cifra rise" style="--i: 2">
        <span class="eyebrow">Escenarios</span>
        <strong class="display num"><AnimatedNumber :value="escenarios" /></strong>
        <p class="muted">con costo óptimo publicado</p>
      </article>
      <article class="card cifra rise" style="--i: 3">
        <span class="eyebrow">Algoritmos</span>
        <strong class="display num"><AnimatedNumber :value="motor.algoritmos.length" /></strong>
        <p class="muted">BFS · Dijkstra · Voraz · A*</p>
      </article>
      <article class="card cifra destacada rise" style="--i: 4">
        <span class="eyebrow">A* verificado</span>
        <strong class="display num">4 200<small> / 4 200</small></strong>
        <p class="muted">rutas con el costo óptimo publicado</p>
      </article>
    </div>

    <h2 class="display seccion rise" style="--i: 5">Cómo se usa</h2>
    <div class="pasos">
      <RouterLink v-for="(p, i) in pasos" :key="p.n" :to="p.ruta" class="card paso rise" :style="{ '--i': 6 + i }">
        <span class="paso-n display">{{ p.n }}</span>
        <span class="badge-icon"><Icon :name="p.icono" :size="17" /></span>
        <h3 class="display">{{ p.titulo }}</h3>
        <p class="muted">{{ p.texto }}</p>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.inicio { display: flex; flex-direction: column; gap: 18px; padding-bottom: 8px; }
.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  align-items: center;
  gap: 24px;
  min-height: 340px;
  padding: 44px 48px;
  overflow: hidden;
  border-radius: var(--r-xl);
  background: var(--cream);
}
.hero h1 { margin-top: 12px; font-size: clamp(38px, 5vw, 62px); }
.lead { max-width: 46ch; margin-top: 18px; color: #5b4c26; font-size: 15px; line-height: 1.65; }
.cta { display: flex; gap: 10px; margin-top: 26px; flex-wrap: wrap; }
.hilo { width: 100%; height: auto; max-height: 290px; }
.muro { stroke: rgba(27, 25, 21, 0.22); stroke-width: 6; stroke-linecap: round; stroke-linejoin: round; }
.camino {
  stroke-linejoin: round;
  stroke: #c0392b;
  stroke-width: 5;
  stroke-linecap: round;
  stroke-dasharray: 700;
  stroke-dashoffset: 700;
    animation: trazar 2.6s 0.5s var(--ease-in-out) forwards;
}
.meta { transform-origin: 380px 40px; animation: latir 2.4s 3s var(--ease-in-out) infinite; }
@keyframes trazar { to { stroke-dashoffset: 0; } }
@keyframes latir { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.25); } }

.cifras { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.cifra { display: grid; gap: 2px; }
.cifra strong { font-size: 46px; font-weight: 400; line-height: 1.1; letter-spacing: -0.03em; }
.cifra strong small { font-size: 20px; color: var(--ink-3); letter-spacing: 0; }
.cifra p { font-size: 12.5px; }
.cifra.destacada { background: #ebf9b8; border-color: transparent; }
.cifra.destacada .muted { color: #4a5b12; }

.seccion { margin: 10px 4px 0; font-size: 28px; }
.pasos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.paso {
  position: relative;
  display: grid;
  gap: 8px;
  align-content: start;
  transition: transform 0.5s var(--spring), border-color 0.3s;
}
.paso:hover { transform: translateY(-4px); border-color: var(--line-strong); }
.paso-n { position: absolute; top: 14px; right: 20px; font-size: 40px; font-style: italic; font-weight: 300; color: rgba(27, 25, 21, 0.12); }
.paso h3 { font-size: 21px; }
.paso p { font-size: 13px; line-height: 1.55; }

@media (max-width: 1100px) {
  .hero { grid-template-columns: 1fr; padding: 32px; }
  .hilo { display: none; }
  .cifras { grid-template-columns: 1fr 1fr; }
  .pasos { grid-template-columns: 1fr; }
}
</style>
