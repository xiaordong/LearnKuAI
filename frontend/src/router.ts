import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'chat', component: () => import('./views/ChatView.vue') },
    { path: '/logs', name: 'logs', component: () => import('./views/LogsView.vue') },
    { path: '/notes', name: 'notes', component: () => import('./views/NotesView.vue') },
  ],
})

export default router
