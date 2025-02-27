import { createRouter, createWebHistory } from 'vue-router'
import { usePermissionStore } from '../stores/permission'
import Welcome from '../views/Welcome.vue'
import Login from '../views/Login.vue'
import ChangePassword from '../views/auth/ChangePassword.vue'
import Home from '../views/Home.vue'
import StockManager from '../views/StockManager.vue'
import TransactionList from '../views/TransactionList.vue'
import ProfitStats from '../views/profit/Stats.vue'
import ExchangeRateManager from '../views/ExchangeRateManager.vue'
import NotFound from '../views/NotFound.vue'

// 系统管理页面
import User from '../views/system/User.vue'
import Role from '../views/system/Role.vue'
import Permission from '../views/system/Permission.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome,
    meta: {
      title: '欢迎',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/auth/change-password',
    name: 'ChangePassword',
    component: ChangePassword,
    meta: {
      title: '修改密码',
      requiresAuth: true
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页',
      requiresAuth: true
    }
  },
  {
    path: '/stock',
    name: 'StockManager',
    component: StockManager,
    meta: {
      title: '股票管理',
      requiresAuth: true
    }
  },
  {
    path: '/transaction/list',
    name: 'TransactionList',
    component: TransactionList,
    meta: { requiresAuth: true }
  },
  {
    path: '/profit/stats',
    name: 'ProfitStats',
    component: ProfitStats,
    meta: { requiresAuth: true }
  },
  {
    path: '/exchange/rate',
    name: 'ExchangeRate',
    component: ExchangeRateManager,
    meta: { requiresAuth: true }
  },
  // 系统管理路由
  {
    path: '/system/user',
    name: 'SystemUser',
    component: User,
    meta: { 
      requiresAuth: true,
      permission: 'system:user:view'
    }
  },
  {
    path: '/system/role',
    name: 'SystemRole',
    component: Role,
    meta: { 
      requiresAuth: true,
      permission: 'system:role:view'
    }
  },
  {
    path: '/system/permission',
    name: 'SystemPermission',
    component: Permission,
    meta: { 
      requiresAuth: true,
      permission: 'system:permission:view'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 检查路由是否需要认证
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (!requiresAuth) {
    // 不需要认证的路由直接放行
    return next()
  }
  
  // 检查认证状态
  const token = localStorage.getItem('token')
  if (!token) {
    // 未认证，重定向到登录页
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  
  // 检查权限
  const permissionStore = usePermissionStore()
  
  // 如果权限尚未加载，则加载权限
  if (!permissionStore.loaded) {
    try {
      await permissionStore.loadPermissions()
    } catch (error) {
      console.error('加载权限失败:', error)
      localStorage.removeItem('token')
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }
  }
  
  // 检查路由是否需要特定权限
  const requiredPermission = to.meta.permission
  if (requiredPermission && !permissionStore.hasPermission(requiredPermission)) {
    // 没有所需权限，重定向到首页
    console.warn(`用户缺少访问 ${to.path} 所需的权限: ${requiredPermission}`)
    return next({ name: 'Home' })
  }
  
  // 通过所有检查，放行
  next()
})

export default router 