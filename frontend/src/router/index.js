import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('../views/Welcome.vue'),
    meta: {
      title: '欢迎',
      requiresAuth: false
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '首页',
      requiresAuth: true
    }
  },
  {
    path: '/auth/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/profit/stats',
    name: 'ProfitStats',
    component: () => import('@/views/ProfitStats.vue'),
    meta: {
      title: '盈利统计',
      requiresAuth: true
    }
  },
  {
    path: '/transactions',
    name: 'TransactionList',
    component: () => import('../views/TransactionList.vue'),
    meta: {
      title: '交易记录',
      requiresAuth: true
    }
  },
  {
    path: '/transactions/add',
    name: 'TransactionAdd',
    component: () => import('../views/TransactionAdd.vue'),
    meta: {
      requiresAuth: true,
      title: '添加交易记录'
    }
  },
  {
    path: '/transactions/edit/:id',
    name: 'TransactionEdit',
    component: () => import('../views/TransactionEdit.vue'),
    meta: {
      requiresAuth: true,
      title: '编辑交易记录'
    }
  },
  {
    path: '/exchange-rates',
    name: 'ExchangeRateManager',
    component: () => import('../views/ExchangeRateManager.vue'),
    meta: {
      title: '汇率管理',
      requiresAuth: true
    }
  },
  {
    path: '/stocks',
    name: 'StockManager',
    component: () => import('../views/StockManager.vue'),
    meta: {
      title: '股票管理',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  try {
    // 设置页面标题
    document.title = to.meta.title ? `${to.meta.title} - 股票交易系统` : '股票交易系统'

    // 检查路由是否需要认证
    if (to.meta.requiresAuth) {
      // 检查登录状态
      const response = await axios.get('/api/auth/check_login', {
        withCredentials: true  // 确保发送 cookies
      })
      
      if (!response.data.is_authenticated) {
        // 未登录，重定向到登录页
        return next({ 
          name: 'Login', 
          query: { redirect: to.fullPath }
        })
      }
    } else if ((to.name === 'Login') && from.name !== 'Login') {
      try {
        const response = await axios.get('/api/auth/check_login', {
          withCredentials: true
        })
        
        if (response.data.is_authenticated) {
          return next({ name: 'Home' })
        }
      } catch (error) {
        console.error('检查登录状态失败:', error)
      }
    }
    
    next()
  } catch (error) {
    console.error('路由守卫错误:', error)
    // 如果检查登录状态失败，为了安全起见，重定向到登录页
    if (to.meta.requiresAuth) {
      return next({ 
        name: 'Login', 
        query: { redirect: to.fullPath }
      })
    }
    next()
  }
})

export default router 