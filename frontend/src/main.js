import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
// 导入Bootstrap Icons
import 'bootstrap-icons/font/bootstrap-icons.css'

// 配置axios
axios.defaults.baseURL = ''  // 移除基础URL，因为我们在请求时已经包含了 /api
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

const app = createApp(App)

// 注册路由
app.use(router)

// 挂载应用
app.mount('#app') 