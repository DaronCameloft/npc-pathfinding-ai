<script setup lang="ts" generic="T extends string">
import { nextTick, onMounted, ref, watch } from 'vue'

export interface Opcion<V extends string> {
  valor: V
  etiqueta: string
  detalle?: string
}

const props = defineProps<{ opciones: Opcion<T>[]; modelValue: T; etiqueta: string }>()
const emit = defineEmits<{ 'update:modelValue': [valor: T] }>()

const raiz = ref<HTMLElement | null>(null)
const pulgar = ref({ x: 0, ancho: 0, listo: false })

async function medir() {
  await nextTick()
  const activo = raiz.value?.querySelector<HTMLElement>('[aria-checked="true"]')
  if (activo) pulgar.value = { x: activo.offsetLeft, ancho: activo.offsetWidth, listo: true }
}
onMounted(() => {
  medir()
  document.fonts?.ready.then(medir)
})
watch(() => [props.modelValue, props.opciones.length], medir)
</script>

<template>
  <div ref="raiz" class="seg" role="radiogroup" :aria-label="etiqueta">
    <span
      class="pulgar"
      :class="{ listo: pulgar.listo }"
      :style="{ width: `${pulgar.ancho}px`, transform: `translateX(${pulgar.x}px)` }"
    />
    <button
      v-for="o in opciones"
      :key="o.valor"
      type="button"
      role="radio"
      :aria-checked="o.valor === modelValue"
      class="opcion"
      @click="emit('update:modelValue', o.valor)"
    >
      <span class="et">{{ o.etiqueta }}</span>
      <small v-if="o.detalle" class="num">{{ o.detalle }}</small>
    </button>
  </div>
</template>

<style scoped>
.seg {
  position: relative;
  display: inline-flex;
  padding: 4px;
  border-radius: 999px;
  background: var(--field);
}
.pulgar {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 0;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 1px 2px rgba(27, 25, 21, 0.06);
  opacity: 0;
  transition: transform 0.55s var(--spring), width 0.4s var(--ease-out), opacity 0.2s;
}
.pulgar.listo { opacity: 1; }
.opcion {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 7px 16px;
  border-radius: 999px;
  color: var(--ink-3);
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.25s;
}
.opcion:hover { color: var(--ink); }
.opcion[aria-checked='true'] { color: var(--ink); }
.opcion small { font-size: 10.5px; color: var(--ink-4); font-weight: 400; }
</style>
