import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
// 导入Bootstrap Icons
import 'bootstrap-icons/font/bootstrap-icons.css'
import './assets/main.css'
import permissionDirective from './directives/permission'

// 配置axios
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:9099'
axios.defaults.withCredentials = true
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest'

// 添加请求拦截器
axios.interceptors.request.use(config => {
  // 从localStorage获取token
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // 添加CSRF token
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
  if (csrfToken) {
    config.headers['X-CSRF-TOKEN'] = csrfToken
  }
  
  return config
})

// 创建应用实例
const app = createApp(App)

// 注册全局属性
app.config.globalProperties.$axios = axios

// 注册Pinia
app.use(createPinia())

// 注册路由
app.use(router)

// 注册权限指令
app.use(permissionDirective)

// 挂载应用
app.mount('#app') 