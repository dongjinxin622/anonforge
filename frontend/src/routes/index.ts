import { createRouter, createWebHistory } from 'vue-router'


const routes = [
  {
    path: '/',
    component: () => import('../pages/Login.vue')
  },
  {
    path: '/login',
    component: () => import('../pages/Login.vue')
  },
  {
    path: '/project',
    component: () => import('../pages/Project.vue')
  },


]


const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router;
