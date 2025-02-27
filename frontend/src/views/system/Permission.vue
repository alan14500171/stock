<template>
  <div class="container-fluid mt-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5>权限管理</h5>
        <div class="d-flex">
          <button 
            class="btn btn-primary" 
            @click="showAddPermissionModal" 
            v-permission="'system:permission:add'"
          >
            <i class="bi bi-plus-lg"></i> 添加权限
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>ID</th>
                <th>权限名称</th>
                <th>权限标识</th>
                <th>类型</th>
                <th>父级权限</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="permission in permissions" :key="permission.id">
                <td>{{ permission.id }}</td>
                <td>{{ permission.name }}</td>
                <td>{{ permission.code }}</td>
                <td>
                  <span 
                    :class="getTypeClass(permission.type)"
                  >
                    {{ getTypeName(permission.type) }}
                  </span>
                </td>
                <td>{{ permission.parent_name || '-' }}</td>
                <td>
                  <div class="btn-group">
                    <button 
                      class="btn btn-sm btn-outline-primary" 
                      @click="showEditPermissionModal(permission)"
                      v-permission="'system:permission:update'"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-danger" 
                      @click="confirmDeletePermission(permission)"
                      v-permission="'system:permission:delete'"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="permissions.length === 0">
                <td colspan="6" class="text-center">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 添加/编辑权限模态框 -->
    <div class="modal fade" id="permissionModal" tabindex="-1" ref="permissionModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? '编辑权限' : '添加权限' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitPermissionForm">
              <div class="mb-3">
                <label for="name" class="form-label">权限名称</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="name" 
                  v-model="permissionForm.name"
                  required
                >
              </div>
              <div class="mb-3">
                <label for="code" class="form-label">权限标识</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="code" 
                  v-model="permissionForm.code"
                  required
                >
                <div class="form-text">例如：system:user:view</div>
              </div>
              <div class="mb-3">
                <label for="type" class="form-label">权限类型</label>
                <select class="form-select" id="type" v-model="permissionForm.type">
                  <option value="1">模块</option>
                  <option value="2">菜单</option>
                  <option value="3">按钮</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="parent_id" class="form-label">父级权限</label>
                <select class="form-select" id="parent_id" v-model="permissionForm.parent_id">
                  <option value="0">无（顶级权限）</option>
                  <option 
                    v-for="parent in parentPermissions" 
                    :key="parent.id" 
                    :value="parent.id"
                  >
                    {{ parent.name }}
                  </option>
                </select>
              </div>
              <div class="text-end">
                <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div class="modal fade" id="deleteConfirmModal" tabindex="-1" ref="deleteConfirmModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>确定要删除权限 "{{ selectedPermission?.name }}" 吗？此操作不可撤销。</p>
            <div class="alert alert-warning">
              <i class="bi bi-exclamation-triangle me-2"></i>
              删除权限将同时删除其下所有子权限，且已分配给角色的权限将被移除。
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="deletePermission">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Modal } from 'bootstrap'
import { useMessage } from '@/composables/useMessage'

// 消息提示
const { success, error } = useMessage()

// 权限列表数据
const permissions = ref([])

// 模态框引用
const permissionModal = ref(null)
const deleteConfirmModal = ref(null)

// 表单数据
const permissionForm = ref({
  name: '',
  code: '',
  type: '2',
  parent_id: '0'
})

// 编辑状态
const isEditing = ref(false)
const selectedPermission = ref(null)

// 父级权限选项（排除当前编辑的权限及其子权限）
const parentPermissions = ref([])

// 加载权限列表
const loadPermissions = async () => {
  try {
    const response = await axios.get('/api/system/permission/list')
    permissions.value = response.data.data
  } catch (err) {
    error('加载权限列表失败: ' + (err.response?.data?.message || err.message))
  }
}

// 加载可选的父级权限
const loadParentPermissions = async () => {
  try {
    // 获取所有权限
    const response = await axios.get('/api/system/permission/list')
    const allPermissions = response.data.data
    
    // 如果是编辑模式，需要排除当前权限及其子权限
    if (isEditing.value && selectedPermission.value) {
      // 获取当前权限的所有子权限ID（包括自身）
      const childIds = getChildPermissionIds(allPermissions, selectedPermission.value.id)
      
      // 过滤掉子权限
      parentPermissions.value = allPermissions.filter(p => !childIds.includes(p.id))
    } else {
      parentPermissions.value = allPermissions
    }
  } catch (err) {
    error('加载父级权限失败: ' + (err.response?.data?.message || err.message))
  }
}

// 获取权限的所有子权限ID（包括自身）
const getChildPermissionIds = (permissions, parentId) => {
  const ids = [parentId]
  
  const findChildren = (parentId) => {
    permissions.forEach(p => {
      if (p.parent_id === parentId) {
        ids.push(p.id)
        findChildren(p.id)
      }
    })
  }
  
  findChildren(parentId)
  return ids
}

// 显示添加权限模态框
const showAddPermissionModal = async () => {
  isEditing.value = false
  permissionForm.value = {
    name: '',
    code: '',
    type: '2',
    parent_id: '0'
  }
  
  await loadParentPermissions()
  new Modal(permissionModal.value).show()
}

// 显示编辑权限模态框
const showEditPermissionModal = async (permission) => {
  isEditing.value = true
  selectedPermission.value = permission
  permissionForm.value = {
    id: permission.id,
    name: permission.name,
    code: permission.code,
    type: permission.type.toString(),
    parent_id: permission.parent_id.toString()
  }
  
  await loadParentPermissions()
  new Modal(permissionModal.value).show()
}

// 显示删除确认模态框
const confirmDeletePermission = (permission) => {
  selectedPermission.value = permission
  new Modal(deleteConfirmModal.value).show()
}

// 提交权限表单
const submitPermissionForm = async () => {
  try {
    if (isEditing.value) {
      // 编辑权限
      await axios.put(`/api/system/permission/update/${permissionForm.value.id}`, permissionForm.value)
      success('权限更新成功')
    } else {
      // 添加权限
      await axios.post('/api/system/permission/add', permissionForm.value)
      success('权限添加成功')
    }
    
    // 关闭模态框并刷新列表
    Modal.getInstance(permissionModal.value).hide()
    loadPermissions()
  } catch (err) {
    error('操作失败: ' + (err.response?.data?.message || err.message))
  }
}

// 删除权限
const deletePermission = async () => {
  try {
    await axios.delete(`/api/system/permission/delete/${selectedPermission.value.id}`)
    success('权限删除成功')
    
    // 关闭模态框并刷新列表
    Modal.getInstance(deleteConfirmModal.value).hide()
    loadPermissions()
  } catch (err) {
    error('删除失败: ' + (err.response?.data?.message || err.message))
  }
}

// 获取权限类型名称
const getTypeName = (type) => {
  const types = {
    1: '模块',
    2: '菜单',
    3: '按钮'
  }
  return types[type] || '未知'
}

// 获取权限类型样式
const getTypeClass = (type) => {
  const classes = {
    1: 'badge bg-primary',
    2: 'badge bg-success',
    3: 'badge bg-info'
  }
  return classes[type] || 'badge bg-secondary'
}

// 页面加载时获取数据
onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.table th {
  font-weight: 600;
}

.badge {
  font-weight: 500;
}

.btn-group .btn {
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}
</style>