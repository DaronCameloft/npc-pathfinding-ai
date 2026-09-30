<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { motor, reintentarConexion } from '../core/motor'
import { alternarSidebar, ui } from '../core/ui'
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

function alTeclado(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
    e.preventDefault()
    alternarSidebar()
  }
}

onMounted(() => {
  moverPildora()
  window.addEventListener('keydown', alTeclado)
})
onBeforeUnmount(() => window.removeEventListener('keydown', alTeclado))
watch(() => route.path, moverPildora)
watch(() => ui.compacta, () => {
  moverPildora()
  setTimeout(moverPildora, 560)
})

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
  <aside class="sidebar frost" :class="{ compacta: ui.compacta }">
    <div class="cabecera">
      <RouterLink to="/" class="marca" aria-label="ArcadiaLabs" title="ArcadiaLabs">
        <BrandMark />
        <strong class="display marca-texto">Arcadia<em>Labs</em></strong>
      </RouterLink>
      <button
        type="button"
        class="alternar"
        :aria-label="ui.compacta ? 'Expandir la barra lateral' : 'Compactar la barra lateral'"
        :aria-pressed="ui.compacta"
        :title="ui.compacta ? 'Expandir (Ctrl+B)' : 'Compactar (Ctrl+B)'"
        @click="alternarSidebar"
      >
        <Icon name="panel" :size="17" />
      </button>
    </div>

    <nav ref="navegacion" class="nav" aria-label="Principal">
      <span class="pildora" :class="{ visible: pildora.visible }" :style="{ transform: `translateY(${pildora.y}px)`, height: `${pildora.alto}px` }" />
      <p class="grupo eyebrow"><span>Laboratorio</span></p>
      <RouterLink v-for="e in laboratorio" :key="e.ruta" :to="e.ruta" class="enlace" :title="ui.compacta ? e.etiqueta : undefined">
        <Icon :name="e.icono" /> <span class="etiqueta">{{ e.etiqueta }}</span>
      </RouterLink>
      <p class="grupo eyebrow"><span>Más</span></p>
      <RouterLink
        v-for="e in mas"
        :key="e.ruta"
        :to="e.ruta"
        class="enlace"
        :class="{ pronto: e.pronto }"
        :tabindex="e.pronto ? -1 : 0"
        :title="ui.compacta ? e.etiqueta : undefined"
      >
        <Icon :name="e.icono" /> <span class="etiqueta">{{ e.etiqueta }}</span>
        <em v-if="e.pronto" class="pill pill-gold">Hito 2</em>
      </RouterLink>
    </nav>

    <button
      class="estado"
      :class="motor.estado"
      type="button"
      :title="ui.compacta ? `${texto.titulo} ${texto.detalle}` : undefined"
      @click="motor.estado === 'sin_conexion' && reintentarConexion()"
    >
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
  gap: 22px;
  width: 244px;
  flex: none;
  padding: 22px 14px 14px;
  overflow: hidden;
  border-radius: var(--r-xl);
  transition: width 0.55s var(--ease-out);
}
.sidebar.compacta { width: 76px; }

.cabecera { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 0 4px 0 8px; transition: gap 0.4s var(--ease-out); }
.marca { display: flex; align-items: center; gap: 11px; min-width: 0; }
.marca-texto { font-size: 25px; font-weight: 500; letter-spacing: -0.03em; white-space: nowrap; transition: opacity 0.25s, max-width 0.5s var(--ease-out); max-width: 140px; }
.marca-texto em { font-weight: 400; color: var(--ink-2); }
.alternar {
  display: grid;
  place-items: center;
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  color: var(--ink-3);
  transition: background 0.2s, color 0.2s, transform 0.45s var(--spring);
}
.alternar:hover { background: rgba(255, 255, 255, 0.8); color: var(--ink); }
.alternar:active { transform: scale(0.88); }

.nav { position: relative; display: flex; flex-direction: column; gap: 2px; }
.grupo { display: block; height: 16px; margin: 16px 12px 6px; font-size: 10.5px; white-space: nowrap; overflow: hidden; transition: opacity 0.25s, margin 0.4s var(--ease-out), height 0.4s var(--ease-out); }
.grupo:first-of-type { margin-top: 0; }
.enlace {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 15px;
  border-radius: 14px;
  color: var(--ink-2);
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.25s, transform 0.4s var(--spring);
}
.enlace svg { flex: none; }
.etiqueta { overflow: hidden; transition: opacity 0.2s, max-width 0.5s var(--ease-out); max-width: 140px; }
.enlace:hover { color: var(--ink); }
.sidebar:not(.compacta) .enlace:hover { transform: translateX(3px); }
.enlace[aria-current='page'] { color: var(--ink); }
.enlace em { margin-left: auto; font-style: normal; font-size: 10.5px; padding: 1px 8px; transition: opacity 0.2s; }
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
  padding: 12px 19px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.95);
  text-align: left;
  white-space: nowrap;
  transition: transform 0.4s var(--spring);
}
.estado:active { transform: scale(0.97); }
.estado-texto { display: grid; line-height: 1.25; overflow: hidden; transition: opacity 0.2s, max-width 0.5s var(--ease-out); max-width: 160px; }
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

/* Modo compacto: solo iconos */
.compacta .cabecera { flex-direction: column; align-items: center; padding: 0; gap: 14px; }
.compacta .marca-texto, .compacta .etiqueta, .compacta .estado-texto { max-width: 0; opacity: 0; }
.compacta .enlace em { opacity: 0; width: 0; padding: 0; margin: 0; overflow: hidden; }
.compacta .grupo { height: 1px; margin: 12px 14px; padding: 0; background: var(--line-strong); opacity: 0.7; }
.compacta .grupo span { opacity: 0; }
.compacta .grupo:first-of-type { display: none; }
.compacta .enlace, .compacta .estado { gap: 0; }

@media (max-width: 900px) {
  .sidebar { width: 76px; }
  .cabecera { flex-direction: column; padding: 0; gap: 14px; }
  .marca-texto, .etiqueta, .estado-texto { max-width: 0; opacity: 0; }
  .alternar { display: none; }
  .enlace em { display: none; }
}
</style>
