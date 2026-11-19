import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'inicio', component: () => import('./views/InicioView.vue') },
    { path: '/explorar', name: 'explorar', component: () => import('./views/ExplorarView.vue') },
    { path: '/comparar', name: 'comparar', component: () => import('./views/CompararView.vue') },
    { path: '/simulacion', name: 'simulacion', component: () => import('./views/SimulacionView.vue') },
    { path: '/patrullaje', name: 'patrullaje', component: () => import('./views/PatrullajeView.vue') },
    { path: '/pasillo', name: 'pasillo', component: () => import('./views/PasilloView.vue') },
    { path: '/botin', name: 'botin', component: () => import('./views/BotinView.vue') },
    { path: '/resultados', name: 'resultados', component: () => import('./views/ResultadosView.vue') },
    { path: '/acerca', name: 'acerca', component: () => import('./views/AcercaView.vue') },
    { path: '/:resto(.*)*', redirect: '/' },
  ],
})
