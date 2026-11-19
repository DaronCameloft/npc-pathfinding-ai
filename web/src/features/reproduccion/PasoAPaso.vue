<script setup lang="ts">
import Icon from '../../shared/Icon.vue'
import type { Pasos } from './usePasos'

defineProps<{ pasos: Pasos; total: number; etiqueta?: string }>()
</script>

<template>
  <div class="paso-a-paso" :class="{ apagado: !total }">
    <button type="button" class="ic" aria-label="Reiniciar" @click="pasos.reiniciar()"><Icon name="reiniciar" :size="15" /></button>
    <button type="button" class="ic" aria-label="Paso atrás" @click="pasos.paso(-1)"><Icon name="anterior" :size="15" /></button>
    <button type="button" class="play" :aria-label="pasos.reproduciendo.value ? 'Pausar' : 'Reproducir'" @click="pasos.alternar()">
      <Icon :name="pasos.reproduciendo.value ? 'pausa' : 'play'" :size="17" :stroke="2" />
    </button>
    <button type="button" class="ic" aria-label="Paso adelante" @click="pasos.paso(1)"><Icon name="siguiente" :size="15" /></button>
    <button type="button" class="ic" aria-label="Ir al final" @click="pasos.alFinal()"><Icon name="bandera" :size="15" /></button>
    <span class="riel"><i :style="{ width: `${total ? (pasos.indice.value / total) * 100 : 0}%` }" /></span>
    <span class="contador mono num">{{ etiqueta ?? 'Paso' }} {{ pasos.indice.value }}<i> / </i>{{ total }}</span>
  </div>
</template>

<style scoped>
.paso-a-paso {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px 6px 6px;
  border-radius: 999px;
  background: var(--field);
}
.apagado { opacity: 0.5; pointer-events: none; }
.ic, .play {
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: var(--ink-2);
  transition: background 0.2s, transform 0.3s var(--spring);
}
.ic { width: 30px; height: 30px; }
.ic:hover { background: #fff; color: var(--ink); }
.play { width: 36px; height: 36px; margin: 0 2px; background: var(--ink); color: #fff; }
.ic:active, .play:active { transform: scale(0.88); }
.riel { position: relative; flex: 1; min-width: 40px; height: 4px; margin: 0 10px; border-radius: 4px; background: var(--line-strong); overflow: hidden; }
.riel i { position: absolute; inset: 0 auto 0 0; background: var(--violet); border-radius: 4px; transition: width 0.35s var(--ease-out); }
.contador { font-size: 11.5px; color: var(--ink-2); white-space: nowrap; }
.contador i { color: var(--ink-4); font-style: normal; }
</style>
