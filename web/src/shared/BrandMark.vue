<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 36 })
</script>

<template>
  <!-- Ariadna: el hilo que guía a través del laberinto. -->
  <svg :width="size" :height="size" viewBox="0 0 40 40" fill="none" aria-hidden="true">
    <rect width="40" height="40" rx="12" fill="#f4dc94" />
    <path
      class="hilo"
      d="M10 29c0-7.5 5-6.4 8.8-10.2S20 10.6 26 10"
      stroke="#1b1915"
      stroke-width="2.6"
      stroke-linecap="round"
    />
    <circle cx="10" cy="29" r="3.1" fill="#1b1915" />
    <circle cx="27" cy="10" r="3.1" fill="#fffdf6" stroke="#1b1915" stroke-width="1.9" />
  </svg>
</template>

<style scoped>
.hilo {
  stroke-dasharray: 60;
  stroke-dashoffset: 60;
  animation: trazar 1.6s 0.3s var(--ease-out) forwards;
}
@keyframes trazar {
  to { stroke-dashoffset: 0; }
}
</style>
