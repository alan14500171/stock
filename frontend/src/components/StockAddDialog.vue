<template>
  <teleport to="body">
    <div v-if="modelValue" class="stock-dialog-backdrop" @click.self="handleClose">
      <div class="stock-dialog">
        <div class="stock-dialog-header">
          <h5 class="stock-dialog-title">{{ editData ? '编辑股票' : '添加新股票' }}</h5>
          <button type="button" class="stock-dialog-close" @click="handleClose">&times;</button>
        </div>
        
        <div class="stock-dialog-body" v-permission="editData ? 'stock:list:edit' : 'stock:list:add'">
          <div v-if="loading" class="stock-dialog-loading">
            <div class="stock-dialog-spinner"></div>
            <p>正在查询股票信息...</p>
          </div>
          
          <form v-else @submit.prevent="handleSubmit">
            <div class="form-group">
              <label>股票代码</label>
              <input 
                type="text" 
                v-model="formData.code"
                :class="{ 'is-invalid': validationErrors.code }"
                placeholder="输入股票代码后按回车键查询"
                @keydown.enter.prevent="handleCodeSearch"
                :readonly="!!editData || loading"
                ref="codeInput"
                :disabled="loading"
              />
              <div class="error-message" v-if="validationErrors.code">{{ validationErrors.code }}</div>
              <button 
                v-if="formData.code && !editData && !loading" 
                type="button" 
                class="search-button"
                @click="handleCodeSearch"
              >
                查询
              </button>
            </div>

            <div class="form-group">
              <label>市场</label>
              <input 
                type="text" 
                v-model="formData.market"
                :class="{ 'is-invalid': validationErrors.market }"
                readonly
              />
              <div class="error-message" v-if="validationErrors.market">{{ validationErrors.market }}</div>
            </div>

            <div class="form-group">
              <label>股票名称</label>
              <input 
                type="text" 
                v-model="formData.code_name"
                :class="{ 'is-invalid': validationErrors.code_name }"
                :readonly="!editData"
              />
              <div class="error-message" v-if="validationErrors.code_name">{{ validationErrors.code_name }}</div>
            </div>

            <div class="form-group">
              <label>谷歌查询代码</label>
              <input 
                type="text" 
                v-model="formData.google_code"
                :readonly="!editData"
              />
            </div>

            <div class="form-group">
              <label>当前股价</label>
              <input 
                type="text" 
                :value="formData.current_price"
                readonly
              />
              <div v-if="statusMessage" :class="{ 
                  'text-danger': statusMessage.includes('已存在'), 
                  'text-primary': statusMessage.includes('查询失败')
                }"
              >
                {{ statusMessage }}
              </div>
            </div>
          </form>
        </div>
        
        <div class="stock-dialog-footer">
          <button type="button" class="btn-secondary" @click="handleClose">取消</button>
          <button 
            type="button" 
            class="btn-primary" 
            @click="handleSubmit"
            :disabled="submitting || loading || !isFormValid"
            v-permission="editData ? 'stock:list:edit' : 'stock:list:add'"
          >
            <span v-if="submitting" class="spinner-sm"></span>
            {{ editData ? '保存修改' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
const loading = ref(false)
const validationErrors = ref({})
const statusMessage = ref('')
const codeInput = ref(null)
const stockInfoCache = ref({})

// 表单数据
const formData = ref({
  market: '',
  code: '',
  code_name: '',
  google_code: '',
  current_price: null
})

// 计算属性：表单是否有效
const isFormValid = computed(() => {
  return formData.value.code && 
         formData.value.market && 
         formData.value.code_name && 
         !Object.keys(validationErrors.value).length
})

// 重置表单
const resetForm = () => {
  formData.value = {
    market: '',
    code: '',
    code_name: '',
    google_code: '',
    current_price: null
  }
  validationErrors.value = {}
  statusMessage.value = ''
}

// 查询股票信息
const handleCodeSearch = async () => {
  const stockCode = formData.value.code.trim()
  
  if (!stockCode || loading.value) {
    return
  }
  
  // 检查缓存
  if (stockInfoCache.value[stockCode]) {
    const cachedData = stockInfoCache.value[stockCode]
    
    if (cachedData.exists) {
      statusMessage.value = '该股票代码已存在'
      return
    }
    
    formData.value.current_price = cachedData.price
    formData.value.google_code = cachedData.google_code
    formData.value.code_name = cachedData.code_name
    formData.value.market = cachedData.market
    return
  }
  
  validationErrors.value = {}
  statusMessage.value = ''
  loading.value = true
  
  try {
    // 查询股票信息
    const timestamp = Date.now()
    const response = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(stockCode)}&_t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store'
      }
    })
    
    // 检查对话框是否已关闭
    if (!props.modelValue) {
      loading.value = false
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
          },
          headers: {
            'Cache-Control': 'no-cache, no-store'
          }
        })
        
        // 再次检查对话框是否已关闭
        if (!props.modelValue) {
          loading.value = false
          return
        }
        
        if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
          const existingStock = checkResponse.data.data.items.find(
            stock => stock.code === stockCode
          )
          
          if (existingStock) {
            stockInfoCache.value[stockCode] = { exists: true }
            statusMessage.value = '该股票代码已存在'
            loading.value = false
            return
          }
        }

        // 更新表单数据
        formData.value.current_price = stockData.price
        formData.value.google_code = stockData.query
        formData.value.code_name = stockData.code_name || stockData.name || ''
        formData.value.market = stockData.market
        
        // 缓存查询结果
        stockInfoCache.value[stockCode] = {
          exists: false,
          price: stockData.price,
          google_code: stockData.query,
          code_name: stockData.code_name || stockData.name || '',
          market: stockData.market
        }
        
        if (!formData.value.code_name) {
          validationErrors.value.code_name = '未能获取公司名称'
        }
      } catch (error) {
        console.error('检查股票是否存在时出错:', error)
        // 即使检查失败，仍然使用查询到的股票信息
        formData.value.current_price = stockData.price
        formData.value.google_code = stockData.query
        formData.value.code_name = stockData.code_name || stockData.name || ''
        formData.value.market = stockData.market
      }
    } else {
      statusMessage.value = '未找到股票信息，请检查股票代码是否正确'
    }
  } catch (error) {
    console.error('查询股票信息时出错:', error)
    statusMessage.value = '查询失败，请检查股票代码是否正确'
  } finally {
    loading.value = false
  }
}

// 表单验证
const validateForm = () => {
  validationErrors.value = {}
  let isValid = true

  if (!formData.value.code || !formData.value.code.trim()) {
    validationErrors.value.code = '请输入股票代码'
    isValid = false
  }

  if (!formData.value.market || !formData.value.market.trim()) {
    validationErrors.value.market = '请选择市场'
    isValid = false
  }

  if (!formData.value.code_name || !formData.value.code_name.trim()) {
    validationErrors.value.code_name = '请输入股票名称'
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
  if (!validateForm() || submitting.value || loading.value) return
  
  try {
    submitting.value = true
    
    const stock = {
      code: formData.value.code.trim(),
      market: formData.value.market.trim(),
      code_name: formData.value.code_name.trim(),
      google_name: formData.value.google_code.trim(),
      currency: formData.value.market === 'HK' ? 'HKD' : 'USD'
    }
    
    const url = props.editData ? `/api/stock/stocks/${props.editData.id}` : '/api/stock/stocks'
    const method = props.editData ? 'put' : 'post'
    
    const response = await axios[method](url, stock, {
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache, no-store'
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
    console.error('提交表单时出错:', error)
    message.error(error.message || '操作失败，请重试')
    validationErrors.value.code_name = error.message
  } finally {
    submitting.value = false
  }
}

// 监听模态框显示状态
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    resetForm()
    
    if (props.editData) {
      formData.value = {
        code: props.editData.code,
        market: props.editData.market,
        code_name: props.editData.code_name,
        google_code: props.editData.google_name,
        current_price: props.editData.current_price
      }
    } else {
      nextTick(() => {
        if (codeInput.value) {
          codeInput.value.focus()
        }
      })
    }
    
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// 添加键盘事件监听
onMounted(() => {
  const handleKeyDown = (event) => {
    if (event.key === 'Escape' && props.modelValue) {
      handleClose()
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  // 清理函数
  onBeforeUnmount(() => {
    document.removeEventListener('keydown', handleKeyDown)
    document.body.style.overflow = ''
  })
})
</script>

<style scoped>
.stock-dialog-backdrop {
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

.stock-dialog {
  width: 100%;
  max-width: 500px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.stock-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.stock-dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.stock-dialog-close {
  background: transparent;
  border: 0;
  font-size: 24px;
  line-height: 1;
  color: #999;
  cursor: pointer;
}

.stock-dialog-body {
  padding: 20px;
  position: relative;
}

.stock-dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.stock-dialog-spinner {
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

.stock-dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #eee;
  gap: 12px;
}

.form-group {
  margin-bottom: 16px;
  position: relative;
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

.form-group input:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

.search-button {
  position: absolute;
  right: 8px;
  top: 32px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.search-button:hover {
  background-color: #0069d9;
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
</style>
