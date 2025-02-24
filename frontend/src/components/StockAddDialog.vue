<template>
  <div v-if="modelValue">
    <div class="modal fade" :class="{ show: modelValue }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">添加新股票</h5>
            <button type="button" class="btn-close" @click="handleClose"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label class="form-label">股票代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.code"
                  :class="{ 'is-invalid': errors.code }"
                  placeholder="输入股票代码后将自动查询股票信息"
                  @keydown.enter.prevent="handleCodeEnter"
                  @keydown.tab.prevent="handleCodeEnter"
                />
                <div class="invalid-feedback">{{ errors.code }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label">市场</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.market"
                  :class="{ 'is-invalid': errors.market }"
                  readonly
                />
                <div class="invalid-feedback">{{ errors.market }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label">股票名称</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.name"
                  :class="{ 'is-invalid': errors.name }"
                  readonly
                />
                <div class="invalid-feedback">{{ errors.name }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label">谷歌查询代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.google_code"
                  readonly
                />
              </div>

              <div class="mb-3">
                <label class="form-label">当前股价</label>
                <input 
                  type="text" 
                  class="form-control" 
                  :value="form.current_price"
                  readonly
                />
                <div v-if="alertMessage" :class="{ 
                    'text-danger': alertMessage.includes('已存在'), 
                    'text-primary': alertMessage.includes('查询失败')
                  }">
                  {{ alertMessage }}
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="handleSubmit"
              :disabled="submitting"
            >
              确认添加
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import axios from 'axios'
import useMessage from '../composables/useMessage'

const props = defineProps({
  modelValue: Boolean,
  editData: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])
const message = useMessage()

const submitting = ref(false)
const errors = ref({})
const alertMessage = ref('')

// 表单数据
const form = ref({
  market: '',
  code: '',
  name: '',
  google_code: '',
  current_price: null
})

// 添加股票代码格式化函数
const formatStockCode = (code, market = '') => {
  // 如果是港股市场，进行数字格式化
  if (market === 'HK' || market.includes('HKG')) {
    // 移除所有非数字字符
    const numericCode = code.replace(/\D/g, '')
    // 统一补齐4位
    return numericCode.padStart(4, '0')
  }
  // 非港股市场，保持原样
  return code.trim()
}

const resetFormExceptCode = () => {
  const currentCode = form.value.code
  form.value = {
    market: '',
    code: currentCode,
    name: '',
    google_code: '',
    current_price: null
  }
  errors.value = {}
}

// 添加计算属性判断是否是错误消息
const isErrorMessage = computed(() => {
  return alertMessage.value && (
    alertMessage.value.includes('已存在') ||
    alertMessage.value.includes('添加失败')
  )
})

// 在 script 部分添加
const displayPrice = computed(() => {
  return form.value.current_price || ''
})

// 处理股票代码回车和Tab事件
const handleCodeEnter = async (event) => {
  event.preventDefault()
  if (!form.value.code) {
    return
  }
  
  errors.value = {}
  alertMessage.value = ''
  
  let queryCode = form.value.code.trim()
  
  try {
    // 使用 search_stock 接口遍历不同市场
    const response = await axios.get(`/api/stock/search_stock?code=${queryCode}`)
    
    if (response.data.success && response.data.data.length > 0) {
      const stockData = response.data.data[0] // 使用第一个匹配结果
      
      // 检查是否已存在
      const checkResponse = await axios.get('/api/stock/stocks', {
        params: {
          search: stockData.code
        }
      })
      
      if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
        const existingStock = checkResponse.data.data.items.find(
          stock => stock.code === stockData.code && stock.market === stockData.market
        )
        if (existingStock) {
          alertMessage.value = '该股票代码已存在'
          resetFormExceptCode()
          const codeInput = document.querySelector('.modal-body input[type="text"]')
          if (codeInput) {
            codeInput.focus()
          }
          return
        }
      }

      // 更新表单数据
      form.value.current_price = stockData.price
      form.value.google_code = stockData.query
      form.value.name = stockData.name || ''
      form.value.market = stockData.market
      form.value.code = stockData.code
      
      if (!form.value.name) {
        errors.value.name = '未能获取公司名称'
      }
      
      // 将焦点设置到确认添加按钮
      const submitButton = document.querySelector('.modal-footer .btn-primary')
      if (submitButton) {
        submitButton.focus()
      }
    } else {
      alertMessage.value = '未找到股票信息，请检查股票代码是否正确'
      resetFormExceptCode()
      const codeInput = document.querySelector('.modal-body input[type="text"]')
      if (codeInput) {
        codeInput.focus()
      }
    }
  } catch (error) {
    alertMessage.value = '查询失败，请检查股票代码是否正确'
    resetFormExceptCode()
    const codeInput = document.querySelector('.modal-body input[type="text"]')
    if (codeInput) {
      codeInput.focus()
    }
  }
}

// 监听股票代码变化
watch(() => form.value.code, (newCode) => {
  if (!newCode) {
    resetForm()
  }
})

// 重置表单
const resetForm = () => {
  form.value = {
    market: '',
    code: '',
    name: '',
    google_code: '',
    current_price: null
  }
  errors.value = {}
  alertMessage.value = ''
}

// 表单验证
const validateForm = () => {
  errors.value = {}
  let isValid = true

  if (!form.value.code) {
    errors.value.code = '请输入股票代码'
    isValid = false
  }
  if (!form.value.market) {
    errors.value.market = '无法确定股票市场'
    isValid = false
  }
  if (!form.value.name) {
    errors.value.name = '未能获取股票名称'
    isValid = false
  }
  if (!form.value.current_price) {
    errors.value.code = '未能获取股票价格，请确认股票代码是否正确'
    isValid = false
  }

  // 检查股票代码格式
  if (form.value.code) {
    if (form.value.market === 'HK' && !/^\d{1,4}$/.test(form.value.code)) {
      errors.value.code = '港股代码必须为1-4位数字'
      isValid = false
    } else if (form.value.market === 'USA' && !/^[A-Za-z]{1,5}$/.test(form.value.code)) {
      errors.value.code = '美股代码必须为1-5位字母'
      isValid = false
    }
  }

  return isValid
}

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
  resetForm()
}

// 提交表单
const handleSubmit = async () => {
  if (!validateForm() || submitting.value) return

  submitting.value = true
  
  try {
    // 再次检查股票是否已存在
    const formattedCode = formatStockCode(form.value.code, form.value.market)
    const checkResponse = await axios.get('/api/stock/stocks', {
      params: {
        search: formattedCode
      }
    })
    
    if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
      const existingStock = checkResponse.data.data.items.find(
        stock => stock.code === formattedCode
      )
      if (existingStock) {
        message.warning('该股票代码已存在')
        form.value.current_price = null
        submitting.value = false
        return
      }
    }

    const stock = {
      code: formattedCode,
      market: form.value.market,
      name: form.value.name,
      full_name: form.value.name,
      currency: form.value.market === 'HK' ? 'HKD' : 'USD'
    }
    
    const response = await axios.post('/api/stock/stocks', stock)
    
    if (response.data.success) {
      message.success('股票添加成功')
      emit('success', response.data.data)
      handleClose()
    } else {
      message.error(response.data.message || '添加股票失败')
      form.value.current_price = null
    }
  } catch (error) {
    message.error(error.response?.data?.message || '添加失败，请稍后重试')
    form.value.current_price = null
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1055;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.modal.show {
  pointer-events: auto;
}

.modal-dialog {
  max-width: 500px;
  margin: 1.75rem auto;
  position: relative;
  width: 100%;
  z-index: 1056;
  pointer-events: auto;
}

.modal-content {
  position: relative;
  background-color: #fff;
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  width: 100%;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h5 {
  font-size: 1rem;
  margin: 0;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 0.75rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1054;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.form-control,
.form-select {
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-color: #dee2e6;
  border-radius: 0.25rem;
}

.form-control:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.form-control::placeholder {
  color: #adb5bd;
  font-size: 0.875rem;
}

.invalid-feedback {
  font-size: 0.75rem;
  color: #dc3545;
  margin-top: 0.25rem;
}

.btn {
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
}

.btn-close {
  padding: 0.5rem;
  margin: -0.5rem -0.5rem -0.5rem auto;
  font-size: 1rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.text-danger {
  color: #dc3545 !important;
}

.text-primary {
  color: #0d6efd !important;
}
</style> 