<script setup lang="ts">
import Sidebar from './shared/Sidebar.vue'
</script>

<template>
  <div class="marco glass">
    <Sidebar />
    <main class="contenido">
      <RouterView v-slot="{ Component, route }">
        <Transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>

<style scoped>
.marco {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.28));
  position: fixed;
  inset: 16px;
  display: flex;
  overflow: hidden;
  border-radius: var(--r-xl);
}
.contenido {
  position: relative;
  flex: 1;
  min-width: 0;
  overflow: hidden auto;
  padding: 28px 32px 32px;
}
@media (max-width: 900px) {
  .marco { inset: 8px; border-radius: 24px; }
  .contenido { padding: 20px 16px 24px; }
}
</style>
