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

const app = createApp(App)

// 注册路由
app.use(router)

// 挂载应用
app.mount('#app') 