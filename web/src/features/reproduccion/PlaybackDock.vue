<script setup lang="ts">
import { computed } from 'vue'
import Icon from '../../shared/Icon.vue'
import { VELOCIDADES } from './usePlayback'

const props = defineProps<{
  reproduciendo: boolean
  indice: number
  total: number
  velocidad: number
  deshabilitado?: boolean
}>()
const emit = defineEmits<{
  alternar: []
  paso: [n: number]
  reiniciar: []
  final: []
  buscar: [n: number]
  velocidad: [i: number]
}>()

const porcentaje = computed(() => (props.total ? (props.indice / props.total) * 100 : 0))
const fmt = (n: number) => n.toLocaleString('es-PE')

function ciclarVelocidad() {
  emit('velocidad', (props.velocidad + 1) % VELOCIDADES.length)
}
</script>

<template>
  <div class="dock glass" :class="{ apagado: deshabilitado }">
    <div class="botones">
      <button type="button" class="ic" aria-label="Reiniciar" @click="emit('reiniciar')"><Icon name="reiniciar" :size="16" /></button>
      <button type="button" class="ic" aria-label="Paso atrás" @click="emit('paso', -1)"><Icon name="anterior" :size="16" /></button>
      <button type="button" class="play" :aria-label="reproduciendo ? 'Pausar' : 'Reproducir'" @click="emit('alternar')">
        <span class="glifo" :class="{ visible: reproduciendo }"><Icon name="pausa" :size="20" :stroke="2" /></span>
        <span class="glifo" :class="{ visible: !reproduciendo }"><Icon name="play" :size="20" :stroke="2" /></span>
      </button>
      <button type="button" class="ic" aria-label="Paso adelante" @click="emit('paso', 1)"><Icon name="siguiente" :size="16" /></button>
      <button type="button" class="ic" aria-label="Ir al final" @click="emit('final')"><Icon name="bandera" :size="16" /></button>
    </div>

    <label class="linea">
      <span class="sr">Posición en la traza</span>
      <input
        type="range"
        min="0"
        :max="total"
        :value="indice"
        :style="{ '--p': `${porcentaje}%` }"
        @input="emit('buscar', Number(($event.target as HTMLInputElement).value))"
      />
    </label>

    <span class="contador mono num">{{ fmt(indice) }}<i> / </i>{{ fmt(total) }}</span>
    <button type="button" class="vel num" aria-label="Cambiar velocidad" @click="ciclarVelocidad">
      {{ VELOCIDADES[velocidad].etiqueta }}
    </button>
  </div>
</template>

<style scoped>
.dock {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 10px 8px 12px;
  border-radius: 999px;
  transition: opacity 0.3s;
}
.dock.apagado { opacity: 0.5; pointer-events: none; }
.botones { display: flex; align-items: center; gap: 2px; }
.ic {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: var(--ink-2);
  transition: background 0.2s, transform 0.35s var(--spring);
}
.ic:hover { background: rgba(27, 25, 21, 0.06); }
.ic:active { transform: scale(0.86); }
.play {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  margin: 0 4px;
  border-radius: 50%;
  color: #fff;
  background: var(--ink);
  transition: transform 0.4s var(--spring), background 0.2s;
}
.play:hover { background: #2f2a24; }
.play:active { transform: scale(0.9); }
.play { position: relative; }
.glifo {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  opacity: 0;
  transform: scale(0.5) rotate(-45deg);
  transition: opacity 0.2s, transform 0.35s var(--spring);
}
.glifo.visible { opacity: 1; transform: none; }

.linea { flex: 1; min-width: 80px; display: block; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
input[type='range'] {
  --p: 0%;
  width: 100%;
  height: 22px;
  margin: 0;
  background: none;
  appearance: none;
  cursor: pointer;
}
input[type='range']::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--violet) var(--p), var(--field) var(--p));
}
input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  margin-top: -6px;
  border-radius: 50%;
  background: #fff;
  border: 1px solid var(--line-strong);
  box-shadow: 0 2px 6px rgba(27, 25, 21, 0.2);
  transition: transform 0.3s var(--spring);
}
input[type='range']:active::-webkit-slider-thumb { transform: scale(1.25); }
input[type='range']::-moz-range-track { height: 6px; border-radius: 999px; background: rgba(27, 25, 21, 0.1); }
input[type='range']::-moz-range-progress { height: 6px; border-radius: 999px; background: var(--violet); }
input[type='range']::-moz-range-thumb { width: 16px; height: 16px; border-radius: 50%; background: #fff; border: 1px solid var(--line-strong); }

.contador { min-width: 112px; text-align: right; font-size: 12px; color: var(--ink-2); }
.contador i { font-style: normal; color: var(--ink-4); }
.vel {
  min-width: 52px;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--field);
  font-size: 12.5px;
  font-weight: 600;
  transition: transform 0.35s var(--spring);
}
.vel:active { transform: scale(0.9); }
@media (max-width: 720px) {
  .contador { display: none; }
}
</style>
