// AIMETA P=Vue应用入口_创建和挂载应用|R=应用初始化_插件注册|NR=不含组件实现|E=main.ts|X=ui|A=createApp_use_mount|D=vue,pinia,vue-router|S=dom|RD=./README.ai
import '@fontsource/noto-sans-sc/300.css';
import '@fontsource/noto-sans-sc/400.css';
import '@fontsource/noto-sans-sc/500.css';
import '@fontsource/noto-sans-sc/700.css';

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { allowUrlToken, consumeTokenFromLocation, setStoredToken } from './utils/authToken'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Handle token from URL (only in development or when explicitly enabled)
if (allowUrlToken()) {
  const token = consumeTokenFromLocation()
  if (token) {
    const authStore = useAuthStore()
    authStore.token = token
    setStoredToken(token)
    authStore.fetchUser()
  }
}

app.mount('#app')
