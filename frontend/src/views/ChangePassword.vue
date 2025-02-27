<template>
  <div class="container mt-4">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card shadow-sm">
          <div class="card-body p-4">
            <h4 class="text-center mb-4">修改密码</h4>
            
            <!-- 成功提示 -->
            <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
              {{ success }}
              <button type="button" class="btn-close" @click="success = ''"></button>
            </div>
            
            <!-- 错误提示 -->
            <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
              {{ error }}
              <button type="button" class="btn-close" @click="error = ''"></button>
            </div>

            <form @submit.prevent="handleChangePassword">
              <!-- 当前密码 -->
              <div class="form-floating mb-3">
                <input 
                  type="password" 
                  class="form-control" 
                  id="currentPassword" 
                  v-model="form.currentPassword"
                  placeholder="当前密码"
                  required
                  :disabled="loading"
                >
                <label for="currentPassword">当前密码</label>
              </div>

              <!-- 新密码 -->
              <div class="form-floating mb-3">
                <input 
                  type="password" 
                  class="form-control" 
                  id="newPassword" 
                  v-model="form.newPassword"
                  placeholder="新密码"
                  required
                  :disabled="loading"
                >
                <label for="newPassword">新密码</label>
              </div>

              <!-- 确认新密码 -->
              <div class="form-floating mb-4">
                <input 
                  type="password" 
                  class="form-control" 
                  id="confirmPassword" 
                  v-model="form.confirmPassword"
                  placeholder="确认新密码"
                  required
                  :disabled="loading"
                >
                <label for="confirmPassword">确认新密码</label>
                <div v-if="passwordMismatch" class="text-danger mt-1 small">
                  两次输入的新密码不一致
                </div>
              </div>

              <!-- 按钮 -->
              <div class="d-grid gap-2">
                <button 
                  type="submit" 
                  class="btn btn-primary"
                  :disabled="loading || !isFormValid"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  {{ loading ? '提交中...' : '修改密码' }}
                </button>
                
                <router-link 
                  :to="{ name: 'Home' }" 
                  class="btn btn-outline-secondary"
                  :disabled="loading"
                >
                  返回首页
                </router-link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import useMessage from '../composables/useMessage'

const router = useRouter()
const message = useMessage()

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

// 检查两次输入的密码是否一致
const passwordMismatch = computed(() => {
  return form.newPassword && form.confirmPassword && 
         form.newPassword !== form.confirmPassword
})

// 表单验证
const isFormValid = computed(() => {
  return form.currentPassword && 
         form.newPassword && 
         form.confirmPassword && 
         form.newPassword === form.confirmPassword
})

const handleChangePassword = async () => {
  if (loading.value) return
  
  // 清除提示信息
  error.value = ''
  success.value = ''
  
  // 验证表单
  if (!isFormValid.value) {
    if (passwordMismatch.value) {
      error.value = '两次输入的新密码不一致'
    } else {
      error.value = '请填写所有必填字段'
    }
    return
  }
  
  loading.value = true
  
  try {
    const response = await axios.post('/api/auth/change_password', {
      current_password: form.currentPassword,
      new_password: form.newPassword
    })
    
    if (response.data.success) {
      success.value = '密码修改成功'
      message.success('密码修改成功')
      
      // 清空表单
      form.currentPassword = ''
      form.newPassword = ''
      form.confirmPassword = ''
    } else {
      error.value = response.data.message || '密码修改失败'
    }
  } catch (err) {
    console.error('密码修改失败:', err)
    error.value = err.response?.data?.message || '密码修改失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card {
  border: none;
  border-radius: 10px;
}

.form-floating > label {
  color: #6c757d;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.alert {
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.spinner-border {
  width: 1rem;
  height: 1rem;
}
</style> 