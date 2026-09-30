<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { motor, reintentarConexion } from '../core/motor'
import BrandMark from './BrandMark.vue'
import Icon from './Icon.vue'

interface Enlace {
  ruta: string
  etiqueta: string
  icono: string
  pronto?: boolean
}

const laboratorio: Enlace[] = [
  { ruta: '/', etiqueta: 'Inicio', icono: 'inicio' },
  { ruta: '/explorar', etiqueta: 'Explorar', icono: 'explorar' },
  { ruta: '/comparar', etiqueta: 'Comparar', icono: 'comparar' },
  { ruta: '/resultados', etiqueta: 'Resultados', icono: 'resultados' },
]
const mas: Enlace[] = [
  { ruta: '/acerca', etiqueta: 'Acerca', icono: 'acerca' },
  { ruta: '/simulacion', etiqueta: 'Simulación', icono: 'simulacion', pronto: true },
]

const route = useRoute()
const navegacion = ref<HTMLElement | null>(null)
const pildora = ref({ y: 0, alto: 0, visible: false })

async function moverPildora() {
  await nextTick()
  const activo = navegacion.value?.querySelector<HTMLElement>('a[aria-current="page"]')
  if (!activo) {
    pildora.value.visible = false
    return
  }
  pildora.value = { y: activo.offsetTop, alto: activo.offsetHeight, visible: true }
}

onMounted(moverPildora)
watch(() => route.path, moverPildora)

const texto = computed(() => {
  switch (motor.estado) {
    case 'listo': return { titulo: 'Motor en línea', detalle: `v${motor.version} · ${motor.latenciaMs} ms` }
    case 'despertando': return { titulo: 'Despertando el motor…', detalle: 'El servidor gratuito tarda unos segundos' }
    case 'sin_conexion': return { titulo: 'Sin conexión', detalle: 'Toca para reintentar' }
    default: return { titulo: 'Conectando…', detalle: '' }
  }
})
</script>

<template>
  <aside class="sidebar frost">
    <RouterLink to="/" class="marca" aria-label="ArcadiaLabs">
      <BrandMark />
      <strong class="display marca-texto">Arcadia<em>Labs</em></strong>
    </RouterLink>

    <nav ref="navegacion" class="nav" aria-label="Principal">
      <span class="pildora" :class="{ visible: pildora.visible }" :style="{ transform: `translateY(${pildora.y}px)`, height: `${pildora.alto}px` }" />
      <p class="grupo eyebrow">Laboratorio</p>
      <RouterLink v-for="e in laboratorio" :key="e.ruta" :to="e.ruta" class="enlace">
        <Icon :name="e.icono" /> <span>{{ e.etiqueta }}</span>
      </RouterLink>
      <p class="grupo eyebrow">Más</p>
      <RouterLink v-for="e in mas" :key="e.ruta" :to="e.ruta" class="enlace" :class="{ pronto: e.pronto }" :tabindex="e.pronto ? -1 : 0">
        <Icon :name="e.icono" /> <span>{{ e.etiqueta }}</span>
        <em v-if="e.pronto" class="pill pill-gold">Hito 2</em>
      </RouterLink>
    </nav>

    <button class="estado" :class="motor.estado" type="button" @click="motor.estado === 'sin_conexion' && reintentarConexion()">
      <span class="punto" />
      <span class="estado-texto">
        <strong>{{ texto.titulo }}</strong>
        <small>{{ texto.detalle }}</small>
      </span>
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 26px;
  width: 244px;
  flex: none;
  padding: 22px 14px 14px;
  border-radius: var(--r-xl);
}
.marca { display: flex; align-items: center; gap: 11px; padding: 0 8px; }
.marca-texto { font-size: 25px; font-weight: 500; letter-spacing: -0.03em; }
.marca-texto em { font-weight: 400; color: var(--ink-2); }

.nav { position: relative; display: flex; flex-direction: column; gap: 2px; }
.grupo { margin: 16px 12px 6px; font-size: 10.5px; }
.grupo:first-of-type { margin-top: 0; }
.enlace {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 14px;
  color: var(--ink-2);
  font-weight: 500;
  transition: color 0.25s, transform 0.4s var(--spring);
}
.enlace:hover { color: var(--ink); transform: translateX(3px); }
.enlace[aria-current='page'] { color: var(--ink); }
.enlace em { margin-left: auto; font-style: normal; font-size: 10.5px; padding: 1px 8px; }
.enlace.pronto { opacity: 0.55; pointer-events: none; }

.pildora {
  position: absolute;
  z-index: 0;
  inset: 0 0 auto 0;
  border-radius: 14px;
  background: #fff;
  opacity: 0;
  transition: transform 0.6s var(--spring), height 0.4s var(--ease-out), opacity 0.3s;
}
.pildora.visible { opacity: 1; }

.estado {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.95);
  text-align: left;
  transition: transform 0.4s var(--spring);
}
.estado:active { transform: scale(0.97); }
.estado-texto { display: grid; line-height: 1.25; }
.estado-texto strong { font-size: 12.5px; font-weight: 600; }
.estado-texto small { color: var(--ink-3); font-size: 11px; }
.punto { width: 9px; height: 9px; flex: none; border-radius: 50%; background: var(--ink-4); }
.listo .punto { background: #37b866; }
.despertando .punto, .conectando .punto { background: var(--gold); animation: latido 1.3s ease-in-out infinite; }
.sin_conexion .punto { background: var(--danger); }
@keyframes latido {
  0%, 100% { box-shadow: 0 0 0 0 rgba(227, 165, 45, 0.5); }
  50% { box-shadow: 0 0 0 7px rgba(227, 165, 45, 0); }
}

@media (max-width: 900px) {
  .sidebar { width: 72px; padding-inline: 10px; }
  .marca-texto, .enlace span, .enlace em, .grupo, .estado-texto { display: none; }
  .enlace { justify-content: center; padding-inline: 0; }
  .estado { justify-content: center; }
}
</style>
