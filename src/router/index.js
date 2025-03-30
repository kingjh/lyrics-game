import { createRouter, createWebHistory } from 'vue-router'
import Game from '../views/Game.vue'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/game/:artist',
    name: 'Game',
    component: Game,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 