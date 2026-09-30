<script setup lang="ts">
import { motor } from '../core/motor'
import Icon from '../shared/Icon.vue'

const equipo = [
  { nombre: 'Victor Paredes Maza', codigo: 'u202416274', rol: 'Líder' },
  { nombre: 'Diana Carolina Li Gayoso', codigo: 'u202415749', rol: 'Integrante' },
  { nombre: 'Jahat Jassiel Trinidad León', codigo: 'u202412248', rol: 'Integrante' },
]
</script>

<template>
  <section class="acerca">
    <header class="rise" style="--i: 0">
      <p class="eyebrow">Acerca</p>
      <h1 class="display titulo">Un laboratorio para <em>ver pensar</em> a los algoritmos</h1>
      <p class="lead muted">
        Trabajo del curso 1ACC0184 Complejidad Algorítmica (UPC, 2026-20). Caso 10: <em>Juegos y AI (pathfinding)</em>.
        El motor en Python calcula todas las rutas; esta web solo dibuja lo que el motor le entrega.
      </p>
    </header>

    <h2 class="display seccion rise" style="--i: 1">Algoritmos</h2>
    <div class="algoritmos">
      <article v-for="(a, i) in motor.algoritmos" :key="a.clave" class="card algo rise" :style="{ '--i': 2 + i }">
        <header>
          <h3 class="display">{{ a.nombre }}</h3>
          <span class="pill" :class="a.garantiza_optimo ? 'pill-lime' : 'pill-gold'">{{ a.garantiza_optimo ? 'Óptimo' : 'No óptimo' }}</span>
        </header>
        <p class="tecnica muted">{{ a.tecnica }}</p>
        <dl>
          <div><dt>Complejidad</dt><dd class="mono">{{ a.complejidad }}</dd></div>
          <div><dt>Referencia</dt><dd>{{ a.referencia }}</dd></div>
        </dl>
      </article>
    </div>

    <div class="doble">
      <article class="card rise" style="--i: 6">
        <header class="card-title"><span class="badge-icon"><Icon name="explorar" :size="16" /></span>Datos</header>
        <p class="texto">
          Tres mapas de <em>Dragon Age: Origins</em> del benchmark de Moving AI Lab (Sturtevant, 2012), con 71&nbsp;174 celdas
          transitables y 4&nbsp;200 escenarios que traen su costo óptimo. Se usan bajo licencia Open Data Commons Attribution,
          con permiso de BioWare. Ocho direcciones, diagonales de costo √2 y sin cortar esquinas.
        </p>
      </article>

      <article class="card rise" style="--i: 7">
        <header class="card-title"><span class="badge-icon"><Icon name="chip" :size="16" /></span>Declaración de uso de IA</header>
        <p class="texto">
          El equipo usó Claude (Anthropic) como asistente de programación para el motor, la API y este dashboard.
          El código fue revisado por los integrantes, que deben poder explicarlo. <span class="muted">(Texto base: el equipo debe ajustarlo antes de la exposición.)</span>
        </p>
      </article>
    </div>

    <h2 class="display seccion rise" style="--i: 8">Equipo</h2>
    <div class="equipo">
      <article v-for="(p, i) in equipo" :key="p.codigo" class="card persona rise" :style="{ '--i': 9 + i }">
        <span class="avatar display">{{ p.nombre.split(' ').map((x) => x[0]).slice(0, 2).join('') }}</span>
        <div>
          <strong>{{ p.nombre }}</strong>
          <p class="muted num">{{ p.codigo }} · {{ p.rol }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.acerca { display: flex; flex-direction: column; gap: 16px; max-width: 1080px; padding-bottom: 12px; }
.titulo { margin-top: 6px; max-width: 18ch; font-size: clamp(36px, 4.6vw, 54px); }
.lead { max-width: 62ch; margin-top: 14px; font-size: 14.5px; line-height: 1.7; }
.seccion { margin: 14px 4px 0; font-size: 27px; }
.algoritmos { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.algo header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.algo h3 { font-size: 23px; }
.tecnica { margin: 4px 0 12px; font-size: 12.5px; }
dl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 0; }
dl div { padding: 9px 12px; border-radius: 12px; background: var(--field); }
dt { color: var(--ink-3); font-size: 10.5px; }
dd { margin: 1px 0 0; font-size: 13px; font-weight: 500; }
.doble { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 4px; }
.texto { margin-top: 12px; font-size: 13.5px; line-height: 1.7; color: var(--ink-2); }
.equipo { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.persona { display: flex; align-items: center; gap: 14px; padding: 16px 18px; }
.persona strong { font-weight: 600; font-size: 13.5px; }
.persona p { font-size: 12px; }
.avatar {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  flex: none;
  border-radius: 16px;
  background: var(--cream);
  font-size: 19px;
  color: var(--ink);
}
@media (max-width: 1000px) {
  .algoritmos, .doble, .equipo { grid-template-columns: 1fr; }
}
</style>
