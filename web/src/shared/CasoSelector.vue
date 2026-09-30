<script setup lang="ts">
import Icon from './Icon.vue'

const props = defineProps<{ modelValue: number; total: number }>()
const emit = defineEmits<{ 'update:modelValue': [n: number] }>()

function fijar(n: number) {
  const nuevo = Math.min(Math.max(0, props.total - 1), Math.max(0, Math.round(n) || 0))
  if (nuevo !== props.modelValue) emit('update:modelValue', nuevo)
}
</script>

<template>
  <div class="caso">
    <button type="button" class="mini" aria-label="Caso anterior" @click="fijar(modelValue - 1)"><Icon name="anterior" :size="13" /></button>
    <label class="campo">
      <span class="eyebrow">Caso</span>
      <input
        class="num"
        type="number"
        :value="modelValue"
        :min="0"
        :max="Math.max(0, total - 1)"
        @change="fijar(Number(($event.target as HTMLInputElement).value))"
      />
      <span class="muted num">/ {{ Math.max(0, total - 1).toLocaleString('es-PE') }}</span>
    </label>
    <button type="button" class="mini" aria-label="Caso siguiente" @click="fijar(modelValue + 1)"><Icon name="siguiente" :size="13" /></button>
    <button type="button" class="mini" aria-label="Caso aleatorio" @click="fijar(Math.floor(Math.random() * total))"><Icon name="dado" :size="15" /></button>
  </div>
</template>

<style scoped>
.caso { display: flex; align-items: center; gap: 6px; }
.campo { display: flex; align-items: baseline; gap: 8px; padding: 0 8px; }
.campo input {
  width: 62px;
  padding: 3px 6px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: var(--field);
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
}
.campo input:focus { outline: none; border-color: var(--violet); background: #fff; }
.mini {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  color: var(--ink-2);
  background: var(--field);
  transition: background 0.2s, transform 0.35s var(--spring);
}
.mini:hover { background: rgba(27, 25, 21, 0.1); }
.mini:active { transform: scale(0.86); }
</style>
