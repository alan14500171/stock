<template>
  <div>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary" v-if="isAuthenticated">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">股票交易系统</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/home" class="nav-link">
                <i class="bi bi-house-door"></i> 首页
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('profit:stats:view')">
              <router-link to="/profit/stats" class="nav-link">
                <i class="bi bi-bar-chart"></i> 收益统计
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('transaction:records:view')">
              <router-link to="/transaction/list" class="nav-link">
                <i class="bi bi-list-ul"></i> 交易记录
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('exchange:rates:view')">
              <router-link to="/exchange/rate" class="nav-link">
                <i class="bi bi-currency-exchange"></i> 汇率管理
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('stock:list:view')">
              <router-link to="/stock" class="nav-link">
                <i class="bi bi-graph-up"></i> 股票管理
              </router-link>
            </li>
            
            <!-- 系统管理下拉菜单 -->
            <li class="nav-item dropdown" v-if="hasAnySystemPermission">
              <a class="nav-link dropdown-toggle" href="#" id="systemDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-gear"></i> 系统管理
              </a>
              <ul class="dropdown-menu" aria-labelledby="systemDropdown">
                <li v-if="hasPermission('system:user:view')">
                  <router-link to="/system/user" class="dropdown-item">
                    <i class="bi bi-people"></i> 用户管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:role:view')">
                  <router-link to="/system/role" class="dropdown-item">
                    <i class="bi bi-person-badge"></i> 角色管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:permission:view')">
                  <router-link to="/system/permission" class="dropdown-item">
                    <i class="bi bi-shield-lock"></i> 权限管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:holder:view')">
                  <router-link to="/system/holder" class="dropdown-item">
                    <i class="bi bi-person-vcard"></i> 持有人管理
                  </router-link>
                </li>
              </ul>
            </li>
          </ul>
          
          <!-- 用户菜单 -->
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-person-circle"></i> {{ currentUsername }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                <li>
                  <a href="#" class="dropdown-item" @click.prevent="openPasswordChangeModal">
                    <i class="bi bi-key"></i> 修改密码
                  </a>
                </li>
                <li>
                  <a href="#" class="dropdown-item" @click.prevent="logout">
                    <i class="bi bi-box-arrow-right"></i> 退出登录
                  </a>
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="container-fluid mt-3">
      <router-view></router-view>
    </div>

    <!-- 密码修改模态框 -->
    <PasswordChangeModal v-if="isAuthenticated" ref="passwordChangeModal" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissionStore } from './stores/permission'
import PasswordChangeModal from './components/PasswordChangeModal.vue'

const router = useRouter()
const permissionStore = usePermissionStore()
const passwordChangeModal = ref(null)

// 计算属性：是否已认证
const isAuthenticated = computed(() => {
  const loggedIn = localStorage.getItem('isLoggedIn') === 'true'
  
  // 检查用户信息是否存在
  let userExists = false
  try {
    const userStr = localStorage.getItem('user')
    userExists = userStr && userStr !== 'undefined' && userStr !== 'null'
    if (userExists) {
      const user = JSON.parse(userStr)
      userExists = user && user.username
    }
  } catch (e) {
    // 清除可能损坏的用户数据
    localStorage.removeItem('user')
    localStorage.removeItem('isLoggedIn')
  }
  
  // 只有当登录状态为true且用户信息存在时，才认为用户已认证
  const authenticated = loggedIn && userExists
  
  return authenticated
})

// 权限检查函数
const hasPermission = (permissionCode) => {
  return permissionStore.hasPermission(permissionCode)
}

// 计算属性：当前用户名
const currentUsername = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.username || ''
  } catch (e) {
    return ''
  }
})

// 计算属性：是否是管理员用户
const isAdmin = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const admin = user.username === 'alan' || user.username === 'admin'
    return admin
  } catch (e) {
    return false
  }
})

// 计算属性：是否有任何系统管理权限
const hasAnySystemPermission = computed(() => {
  const hasPermission = permissionStore.hasPermission('system:user:view') || 
                        permissionStore.hasPermission('system:role:view') || 
                        permissionStore.hasPermission('system:permission:view')
  return hasPermission
})

// 方法：退出登录
const logout = () => {
  // 先移除登录状态和用户信息
  localStorage.removeItem('isLoggedIn')
  localStorage.removeItem('user')
  permissionStore.resetPermissions()
  
  // 确保在路由跳转前完成状态更新
  nextTick(() => {
    // 强制刷新页面以确保导航栏完全关闭
    window.location.href = '/login'
  })
}

// 方法：打开修改密码模态框
const openPasswordChangeModal = () => {
  passwordChangeModal.value.openModal()
}

// 方法：初始化Bootstrap下拉菜单
const initBootstrapDropdowns = () => {
  if (typeof window !== 'undefined') {
    // 确保Bootstrap已加载
    if (!window.bootstrap && typeof bootstrap !== 'undefined') {
      window.bootstrap = bootstrap
    }
    
    if (window.bootstrap) {
      try {
        // 检查导航栏是否显示
        const navbar = document.querySelector('.navbar')
        if (!navbar) {
          return
        }
        
        if (getComputedStyle(navbar).display === 'none') {
          return
        }
        
        // 销毁现有的下拉菜单实例
        const dropdownElementList = document.querySelectorAll('.dropdown-toggle')
        
        if (dropdownElementList.length === 0) {
          return
        }
        
        dropdownElementList.forEach((dropdownToggleEl, index) => {
          // 尝试获取现有实例并销毁
          const instance = window.bootstrap.Dropdown.getInstance(dropdownToggleEl)
          if (instance) {
            instance.dispose()
          }
          
          // 创建新实例
          new window.bootstrap.Dropdown(dropdownToggleEl)
        })
      } catch (error) {
        // 忽略初始化错误
      }
    } else {
      // 尝试从全局变量获取Bootstrap
      setTimeout(() => {
        if (window.bootstrap) {
          initBootstrapDropdowns()
        }
      }, 500)
    }
  }
}

// 监听认证状态变化
watch(isAuthenticated, (newValue) => {
  if (newValue) {
    if (!permissionStore.loaded) {
      permissionStore.loadPermissions()
    }
    
    // 在DOM更新后初始化下拉菜单
    nextTick(() => {
      setTimeout(initBootstrapDropdowns, 300)
    })
  }
})

// 生命周期钩子：组件挂载后
onMounted(() => {
  // 导入Bootstrap
  import('bootstrap').then(module => {
    window.bootstrap = module
    
    // 如果已登录，预加载权限
    if (isAuthenticated.value && !permissionStore.loaded) {
      permissionStore.loadPermissions()
    }
    
    // 确保Bootstrap的下拉菜单正常工作
    nextTick(() => {
      setTimeout(initBootstrapDropdowns, 300)
    })
    
    // 再次尝试初始化下拉菜单（以防第一次尝试失败）
    setTimeout(() => {
      initBootstrapDropdowns()
    }, 1000)
    
    // 第三次尝试初始化下拉菜单
    setTimeout(() => {
      initBootstrapDropdowns()
    }, 2000)
  }).catch(error => {
    // 忽略动态导入Bootstrap失败
  })
  
  // 监听路由变化，在路由变化后重新初始化下拉菜单
  router.beforeEach((to, from, next) => {
    next()
  })
  
  router.afterEach((to, from) => {
    // 检查路由是否与认证相关
    const isAuthRoute = to.path === '/login' || 
                       from.path === '/login' || 
                       to.path === '/logout' || 
                       from.path === '/logout'
    
    if (isAuthRoute) {
      // 在页面完全加载后重新检查认证状态
      setTimeout(() => {
        const currentAuth = localStorage.getItem('isLoggedIn') === 'true'
        
        if (currentAuth && to.path !== '/login') {
          nextTick(() => {
            setTimeout(initBootstrapDropdowns, 300)
          })
        }
      }, 500)
    } else if (isAuthenticated.value) {
      nextTick(() => {
        setTimeout(initBootstrapDropdowns, 300)
      })
    }
  })
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