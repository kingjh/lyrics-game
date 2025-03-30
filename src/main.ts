import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import axios from 'axios'

// 配置axios
axios.interceptors.request.use(config => {
  // 添加必要的请求头
  if (config.headers) {
    config.headers['Content-Type'] = 'application/json'
  }
  return config
})

// 配置响应拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('API请求失败:', error)
    return Promise.reject(error)
  }
)

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#7e57c2',
          secondary: '#9575cd',
          accent: '#512da8',
          error: '#e53935',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107',
        },
      },
    },
  },
})

createApp(App)
  .use(router)
  .use(vuetify)
  .mount('#app') 