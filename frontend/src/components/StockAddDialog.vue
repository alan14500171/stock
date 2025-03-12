<template>
  <teleport to="body">
    <div v-if="modelValue" class="stock-add-dialog-wrapper">
      <div class="stock-add-dialog-backdrop" @click="handleClose"></div>
      <div class="stock-add-dialog">
        <div class="stock-add-dialog-header">
          <h5 class="stock-add-dialog-title">{{ editData ? '编辑股票' : '添加新股票' }}</h5>
          <button type="button" class="stock-add-dialog-close" @click="handleClose">&times;</button>
        </div>
        <div class="stock-add-dialog-body" v-permission="editData ? 'stock:list:edit' : 'stock:list:add'">
          <form @submit.prevent="handleSubmit">
            <div class="form-group">
              <label class="form-label">股票代码</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="form.code"
                :class="{ 'is-invalid': errors.code }"
                placeholder="输入股票代码后将自动查询股票信息"
                @keydown.enter.prevent="handleCodeEnter"
                @keydown.tab.prevent="handleCodeEnter"
                @blur="debouncedHandleCodeBlur"
                :readonly="!!editData"
                ref="codeInput"
              />
              <div class="invalid-feedback">{{ errors.code }}</div>
            </div>

            <div class="form-group">
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

            <div class="form-group">
              <label class="form-label">股票名称</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="form.code_name"
                :class="{ 'is-invalid': errors.code_name }"
                :readonly="!editData"
              />
              <div class="invalid-feedback">{{ errors.code_name }}</div>
            </div>

            <div class="form-group">
              <label class="form-label">谷歌查询代码</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="form.google_code"
                :readonly="!editData"
              />
            </div>

            <div class="form-group">
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
                }"
              >
                {{ alertMessage }}
              </div>
            </div>
          </form>
        </div>
        <div class="stock-add-dialog-footer">
          <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="handleSubmit"
            :disabled="submitting || isProcessing"
            v-permission="editData ? 'stock:list:edit' : 'stock:list:add'"
          >
            <span v-if="submitting || isProcessing" class="spinner-border spinner-border-sm me-1"></span>
            {{ editData ? '保存修改' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'

// 添加防抖函数
const debounce = (fn, delay) => {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

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
const stockSelected = ref(false)
const isProcessing = ref(false) // 添加处理状态标志
const lastFetchedCode = ref('') // 添加一个变量来跟踪最后一次查询的代码

// 表单数据
const form = ref({
  market: '',
  code: '',
  code_name: '',
  google_code: '',
  current_price: null
})

// 添加一个缓存对象来存储已查询过的股票信息
const stockInfoCache = ref({});

const resetFormExceptCode = () => {
  const currentCode = form.value.code;
  errors.value = {};
  alertMessage.value = '';
  
  // 只重置其他字段，保留代码
  form.value = {
    market: '',
    code: currentCode,
    code_name: '',
    google_code: '',
    current_price: null
  };
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
  event.preventDefault();
  if (!form.value.code || isProcessing.value) {
    return;
  }
  
  // 如果代码没有变化，不要重新查询
  if (stockSelected.value && form.value.code.trim() === form.value.code) {
    return;
  }
  
  await fetchStockInfo();
}

// 处理股票代码失去焦点事件
const handleCodeBlur = async () => {
  // 如果没有代码，或者正在处理中，或者代码只有空格，则不执行查询
  if (!form.value.code || isProcessing.value || !form.value.code.trim()) {
    return;
  }
  
  // 如果已经选择了股票且代码没有变化，不要重新查询
  if (stockSelected.value && props.editData && form.value.code === props.editData.code) {
    return;
  }
  
  // 如果已经选择了股票且代码没有变化，不要重新查询
  if (stockSelected.value && form.value.code_name) {
    return;
  }
  
  // 如果这个代码已经查询过了，不要重新查询
  if (lastFetchedCode.value === form.value.code.trim()) {
    return;
  }
  
  await fetchStockInfo();
}

// 创建防抖版本的handleCodeBlur
const debouncedHandleCodeBlur = debounce(handleCodeBlur, 300);

// 提取股票信息查询逻辑到单独的函数
const fetchStockInfo = async () => {
  if (isProcessing.value) {
    return;
  }
  
  const stockCode = form.value.code.trim();
  
  // 如果代码为空，不执行查询
  if (!stockCode) {
    return;
  }
  
  // 如果这个代码已经查询过了，不要重新查询
  if (lastFetchedCode.value === stockCode) {
    return;
  }
  
  // 更新最后查询的代码
  lastFetchedCode.value = stockCode;
  
  // 如果缓存中已有该股票信息，直接使用缓存
  if (stockInfoCache.value[stockCode]) {
    const cachedData = stockInfoCache.value[stockCode];
    
    // 如果缓存显示股票已存在，显示提示信息
    if (cachedData.exists) {
      alertMessage.value = '该股票代码已存在';
      resetFormExceptCode();
      return;
    }
    
    // 使用缓存数据填充表单
    form.value.current_price = cachedData.price;
    form.value.google_code = cachedData.google_code;
    form.value.code_name = cachedData.code_name;
    form.value.market = cachedData.market;
    stockSelected.value = true;
    return;
  }
  
  // 设置处理中状态
  isProcessing.value = true;
  
  try {
    // 查询股票信息
    const response = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(stockCode)}&_t=${Date.now()}`);
    
    // 如果在请求过程中对话框已关闭，则不处理响应
    if (!props.modelValue) {
      isProcessing.value = false;
      return;
    }
    
    // 如果在请求过程中代码已经改变，则不处理响应
    if (stockCode !== form.value.code.trim()) {
      isProcessing.value = false;
      return;
    }
    
    if (response.data.success && response.data.data.length > 0) {
      const stockData = response.data.data[0];
      stockData.market = stockData.market === 'HK' || stockData.exchange === 'HKG' ? 'HK' : 'USA';

      // 检查股票是否已存在
      const checkResponse = await axios.get('/api/stock/stocks', {
        params: {
          search: stockCode,
          _t: Date.now() // 添加时间戳防止缓存
        }
      });
      
      // 如果在请求过程中对话框已关闭，则不处理响应
      if (!props.modelValue) {
        isProcessing.value = false;
        return;
      }
      
      // 如果在请求过程中代码已经改变，则不处理响应
      if (stockCode !== form.value.code.trim()) {
        isProcessing.value = false;
        return;
      }
      
      if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
        const existingStock = checkResponse.data.data.items.find(
          stock => stock.code === stockCode
        );
        if (existingStock) {
          // 缓存该股票已存在的信息
          stockInfoCache.value[stockCode] = { exists: true };
          alertMessage.value = '该股票代码已存在';
          resetFormExceptCode();
          return;
        }
      }

      // 更新表单数据,保持原始代码
      form.value.current_price = stockData.price;
      form.value.google_code = stockData.query;
      form.value.code_name = stockData.code_name || stockData.name || '';
      form.value.market = stockData.market;
      
      // 缓存查询结果
      stockInfoCache.value[stockCode] = {
        exists: false,
        price: stockData.price,
        google_code: stockData.query,
        code_name: stockData.code_name || stockData.name || '',
        market: stockData.market
      };
      
      if (form.value.code_name) {
        stockSelected.value = true;
      } else {
        errors.value.code_name = '未能获取公司名称';
      }
    } else {
      alertMessage.value = '未找到股票信息，请检查股票代码是否正确';
      resetFormExceptCode();
    }
  } catch (error) {
    console.error('查询股票信息失败:', error);
    alertMessage.value = '查询失败，请检查股票代码是否正确';
    resetFormExceptCode();
  } finally {
    isProcessing.value = false; // 重置处理状态
  }
}

// 监听股票代码变化，使用防抖减少触发频率
const debouncedCodeWatcher = debounce((newCode, oldCode) => {
  if (!newCode) {
    resetForm();
  } else if (stockSelected.value && newCode !== oldCode) {
    // 只有当代码真正变化时才重置选择状态
    stockSelected.value = false;
    // 重置最后查询的代码，以便可以重新查询
    lastFetchedCode.value = '';
  }
}, 300);

watch(() => form.value.code, debouncedCodeWatcher);

// 监听模态框显示状态
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    // 模态框打开时，重置处理状态
    isProcessing.value = false;
    lastFetchedCode.value = '';
    
    // 如果是添加模式，聚焦到代码输入框
    if (!props.editData) {
      nextTick(() => {
        if (codeInput.value) {
          codeInput.value.focus();
        }
      });
    }
    
    // 防止滚动
    document.body.style.overflow = 'hidden';
  } else {
    // 模态框关闭时重置表单
    resetForm();
    
    // 恢复滚动
    document.body.style.overflow = '';
  }
});

// 重置表单
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
  // 清除缓存
  stockInfoCache.value = {}
}

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

// 监听 editData 变化
watch(() => props.editData, (newData) => {
  if (newData) {
    // 直接使用原始数据,不做任何格式处理
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

// 修改提交表单方法
const handleSubmit = async () => {
  if (!validateForm() || submitting.value || isProcessing.value) return
  
  try {
    submitting.value = true
    
    // 确保所有必要字段都存在且不为空
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
    console.error('提交失败:', error)
    message.error(error.message || '操作失败，请重试')
    errors.value.code_name = error.message
  } finally {
    submitting.value = false
  }
}

// 引用代码输入框
const codeInput = ref(null)

// 在组件挂载时添加事件监听
onMounted(() => {
  // 添加键盘事件监听，按ESC关闭对话框
  const handleKeyDown = (event) => {
    if (event.key === 'Escape' && props.modelValue) {
      handleClose()
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  // 在组件卸载前移除事件监听
  return () => {
    document.removeEventListener('keydown', handleKeyDown)
  }
})
</script>

<style scoped>
.stock-add-dialog-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.stock-add-dialog-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 2001;
}

.stock-add-dialog {
  position: relative;
  width: 100%;
  max-width: 500px;
  margin: 1.75rem auto;
  background-color: #fff;
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  z-index: 2002;
}

.stock-add-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.stock-add-dialog-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 500;
}

.stock-add-dialog-close {
  background: transparent;
  border: 0;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
  color: #000;
  opacity: 0.5;
  padding: 0;
  cursor: pointer;
}

.stock-add-dialog-close:hover {
  opacity: 0.75;
}

.stock-add-dialog-body {
  padding: 1rem;
}

.stock-add-dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding: 0.75rem;
  border-top: 1px solid #dee2e6;
  gap: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
}

.form-control {
  display: block;
  width: 100%;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #495057;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
  color: #495057;
  background-color: #fff;
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-control:disabled,
.form-control[readonly] {
  background-color: #e9ecef;
  opacity: 1;
}

.is-invalid {
  border-color: #dc3545;
}

.is-invalid:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.invalid-feedback {
  display: block;
  width: 100%;
  margin-top: 0.25rem;
  font-size: 80%;
  color: #dc3545;
}

.btn {
  display: inline-block;
  font-weight: 400;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  user-select: none;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  border-radius: 0.25rem;
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-primary {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  color: #fff;
  background-color: #0069d9;
  border-color: #0062cc;
}

.btn-primary:focus {
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.5);
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-secondary:hover {
  color: #fff;
  background-color: #5a6268;
  border-color: #545b62;
}

.btn-secondary:focus {
  box-shadow: 0 0 0 0.2rem rgba(108, 117, 125, 0.5);
}

.spinner-border {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  vertical-align: text-bottom;
  border: 0.2em solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spinner-border 0.75s linear infinite;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
  border-width: 0.2em;
}

.me-1 {
  margin-right: 0.25rem;
}

.text-danger {
  color: #dc3545;
}

.text-primary {
  color: #007bff;
}

@keyframes spinner-border {
  to {
    transform: rotate(360deg);
  }
}
</style> 