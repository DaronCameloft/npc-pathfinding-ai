<script setup lang="ts">
import Sidebar from './shared/Sidebar.vue'
</script>

<template>
  <div class="marco">
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
  position: fixed;
  inset: 12px;
  display: flex;
  gap: 12px;
}
.contenido {
  position: relative;
  flex: 1;
  min-width: 0;
  overflow: hidden auto;
  padding: 28px 32px 32px;
  border-radius: var(--r-xl);
  background: var(--panel);
  border: 1px solid var(--line);
}
@media (max-width: 900px) {
  .marco { inset: 8px; gap: 8px; }
  .contenido { padding: 20px 16px 24px; border-radius: 24px; }
}
</style>
