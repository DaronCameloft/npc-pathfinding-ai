<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{ value: number; decimals?: number; duration?: number; separador?: boolean }>(),
  { decimals: 0, duration: 900, separador: true },
)

const mostrado = ref(props.value)
let cuadro = 0

function formatear(n: number) {
  return n.toLocaleString('es-PE', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
    useGrouping: props.separador,
  })
}

watch(
  () => props.value,
  (destino, origen) => {
    cancelAnimationFrame(cuadro)
    const desde = origen ?? 0
    const t0 = performance.now()
    const paso = (ahora: number) => {
      const t = Math.min(1, (ahora - t0) / props.duration)
      mostrado.value = desde + (destino - desde) * (1 - Math.pow(1 - t, 4))
      if (t < 1) cuadro = requestAnimationFrame(paso)
    }
    cuadro = requestAnimationFrame(paso)
  },
)
onBeforeUnmount(() => cancelAnimationFrame(cuadro))
</script>

<template>
  <span class="num">{{ formatear(mostrado) }}</span>
</template>
