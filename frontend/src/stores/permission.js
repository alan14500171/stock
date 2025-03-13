import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useUserStore } from './user'

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
    // 如果权限已经加载，则不重复加载
    if (loaded.value && permissions.value.length > 0) {
      return;
    }
    
    loading.value = true;
    
    try {
      const userStore = useUserStore();
      const user = userStore.user;
      const isAdmin = userStore.isAdmin;
      
      // 如果是管理员用户，授予所有权限
      if (isAdmin) {
        // 设置管理员角色和权限
        roles.value = [
          { id: 'admin', name: '管理员', code: 'admin' }
        ];
        setAdminPermissions();
      } else {
        try {
          // 从后端获取用户权限
          const response = await axios.get('/api/auth/user/permissions');
          const userData = response.data.data;
          
          // 处理权限数据
          let permissionsData = userData.permissions || [];
          
          if (permissionsData && Array.isArray(permissionsData)) {
            if (permissionsData.length > 0) {
              // 判断数据类型（字符串数组或对象数组）
              const firstItem = permissionsData[0];
              
              // 统一转换为对象数组形式
              if (typeof firstItem === 'string') {
                permissions.value = permissionsData.map(p => ({ code: p }));
              } else {
                permissions.value = permissionsData;
              }
            } else {
              permissions.value = [];
            }
          }
          
          // 处理角色数据
          const rolesData = userData.roles || [];
          roles.value = Array.isArray(rolesData) ? rolesData : [];
          
        } catch (error) {
          // 加载失败时设置默认权限
          permissions.value = [];
          roles.value = [];
          setDefaultPermissions();
        }
      }
    } catch (error) {
      // 出错时设置默认权限
      setDefaultPermissions();
    } finally {
      loading.value = false;
      loaded.value = true;
    }
  };

  // 设置管理员权限
  const setAdminPermissions = () => {
    console.log('设置管理员权限')
    permissions.value = [
      // 股票管理
      'stock',
      'stock:list',
      'stock:list:view',
      'stock:list:add',
      'stock:list:edit',
      'stock:list:delete',
      'stock:holdings',
      'stock:holdings:view',
      'stock:holdings:export',
      
      // 交易管理
      'transaction',
      'transaction:records',
      'transaction:records:view',
      'transaction:records:add',
      'transaction:records:edit',
      'transaction:records:delete',
      'transaction:records:export',
      'transaction:stats',
      'transaction:stats:view',
      'transaction:stats:export',
      'transaction:split',
      'transaction:split:view',
      'transaction:split:add',
      'transaction:split:edit',
      'transaction:split:delete',
      
      // 收益统计
      'profit',
      'profit:stats',
      'profit:stats:view',
      'profit:overview',
      'profit:overview:view',
      'profit:overview:export',
      'profit:details',
      'profit:details:view',
      'profit:details:export',
      
      // 汇率管理
      'exchange',
      'exchange:rates',
      'exchange:rates:view',
      'exchange:rates:add',
      'exchange:rates:edit',
      'exchange:rates:delete',
      'exchange:converter',
      'exchange:converter:use',
      
      // 系统管理
      'system',
      'system:user',
      'system:user:view',
      'system:user:add',
      'system:user:edit',
      'system:user:delete',
      'system:user:assign',
      'system:role',
      'system:role:view',
      'system:role:add',
      'system:role:edit',
      'system:role:delete',
      'system:role:assign',
      'system:permission',
      'system:permission:view',
      'system:permission:add',
      'system:permission:edit',
      'system:permission:delete',
      'system:settings',
      'system:settings:view',
      'system:settings:edit',
      'system:holder',
      'system:holder:view',
      'system:holder:add',
      'system:holder:edit',
      'system:holder:delete'
    ]
    
    // 设置角色
    roles.value = ['admin']
    loaded.value = true
    console.log('管理员权限设置完成')
  }

  // 设置默认权限
  const setDefaultPermissions = () => {
    // 默认只设置基本权限
    console.log('设置默认权限（基本权限）')
    permissions.value = []
    roles.value = []
    loaded.value = true
  }

  // 检查是否有指定权限
  const hasPermission = (permission) => {
    // 如果没有传入权限标识，或者权限列表为空，则返回 false
    if (!permission || permissions.value.length === 0) {
      console.log('权限检查失败:', permission, '权限列表为空或未指定权限')
      return false
    }
    
    // 检查是否包含指定权限
    const result = permissions.value.some(p => {
      // 处理权限对象或字符串
      const permCode = typeof p === 'string' ? p : p.code
      return permCode === permission
    })
    console.log('权限检查:', permission, result ? '通过' : '未通过')
    return result
  }

  // 检查是否有指定角色
  const hasRole = (role) => {
    // 如果没有传入角色标识，或者角色列表为空，则返回 false
    if (!role || roles.value.length === 0) {
      console.log('角色检查失败:', role, '角色列表为空或未指定角色')
      return false
    }
    
    // 检查是否包含指定角色
    const result = roles.value.some(r => {
      // 处理角色对象或字符串
      const roleName = typeof r === 'string' ? r : r.name
      return roleName === role
    })
    console.log('角色检查:', role, result ? '通过' : '未通过')
    return result
  }

  // 重置权限状态
  const resetPermissions = () => {
    console.log('重置权限状态')
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
    resetPermissions,
    setAdminPermissions,
    setDefaultPermissions
  }
}) 