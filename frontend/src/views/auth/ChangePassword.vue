<template>
  <div class="change-password-container">
    <div class="card">
      <div class="card-header">
        <h2>修改密码</h2>
      </div>
      <div class="card-body">
        <form @submit.prevent="changePassword">
          <div class="mb-3">
            <label for="currentPassword" class="form-label">当前密码</label>
            <input 
              type="password" 
              class="form-control" 
              id="currentPassword" 
              v-model="passwordForm.currentPassword"
              required
            >
          </div>
          <div class="mb-3">
            <label for="newPassword" class="form-label">新密码</label>
            <input 
              type="password" 
              class="form-control" 
              id="newPassword" 
              v-model="passwordForm.newPassword"
              required
            >
            <div class="form-text">密码长度至少为8个字符，包含字母和数字</div>
          </div>
          <div class="mb-3">
            <label for="confirmPassword" class="form-label">确认新密码</label>
            <input 
              type="password" 
              class="form-control" 
              id="confirmPassword" 
              v-model="passwordForm.confirmPassword"
              required
            >
          </div>
          <div v-if="errorMessage" class="alert alert-danger">
            {{ errorMessage }}
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '修改密码' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useMessage } from '../../composables/useMessage'

const router = useRouter()
const { success, error } = useMessage()

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errorMessage = ref('')
const isSubmitting = ref(false)

const changePassword = async () => {
  // 重置错误信息
  errorMessage.value = ''
  
  // 验证表单
  if (passwordForm.value.newPassword.length < 8) {
    errorMessage.value = '新密码长度至少为8个字符'
    return
  }
  
  if (!/[a-zA-Z]/.test(passwordForm.value.newPassword) || 
      !/[0-9]/.test(passwordForm.value.newPassword)) {
    errorMessage.value = '新密码必须包含字母和数字'
    return
  }
  
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    errorMessage.value = '两次输入的新密码不一致'
    return
  }
  
  // 提交修改密码请求
  isSubmitting.value = true
  
  try {
    await axios.post('/api/auth/change-password', {
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    
    success('密码修改成功，请重新登录')
    
    // 清除登录状态，重定向到登录页
    localStorage.removeItem('token')
    router.push('/login')
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message
    } else {
      errorMessage.value = '修改密码失败，请稍后重试'
    }
    error(errorMessage.value)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.change-password-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 0 15px;
}

.card {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  background-color: #f8f9fa;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.card-body {
  padding: 30px;
}

.btn-primary {
  width: 100%;
  padding: 10px;
  margin-top: 10px;
}
</style> 