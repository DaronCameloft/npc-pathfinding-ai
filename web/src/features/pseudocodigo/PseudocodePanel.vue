<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import Icon from '../../shared/Icon.vue'
import type { LineaPseudocodigo } from '../../core/types'

const props = defineProps<{
  nombre: string
  lineas: LineaPseudocodigo[]
  /** Número de línea que se ejecuta ahora (0 = ninguna). */
  activa: number
  conteos: Record<number, number>
}>()

const lista = ref<HTMLElement | null>(null)
const resalte = ref({ y: 0, alto: 0, visible: false })

/** El resalte se mide sobre la fila real: las líneas largas pueden ocupar dos renglones. */
async function medir() {
  await nextTick()
  const fila = lista.value?.querySelector<HTMLElement>(`[data-linea="${props.activa}"]`)
  if (!fila) {
    resalte.value.visible = false
    return
  }
  resalte.value = { y: fila.offsetTop, alto: fila.offsetHeight, visible: true }
}

onMounted(() => {
  medir()
  document.fonts?.ready.then(medir)
})
watch(() => [props.activa, props.lineas], medir)
</script>

<template>
  <section class="card panel" aria-label="Pseudocódigo">
    <header class="card-title">
      <span class="badge-icon"><Icon name="codigo" :size="16" /></span>
      Pseudocódigo
      <span class="pill nombre" title="Cada línea muestra cuántas veces se ha ejecutado hasta ahora">{{ nombre }}</span>
    </header>

    <ol ref="lista" class="lineas">
      <span
        class="resalte"
        :class="{ visible: resalte.visible }"
        :style="{ transform: `translateY(${resalte.y}px)`, height: `${resalte.alto}px` }"
      />
      <li v-for="l in lineas" :key="l.numero" :data-linea="l.numero" :class="{ activa: l.numero === activa }">
        <span class="numero mono">{{ l.numero }}</span>
        <span class="texto mono" :style="{ paddingLeft: `${l.nivel * 18}px` }">{{ l.texto }}</span>
        <span class="conteo mono num" :class="{ vacio: !conteos[l.numero] }">
          {{ conteos[l.numero] ? `×${conteos[l.numero].toLocaleString('es-PE')}` : '' }}
        </span>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 8px; padding-bottom: 14px; }
.nombre { margin-left: auto; font-family: var(--font-ui); font-size: 11.5px; }
.lineas { position: relative; margin: 0; padding: 0; list-style: none; }
.lineas li {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 22px 1fr auto;
  align-items: start;
  gap: 8px;
  min-height: 28px;
  padding: 5px 10px;
  font-size: 11.6px;
  line-height: 1.42;
  color: var(--ink-3);
  transition: color 0.25s;
}
.lineas li.activa { color: var(--ink); }
.numero { color: var(--ink-4); text-align: right; font-size: 11px; padding-top: 1px; }
.activa .numero { color: var(--violet); font-weight: 500; }
.texto { min-width: 0; overflow-wrap: anywhere; }
.conteo { min-width: 44px; padding-top: 1px; text-align: right; font-size: 10.5px; color: var(--ink-3); transition: opacity 0.3s; }
.conteo.vacio { opacity: 0; }
.activa .conteo { color: var(--violet); }
.resalte {
  position: absolute;
  z-index: 0;
  inset: 0 0 auto 0;
  border-radius: 11px;
  background: var(--violet-soft);
  box-shadow: inset 3px 0 0 var(--violet), 0 8px 18px -12px rgba(106, 63, 216, 0.6);
  opacity: 0;
  transition: transform 0.5s var(--spring-soft), height 0.35s var(--ease-out), opacity 0.3s;
}
.resalte.visible { opacity: 1; }
</style>
