<template>
  <div class="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" :to="isAuthenticated ? '/home' : '/'">股票交易记录系统</router-link>
        
        <!-- 未登录状态显示登录按钮 -->
        <div v-if="!isAuthenticated" class="navbar-nav ms-auto">
          <router-link to="/auth/login" class="nav-link">登录</router-link>
        </div>

        <!-- 登录状态显示完整导航菜单 -->
        <template v-else>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'ProfitStats'}">盈利统计</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'TransactionList'}">交易记录</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'ExchangeRateManager'}">汇率管理</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'StockManager'}">股票管理</router-link>
              </li>
              
              <!-- 系统管理下拉菜单 -->
              <li class="nav-item dropdown" v-if="hasAnySystemPermission">
                <a class="nav-link dropdown-toggle" href="#" id="systemDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                  <i class="bi bi-gear"></i> 系统管理
                </a>
                <ul class="dropdown-menu" aria-labelledby="systemDropdown">
                  <li v-if="hasPermission('system:user:view')">
                    <router-link class="dropdown-item" :to="{name: 'SystemUser'}">
                      <i class="bi bi-people me-2"></i>用户管理
                    </router-link>
                  </li>
                  <li v-if="hasPermission('system:role:view')">
                    <router-link class="dropdown-item" :to="{name: 'SystemRole'}">
                      <i class="bi bi-person-badge me-2"></i>角色管理
                    </router-link>
                  </li>
                  <li v-if="hasPermission('system:permission:view')">
                    <router-link class="dropdown-item" :to="{name: 'SystemPermission'}">
                      <i class="bi bi-key me-2"></i>权限管理
                    </router-link>
                  </li>
                </ul>
              </li>
            </ul>
            <ul class="navbar-nav ms-auto">
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'ChangePassword'}">
                  <i class="bi bi-key"></i> 修改密码
                </router-link>
              </li>
              <li class="nav-item">
                <a href="#" class="nav-link" @click.prevent="handleLogout">
                  <i class="bi bi-box-arrow-right"></i> 退出登录
                </a>
              </li>
            </ul>
          </div>
        </template>
      </div>
    </nav>

    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    
    <!-- 密码修改弹窗组件 -->
    <PasswordChangeModal ref="passwordChangeModal" />
    <MessageToast />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import useMessage from './composables/useMessage'
import PasswordChangeModal from './components/PasswordChangeModal.vue'
import MessageToast from './components/MessageToast.vue'
import { usePermissionStore } from './stores/permission'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const permissionStore = usePermissionStore()
const isAuthenticated = ref(false)
const username = ref('')
const passwordChangeModal = ref(null)

// 检查是否有任何系统管理相关权限
const hasAnySystemPermission = computed(() => {
  return permissionStore.hasPermission('system:user:list') || 
         permissionStore.hasPermission('system:role:list') || 
         permissionStore.hasPermission('system:permission:list')
})

// 检查是否有指定权限
const hasPermission = (permission) => {
  return permissionStore.hasPermission(permission)
}

// 打开密码修改弹窗
const openPasswordModal = () => {
  if (passwordChangeModal.value) {
    passwordChangeModal.value.openModal()
  }
}

// 检查登录状态
const checkAuth = async () => {
  try {
    const response = await axios.get('/api/auth/check')
    isAuthenticated.value = response.data.authenticated
    username.value = response.data.username || ''
    
    // 如果已登录，加载用户权限
    if (isAuthenticated.value) {
      await permissionStore.loadPermissions()
    } else {
      permissionStore.resetPermissions()
    }
    
    // 如果已登录但在登录页面，重定向到首页
    if (isAuthenticated.value && router.currentRoute.value.name === 'Login') {
      const redirectPath = router.currentRoute.value.query.redirect || '/home'
      router.push(redirectPath)
    }
    
    // 如果未登录且需要认证，重定向到登录页
    if (!isAuthenticated.value && router.currentRoute.value.meta.requiresAuth) {
      router.push({
        name: 'Login',
        query: { redirect: router.currentRoute.value.fullPath }
      })
    }
  } catch (error) {
    console.error('检查登录状态失败:', error)
    isAuthenticated.value = false
    username.value = ''
    permissionStore.resetPermissions()
  }
}

// 处理登录成功
const handleLoginSuccess = async () => {
  isAuthenticated.value = true
  const redirectPath = router.currentRoute.value.query.redirect || '/home'
  await router.push(redirectPath)
}

// 处理退出登录
const handleLogout = async () => {
  try {
    const response = await axios.get('/api/auth/logout')
    if (response.data.success) {
      isAuthenticated.value = false
      message.success('退出登录成功')
      username.value = ''
      permissionStore.resetPermissions()
      router.push('/')
    }
  } catch (error) {
    console.error('退出登录失败:', error)
    message.error('退出登录失败，请稍后重试')
  }
}

// 监听路由变化，检查登录状态
watch(
  () => route.path,
  async (newPath) => {
    // 如果是登录页面，不需要检查登录状态
    if (newPath === '/auth/login') return
    
    // 如果未登录，检查登录状态
    if (!isAuthenticated.value) {
      await checkAuth()
    }
  }
)

// 组件挂载时添加事件监听
onMounted(async () => {
  await checkAuth()
  window.addEventListener('login-success', handleLoginSuccess)
})

// 组件卸载前移除事件监听
onBeforeUnmount(() => {
  window.removeEventListener('login-success', handleLoginSuccess)
})
</script>

<style>
.app-container {
  min-height: 100vh;
  background-color: #f8f9fa;
}

.navbar {
  margin-bottom: 0;
  padding: 0.5rem 1rem;
  background-color: #343a40 !important;
}

/* 导航栏样式优化 */
.navbar-brand {
  font-weight: 500;
  font-size: 1.1rem;
  color: #fff !important;
}

.navbar-nav .nav-link {
  color: rgba(255, 255, 255, 0.85) !important;
  padding: 0.5rem 1rem;
  font-weight: 400;
  font-size: 0.9rem;
}

.navbar-nav .nav-link:hover {
  color: #fff !important;
}

.navbar-nav .nav-link.active {
  color: #fff !important;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 0.25rem;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式调整 */
@media (max-width: 991.98px) {
  .navbar-nav {
    padding: 0.5rem 0;
  }
  
  .navbar-nav .nav-link {
    padding: 0.5rem 0;
  }
  
  .navbar-nav .nav-item {
    margin: 0.25rem 0;
  }
}
</style> 