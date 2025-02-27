import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const usePermissionStore = defineStore('permission', () => {
  // 用户权限列表
  const permissions = ref([])
  // 用户角色列表
  const roles = ref([])
  // 是否已加载权限
  const loaded = ref(false)
  // 加载状态
  const loading = ref(false)

  // 加载用户权限
  const loadPermissions = async () => {
    if (loaded.value) return
    
    loading.value = true
    try {
      const response = await axios.get('/api/system/user/info')
      
      if (response.data.success) {
        permissions.value = response.data.data.permissions || []
        roles.value = response.data.data.roles || []
        loaded.value = true
      } else {
        console.error('加载权限失败:', response.data.message)
      }
    } catch (error) {
      console.error('加载权限失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 检查是否有指定权限
  const hasPermission = (permission) => {
    // 如果没有传入权限标识，或者权限列表为空，则返回 false
    if (!permission || permissions.value.length === 0) {
      return false
    }
    
    // 检查是否包含指定权限
    return permissions.value.some(p => p.code === permission)
  }

  // 检查是否有指定角色
  const hasRole = (role) => {
    // 如果没有传入角色标识，或者角色列表为空，则返回 false
    if (!role || roles.value.length === 0) {
      return false
    }
    
    // 检查是否包含指定角色
    return roles.value.some(r => r.name === role)
  }

  // 重置权限状态
  const resetPermissions = () => {
    permissions.value = []
    roles.value = []
    loaded.value = false
  }

  return {
    permissions,
    roles,
    loaded,
    loading,
    loadPermissions,
    hasPermission,
    hasRole,
    resetPermissions
  }
}) 