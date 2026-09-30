<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 38 })
</script>

<template>
  <!-- Ariadna: el hilo que guía a través del laberinto. -->
  <svg :width="size" :height="size" viewBox="0 0 40 40" fill="none" aria-hidden="true">
    <defs>
      <linearGradient id="marca-fondo" x1="4" y1="2" x2="38" y2="40" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#f8cf7c" />
        <stop offset="1" stop-color="#d9822b" />
      </linearGradient>
    </defs>
    <rect width="40" height="40" rx="12" fill="url(#marca-fondo)" />
    <rect x="0.5" y="0.5" width="39" height="39" rx="11.5" stroke="rgba(255,255,255,.55)" />
    <path
      class="hilo"
      d="M10 29c0-7.5 5-6.4 8.8-10.2S20 10.6 26 10"
      stroke="#1d1a16"
      stroke-width="2.6"
      stroke-linecap="round"
    />
    <circle cx="10" cy="29" r="3.1" fill="#1d1a16" />
    <circle cx="27" cy="10" r="3.1" fill="#fffaf0" stroke="#1d1a16" stroke-width="1.9" />
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
