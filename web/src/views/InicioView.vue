<script setup lang="ts">
import { computed } from 'vue'
import { motor } from '../core/motor'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import HeroArte from '../features/inicio/HeroArte.vue'
import NpcDemo from '../features/inicio/NpcDemo.vue'
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
    <header class="rise" style="--i: 0">
      <h1 class="display pagina-titulo">Bienvenido a <em>ArcadiaLabs</em></h1>
      <p class="pagina-sub">Un laboratorio visual de búsqueda de rutas para NPCs, sobre mapas reales de Dragon Age: Origins.</p>
    </header>

    <div class="bento">
      <article class="hero rise" style="--i: 1">
        <HeroArte />
        <div class="hero-top">
          <span class="chip-icono"><Icon name="explorar" :size="15" /></span>
          <span class="chip-icono"><Icon name="metricas" :size="15" /></span>
          <span class="hero-etiqueta">Búsqueda · en vivo</span>
        </div>
        <div class="hero-cuerpo">
          <h2 class="display">Encuentra el camino, <em>entiende el algoritmo.</em></h2>
          <p class="lead">Compara búsquedas, sigue cada decisión y comprueba por qué A* equilibra costo y esfuerzo.</p>
          <div class="cta">
            <RouterLink to="/explorar" class="btn btn-dark">Explorar el caso 375 <Icon name="flecha" :size="16" /></RouterLink>
            <RouterLink to="/comparar" class="btn">Comparar</RouterLink>
          </div>
        </div>
      </article>

      <article class="card ilustracion rise" style="--i: 2">
        <header class="card-title">
          <span class="badge-icon"><Icon name="chip" :size="16" /></span>
          El NPC que recalcula
          <span class="pill pill-lime">A*</span>
        </header>
        <NpcDemo />
      </article>

      <article class="cifra c-sky rise" style="--i: 3">
        <span class="eyebrow">Mapas</span>
        <strong class="display num"><AnimatedNumber :value="motor.mapas.length" /></strong>
        <p><AnimatedNumber :value="vertices" /> vértices en total</p>
      </article>
      <article class="cifra c-lilac rise" style="--i: 4">
        <span class="eyebrow">Escenarios</span>
        <strong class="display num"><AnimatedNumber :value="escenarios" /></strong>
        <p>con costo óptimo publicado</p>
      </article>
      <article class="cifra c-cream rise" style="--i: 5">
        <span class="eyebrow">Algoritmos</span>
        <strong class="display num"><AnimatedNumber :value="motor.algoritmos.length" /></strong>
        <p>BFS · Dijkstra · Voraz · A*</p>
      </article>
      <article class="cifra c-lime rise" style="--i: 6">
        <span class="eyebrow">A* verificado</span>
        <strong class="display num">4 200<small> / 4 200</small></strong>
        <p>rutas con el costo óptimo publicado</p>
      </article>

      <RouterLink v-for="(p, i) in pasos" :key="p.n" :to="p.ruta" class="card paso rise" :style="{ '--i': 7 + i }">
        <span class="paso-n display">{{ p.n }}</span>
        <span class="badge-icon"><Icon :name="p.icono" :size="17" /></span>
        <h3 class="display">{{ p.titulo }}</h3>
        <p class="muted">{{ p.texto }}</p>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.inicio { display: flex; flex-direction: column; gap: 22px; padding-bottom: 8px; }
.bento { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 16px; }

.c-cream { background: var(--cream); }
.c-sky { background: #dcebf7; }
.c-lilac { background: #e9e2fa; }
.c-lime { background: #e7f7ae; }

.hero {
  position: relative;
  grid-column: span 5;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 24px;
  min-height: 360px;
  padding: 22px 26px 26px;
  overflow: hidden;
  border-radius: var(--r-lg);
  isolation: isolate;
}
.hero > :not(:first-child) { position: relative; z-index: 1; }
.hero-top { display: flex; align-items: center; gap: 8px; }
.chip-icono {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--ink);
  color: #fff;
}
.hero-etiqueta { margin-left: 4px; font-size: 12.5px; font-weight: 500; color: var(--ink-2); }
.hero h2 { font-size: clamp(32px, 3.4vw, 46px); }
.lead { max-width: 40ch; margin-top: 10px; color: #5b4c26; font-size: 13.5px; line-height: 1.6; }
.cta { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }

.ilustracion { grid-column: span 7; display: flex; flex-direction: column; gap: 12px; }
.ilustracion .pill { margin-left: auto; }

.cifra {
  grid-column: span 3;
  display: grid;
  gap: 2px;
  padding: 18px 22px;
  border-radius: var(--r-lg);
}
.cifra .eyebrow { color: rgba(27, 25, 21, 0.55); }
.cifra strong { font-size: 44px; font-weight: 400; line-height: 1.1; letter-spacing: -0.03em; }
.cifra strong small { font-size: 19px; color: rgba(27, 25, 21, 0.5); letter-spacing: 0; }
.cifra p { font-size: 12.5px; color: rgba(27, 25, 21, 0.68); }

.paso {
  grid-column: span 4;
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

@media (max-width: 1180px) {
  .hero, .ilustracion { grid-column: span 12; }
  .cifra { grid-column: span 6; }
  .paso { grid-column: span 12; }
}
</style>
