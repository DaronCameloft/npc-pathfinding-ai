<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; size?: number; stroke?: number }>(), {
  size: 18,
  stroke: 1.7,
})

/** Iconos de trazo sobre una cuadrícula de 24 px. */
const trazos: Record<string, string[]> = {
  inicio: ['M4 11.2 12 4l8 7.2', 'M6 10v9h12v-9', 'M10 19v-5h4v5'],
  explorar: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z', 'm15.5 8.5-2 5-5 2 2-5 5-2Z'],
  comparar: ['M4 5h7v14H4z', 'M13 5h7v14h-7z'],
  resultados: ['M4 19V5', 'M4 19h16', 'M8 15v-4', 'M12 15V8', 'M16 15v-6'],
  acerca: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z', 'M12 11v5', 'M12 8h.01'],
  simulacion: ['M6 4h12v16H6z', 'M9 8h6', 'M9 12h6', 'M9 16h3'],
  play: ['M8 5.5v13l11-6.5-11-6.5Z'],
  pausa: ['M8 5h3v14H8z', 'M13 5h3v14h-3z'],
  siguiente: ['M6 5.5v13l9-6.5-9-6.5Z', 'M18 5v14'],
  anterior: ['M18 5.5v13L9 12l9-6.5Z', 'M6 5v14'],
  reiniciar: ['M4 12a8 8 0 1 0 2.6-5.9', 'M4 5v4.5h4.5'],
  codigo: ['m8.5 8-4 4 4 4', 'm15.5 8 4 4-4 4', 'm13.5 5-3 14'],
  metricas: ['M4 14a8 8 0 1 1 16 0', 'M12 14l3.5-4.5', 'M12 14h.01'],
  bloquear: ['M4 4h16v16H4z', 'm9 9 6 6', 'm15 9-6 6'],
  dado: ['M4 4h16v16H4z', 'M8.5 8.5h.01', 'M15.5 8.5h.01', 'M12 12h.01', 'M8.5 15.5h.01', 'M15.5 15.5h.01'],
  bandera: ['M6 21V4', 'M6 4h11l-2 4 2 4H6'],
  chip: ['M7 7h10v10H7z', 'M10 3v4', 'M14 3v4', 'M10 17v4', 'M14 17v4', 'M3 10h4', 'M3 14h4', 'M17 10h4', 'M17 14h4'],
  chispa: ['M12 3v4', 'M12 17v4', 'M3 12h4', 'M17 12h4', 'm6 6 2.5 2.5', 'm15.5 15.5 2.5 2.5', 'm18 6-2.5 2.5', 'm8.5 15.5-2.5 2.5'],
  flecha: ['M5 12h14', 'm13 6 6 6-6 6'],
  candado: ['M6 11h12v9H6z', 'M8.5 11V8a3.5 3.5 0 0 1 7 0v3'],
  check: ['m5 12.5 4.5 4.5L19 7.5'],
  panel: ['M4 5h16v14H4z', 'M9.5 5v14'],
  zoom_mas: ['M12 5v14', 'M5 12h14'],
  zoom_menos: ['M5 12h14'],
  ajustar: ['M4 9V4h5', 'M20 9V4h-5', 'M4 15v5h5', 'M20 15v5h-5'],
}

const rutas = computed(() => trazos[props.name] ?? [])
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, i) in rutas" :key="i" :d="d" />
  </svg>
</template>
