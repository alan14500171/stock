<template>
  <teleport to="body">
    <div v-if="modelValue" class="stock-add-dialog-overlay">
      <div class="stock-add-dialog-container">
        <div class="stock-add-dialog-header">
          <h5 class="stock-add-dialog-title">{{ editData ? '编辑股票' : '添加新股票' }}</h5>
          <button type="button" class="stock-add-dialog-close" @click="handleClose">&times;</button>
        </div>
        
        <div class="stock-add-dialog-body" v-permission="editData ? 'stock:list:edit' : 'stock:list:add'">
          <div v-if="isProcessing" class="stock-add-dialog-loading">
            <div class="spinner"></div>
            <p>正在查询股票信息...</p>
          </div>
          
          <form v-else @submit.prevent="handleSubmit">
            <div class="form-group">
              <label>股票代码</label>
              <input 
                type="text" 
                v-model="form.code"
                :class="{ 'is-invalid': errors.code }"
                placeholder="输入股票代码后将自动查询股票信息"
                @keydown.enter.prevent="handleCodeEnter"
                @keydown.tab.prevent="handleCodeEnter"
                @blur="handleCodeBlur"
                :readonly="!!editData"
                ref="codeInput"
              />
              <div class="error-message" v-if="errors.code">{{ errors.code }}</div>
            </div>

            <div class="form-group">
              <label>市场</label>
              <input 
                type="text" 
                v-model="form.market"
                :class="{ 'is-invalid': errors.market }"
                readonly
              />
              <div class="error-message" v-if="errors.market">{{ errors.market }}</div>
            </div>

            <div class="form-group">
              <label>股票名称</label>
              <input 
                type="text" 
                v-model="form.code_name"
                :class="{ 'is-invalid': errors.code_name }"
                :readonly="!editData"
              />
              <div class="error-message" v-if="errors.code_name">{{ errors.code_name }}</div>
            </div>

            <div class="form-group">
              <label>谷歌查询代码</label>
              <input 
                type="text" 
                v-model="form.google_code"
                :readonly="!editData"
              />
            </div>

            <div class="form-group">
              <label>当前股价</label>
              <input 
                type="text" 
                :value="form.current_price"
                readonly
              />
              <div v-if="alertMessage" :class="{ 
                  'text-danger': alertMessage.includes('已存在'), 
                  'text-primary': alertMessage.includes('查询失败')
                }"
              >
                {{ alertMessage }}
              </div>
            </div>
          </form>
        </div>
        
        <div class="stock-add-dialog-footer">
          <button type="button" class="btn-secondary" @click="handleClose">取消</button>
          <button 
            type="button" 
            class="btn-primary" 
            @click="handleSubmit"
            :disabled="submitting || isProcessing"
            v-permission="editData ? 'stock:list:edit' : 'stock:list:add'"
          >
            <span v-if="submitting || isProcessing" class="spinner-sm"></span>
            {{ editData ? '保存修改' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'

const props = defineProps({
  modelValue: Boolean,
  editData: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])
const message = useMessage()

// 状态变量
const submitting = ref(false)
const errors = ref({})
const alertMessage = ref('')
const stockSelected = ref(false)
const isProcessing = ref(false)
const lastFetchedCode = ref('')
const codeInput = ref(null)

// 表单数据
const form = ref({
  market: '',
  code: '',
  code_name: '',
  google_code: '',
  current_price: null
})

// 缓存对象
const stockInfoCache = ref({})

// 重置表单，保留代码
const resetFormExceptCode = () => {
  const currentCode = form.value.code
  errors.value = {}
  alertMessage.value = ''
  
  form.value = {
    market: '',
    code: currentCode,
    code_name: '',
    google_code: '',
    current_price: null
  }
}

// 完全重置表单
const resetForm = () => {
  form.value = {
    market: '',
    code: '',
    code_name: '',
    google_code: '',
    current_price: null
  }
  errors.value = {}
  alertMessage.value = ''
  stockSelected.value = false
  lastFetchedCode.value = ''
  stockInfoCache.value = {}
}

// 处理回车和Tab事件
const handleCodeEnter = async (event) => {
  event.preventDefault()
  
  if (!form.value.code || isProcessing.value) {
    return
  }
  
  if (stockSelected.value && form.value.code.trim() === form.value.code) {
    return
  }
  
  await fetchStockInfo()
}

// 处理失去焦点事件
const handleCodeBlur = async () => {
  // 使用setTimeout确保在所有其他事件处理完成后执行
  setTimeout(async () => {
    if (!form.value.code || isProcessing.value || !form.value.code.trim()) {
      return
    }
    
    if (stockSelected.value && props.editData && form.value.code === props.editData.code) {
      return
    }
    
    if (stockSelected.value && form.value.code_name) {
      return
    }
    
    if (lastFetchedCode.value === form.value.code.trim()) {
      return
    }
    
    await fetchStockInfo()
  }, 300)
}

// 查询股票信息
const fetchStockInfo = async () => {
  if (isProcessing.value) {
    return
  }
  
  const stockCode = form.value.code.trim()
  
  if (!stockCode) {
    return
  }
  
  if (lastFetchedCode.value === stockCode) {
    return
  }
  
  // 设置处理中状态
  isProcessing.value = true
  lastFetchedCode.value = stockCode
  
  // 使用缓存
  if (stockInfoCache.value[stockCode]) {
    const cachedData = stockInfoCache.value[stockCode]
    
    if (cachedData.exists) {
      alertMessage.value = '该股票代码已存在'
      resetFormExceptCode()
      isProcessing.value = false
      return
    }
    
    form.value.current_price = cachedData.price
    form.value.google_code = cachedData.google_code
    form.value.code_name = cachedData.code_name
    form.value.market = cachedData.market
    stockSelected.value = true
    isProcessing.value = false
    return
  }
  
  try {
    // 查询股票信息
    const response = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(stockCode)}&_t=${Date.now()}`)
    
    // 检查对话框是否已关闭或代码已改变
    if (!props.modelValue || stockCode !== form.value.code.trim()) {
      isProcessing.value = false
      return
    }
    
    if (response.data.success && response.data.data.length > 0) {
      const stockData = response.data.data[0]
      stockData.market = stockData.market === 'HK' || stockData.exchange === 'HKG' ? 'HK' : 'USA'

      try {
        // 检查股票是否已存在
        const checkResponse = await axios.get('/api/stock/stocks', {
          params: {
            search: stockCode,
            _t: Date.now()
          }
        })
        
        // 再次检查对话框是否已关闭或代码已改变
        if (!props.modelValue || stockCode !== form.value.code.trim()) {
          isProcessing.value = false
          return
        }
        
        if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
          const existingStock = checkResponse.data.data.items.find(
            stock => stock.code === stockCode
          )
          
          if (existingStock) {
            stockInfoCache.value[stockCode] = { exists: true }
            alertMessage.value = '该股票代码已存在'
            resetFormExceptCode()
            isProcessing.value = false
            return
          }
        }

        // 更新表单数据
        form.value.current_price = stockData.price
        form.value.google_code = stockData.query
        form.value.code_name = stockData.code_name || stockData.name || ''
        form.value.market = stockData.market
        
        // 缓存查询结果
        stockInfoCache.value[stockCode] = {
          exists: false,
          price: stockData.price,
          google_code: stockData.query,
          code_name: stockData.code_name || stockData.name || '',
          market: stockData.market
        }
        
        if (form.value.code_name) {
          stockSelected.value = true
        } else {
          errors.value.code_name = '未能获取公司名称'
        }
      } catch (checkError) {
        // 即使检查失败，仍然使用查询到的股票信息
        form.value.current_price = stockData.price
        form.value.google_code = stockData.query
        form.value.code_name = stockData.code_name || stockData.name || ''
        form.value.market = stockData.market
        stockSelected.value = true
      }
    } else {
      alertMessage.value = '未找到股票信息，请检查股票代码是否正确'
      resetFormExceptCode()
    }
  } catch (error) {
    alertMessage.value = '查询失败，请检查股票代码是否正确'
    resetFormExceptCode()
  } finally {
    isProcessing.value = false
  }
}

// 监听股票代码变化
watch(() => form.value.code, (newCode, oldCode) => {
  if (!newCode) {
    resetForm()
  } else if (stockSelected.value && newCode !== oldCode) {
    stockSelected.value = false
    lastFetchedCode.value = ''
  }
}, { flush: 'post' })

// 监听模态框显示状态
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    isProcessing.value = false
    lastFetchedCode.value = ''
    
    if (!props.editData) {
      nextTick(() => {
        if (codeInput.value) {
          codeInput.value.focus()
        }
      })
    }
    
    document.body.style.overflow = 'hidden'
  } else {
    resetForm()
    document.body.style.overflow = ''
  }
})

// 监听 editData 变化
watch(() => props.editData, (newData) => {
  if (newData) {
    form.value = {
      code: newData.code,
      market: newData.market,
      code_name: newData.code_name,
      google_code: newData.google_name,
      current_price: newData.current_price
    }
    stockSelected.value = true
    lastFetchedCode.value = newData.code
  } else {
    resetForm()
  }
}, { immediate: true })

// 表单验证
const validateForm = () => {
  errors.value = {}
  let isValid = true

  if (!form.value.code || !form.value.code.trim()) {
    errors.value.code = '请输入股票代码'
    isValid = false
  }

  if (!form.value.market || !form.value.market.trim()) {
    errors.value.market = '请选择市场'
    isValid = false
  }

  if (!form.value.code_name || !form.value.code_name.trim()) {
    errors.value.code_name = '请输入股票名称'
    isValid = false
  }

  if (!form.value.google_code || !form.value.google_code.trim()) {
    errors.value.google_code = '请输入谷歌查询代码'
    isValid = false
  }

  return isValid
}

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
}

// 提交表单
const handleSubmit = async () => {
  if (!validateForm() || submitting.value || isProcessing.value) return
  
  try {
    submitting.value = true
    
    if (!form.value.code_name || !form.value.code_name.trim()) {
      throw new Error('股票名称不能为空')
    }
    
    const stock = {
      code: form.value.code.trim(),
      market: form.value.market.trim(),
      code_name: form.value.code_name.trim(),
      google_name: form.value.google_code.trim(),
      currency: form.value.market === 'HK' ? 'HKD' : 'USD'
    }
    
    const url = props.editData ? `/api/stock/stocks/${props.editData.id}` : '/api/stock/stocks'
    const method = props.editData ? 'put' : 'post'
    
    const response = await axios[method](url, stock, {
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    
    if (response.data.success) {
      message.success(props.editData ? '股票更新成功' : '股票添加成功')
      emit('success')
      handleClose()
    } else {
      throw new Error(response.data.message || '操作失败')
    }
  } catch (error) {
    message.error(error.message || '操作失败，请重试')
    errors.value.code_name = error.message
  } finally {
    submitting.value = false
  }
}

// 添加键盘事件监听
onMounted(() => {
  const handleKeyDown = (event) => {
    if (event.key === 'Escape' && props.modelValue) {
      handleClose()
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  return () => {
    document.removeEventListener('keydown', handleKeyDown)
  }
})
</script>

<style scoped>
.stock-add-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.stock-add-dialog-container {
  width: 100%;
  max-width: 500px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.stock-add-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.stock-add-dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.stock-add-dialog-close {
  background: transparent;
  border: 0;
  font-size: 24px;
  line-height: 1;
  color: #999;
  cursor: pointer;
}

.stock-add-dialog-body {
  padding: 20px;
}

.stock-add-dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 123, 255, 0.1);
  border-radius: 50%;
  border-top-color: #007bff;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.spinner-sm {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stock-add-dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #eee;
  gap: 12px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.form-group input {
  display: block;
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #495057;
  background-color: #fff;
  border: 1px solid #ced4da;
  border-radius: 4px;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-group input:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-group input[readonly] {
  background-color: #f8f9fa;
  opacity: 1;
}

.form-group input.is-invalid {
  border-color: #dc3545;
}

.error-message {
  display: block;
  width: 100%;
  margin-top: 4px;
  font-size: 12px;
  color: #dc3545;
}

.btn-primary, .btn-secondary {
  display: inline-block;
  font-weight: 400;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  user-select: none;
  border: 1px solid transparent;
  padding: 8px 16px;
  font-size: 14px;
  line-height: 1.5;
  border-radius: 4px;
  transition: all 0.15s ease-in-out;
  cursor: pointer;
}

.btn-primary {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  background-color: #0069d9;
  border-color: #0062cc;
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

.text-danger {
  color: #dc3545;
}

.text-primary {
  color: #007bff;
}
</style> </style>
