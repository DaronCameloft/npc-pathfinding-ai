<script setup lang="ts">
/** Fondo artístico de la tarjeta principal: capas planas de crema y dorado, sin degradados. */
</script>

<template>
  <svg class="arte" viewBox="0 0 600 420" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <rect width="600" height="420" fill="#f6e7b8" />

    <g class="soles">
      <circle cx="545" cy="70" r="215" fill="#f3d789" />
      <circle cx="545" cy="70" r="150" fill="#f1cd6d" />
      <circle cx="545" cy="70" r="88" fill="#efc255" />
    </g>

    <g class="ola ola-a">
      <path d="M-40 250C90 170 210 330 340 250S540 150 660 210V460H-40Z" fill="#fbf0cf" />
    </g>
    <g class="ola ola-b">
      <path d="M-40 300C80 240 200 380 330 310S520 240 660 290V460H-40Z" fill="#f8e7ae" />
    </g>
    <g class="ola ola-c">
      <path d="M-40 350C110 310 230 410 380 360S540 330 660 360V460H-40Z" fill="#f2d98f" />
    </g>

    <g fill="none" stroke="#ffffff" stroke-linecap="round" class="hilos">
      <path d="M-20 205C120 120 240 300 380 210S560 110 640 170" stroke-width="1.6" opacity=".7" />
      <path d="M-20 232C120 150 250 325 390 235S560 140 640 195" stroke-width="1.2" opacity=".5" />
      <path d="M330 -20C300 90 380 190 470 250" stroke-width="1.4" opacity=".55" />
    </g>
  </svg>
</template>

<style scoped>
.arte {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: inherit;
}
.soles { transform-origin: 545px 70px; animation: respirar 9s ease-in-out infinite; }
.ola { animation: derivar 14s ease-in-out infinite alternate; }
.ola-b { animation-duration: 18s; animation-direction: alternate-reverse; }
.ola-c { animation-duration: 22s; }
.hilos { animation: derivar 26s ease-in-out infinite alternate-reverse; }
@keyframes respirar { 50% { transform: scale(1.06); } }
@keyframes derivar {
  from { transform: translateX(-22px); }
  to { transform: translateX(22px); }
}
</style>
