import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import * as bootstrap from 'bootstrap'
// 导入Bootstrap Icons
import 'bootstrap-icons/font/bootstrap-icons.css'
import './assets/main.css'
import permissionDirective from './directives/permission'

// 导入 Toast 插件
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

// 将Bootstrap挂载到window对象
window.bootstrap = bootstrap

// 在DOM加载完成后初始化Bootstrap组件
document.addEventListener('DOMContentLoaded', () => {
  // 从Bootstrap获取全局变量
  window.bootstrap = bootstrap;
  
  // 初始化所有下拉菜单
  const dropdownElementList = document.querySelectorAll('.dropdown-toggle');
  if (dropdownElementList.length > 0) {
    dropdownElementList.forEach((dropdownToggleEl, index) => {
      new bootstrap.Dropdown(dropdownToggleEl);
    });
  }
  
  // 初始化所有模态框
  const modalElements = document.querySelectorAll('.modal');
  if (modalElements.length > 0) {
    modalElements.forEach((modalEl, index) => {
      new bootstrap.Modal(modalEl);
    });
  }
});

// 配置axios
const axiosInstance = axios.create({
  baseURL: '/api',  // 使用相对路径
  timeout: 15000,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
  }
})

// axios请求拦截器
axiosInstance.interceptors.request.use(
  config => {
    // 在发送请求前做些什么
    
    return config;
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error);
  }
);

// axios响应拦截器
axiosInstance.interceptors.response.use(
  response => {
    // 对响应数据做些什么
    
    return response;
  },
  error => {
    // 对响应错误做些什么
    return Promise.reject(error);
  }
);

// 创建应用实例
const app = createApp(App)

// 注册Element Plus
app.use(ElementPlus, {
  locale: zhCn,
})

// 注册 Toast 插件
app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: true,
  closeButton: 'button',
  icon: true,
  rtl: false
})

// 注册全局属性
app.config.globalProperties.$axios = axiosInstance
app.config.globalProperties.$bootstrap = bootstrap

// 注册Pinia
app.use(createPinia())

// 注册路由
app.use(router)

// 注册权限指令
app.use(permissionDirective)

// 挂载应用
app.mount('#app') 