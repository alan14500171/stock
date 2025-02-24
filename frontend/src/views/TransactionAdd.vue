<template>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">添加交易记录</h5>
    </div>
    
    <div class="card-body">
      <!-- 基本信息 -->
      <div class="row mb-4">
        <div class="col-md-4">
          <label class="form-label">交易日期</label>
          <div class="date-input">
            <input
              type="text"
              class="form-control"
              v-model="form.transaction_date"
              :ref="el => inputRefs.transaction_date.value = el"
              @blur="handleDateBlur"
              @keydown="handleKeyNavigation($event, 'transaction_date')"
              :class="{ 'is-invalid': errors.transaction_date }"
              placeholder="YYYY-MM-DD"
            />
            <div class="invalid-feedback">{{ errors.transaction_date }}</div>
          </div>
        </div>

        <div class="col-md-4">
          <label class="form-label">股票代码</label>
          <div class="position-relative">
            <div class="stock-input-wrapper">
              <input
                type="text"
                class="form-control"
                v-model="form.stock_code"
                :ref="el => inputRefs.stock_code.value = el"
                @input="handleStockCodeInput"
                @keydown="handleKeyNavigation($event, 'stock_code')"
                @keydown.down.prevent="navigateStockList('down')"
                @keydown.up.prevent="navigateStockList('up')"
                @keydown.enter.prevent="handleStockSelect"
                @keydown.esc="closeStockList"
                :class="{ 'is-invalid': errors.stock_code }"
                placeholder="输入代码或名称搜索"
              />
              <span v-if="form.stock_code && form.stock_name" class="selected-stock">
                <span :class="['market-tag', form.market === 'HK' ? 'hk' : 'usa']">{{ form.market }}</span>
                {{ form.stock_code }} {{ form.stock_name }}
              </span>
            </div>
            <div class="invalid-feedback">{{ errors.stock_code }}</div>
            
            <!-- 股票搜索结果下拉列表 -->
            <div v-if="showStockList && filteredStocks.length > 0" class="stock-list">
              <a
                v-for="(stock, index) in filteredStocks"
                :key="stock.code"
                href="#"
                class="stock-item"
                :class="{ 'active': index === currentStockIndex }"
                @click.prevent="selectStock(stock)"
                @mouseover="currentStockIndex = index"
              >
                <span :class="['market-tag', stock.market === 'HK' ? 'hk' : 'usa']">{{ stock.market }}</span>
                {{ stock.code }} - {{ stock.name }}
              </a>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <label class="form-label">交易编号</label>
          <input
            type="text"
            class="form-control"
            v-model="form.transaction_code"
            :ref="el => inputRefs.transaction_code.value = el"
            @input="handleTransactionCodeInput"
            @blur="handleTransactionCodeBlur"
            @keydown="handleKeyNavigation($event, 'transaction_code')"
            :class="{ 'is-invalid': errors.transaction_code }"
          />
          <div class="invalid-feedback">{{ errors.transaction_code }}</div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-4">
          <label class="form-label">交易类型</label>
          <input
            type="text"
            class="form-control"
            v-model="form.transaction_type"
            :ref="el => inputRefs.transaction_type.value = el"
            @keydown="handleKeyNavigation($event, 'transaction_type')"
            :class="{ 'is-invalid': errors.transaction_type }"
            placeholder="P-买入 S-卖出"
          />
          <div class="invalid-feedback">{{ errors.transaction_type }}</div>
        </div>
      </div>

      <!-- 成交明细 -->
      <div class="mb-4">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <label class="form-label mb-0">成交明细</label>
          <button 
            type="button" 
            class="btn btn-sm btn-outline-primary" 
            @click="addDetail"
            :ref="el => inputRefs.addDetailBtn.value = el"
          >
            添加成交记录
          </button>
        </div>

        <div class="border rounded p-3">
          <div v-for="(detail, index) in form.details" :key="index" class="row g-2 mb-2">
            <div class="col-md-5">
              <label class="form-label">数量</label>
              <input
                type="text"
                class="form-control"
                v-model="detail.quantity"
                :ref="el => setQuantityRef(el, index)"
                @keydown="handleKeyNavigation($event, `quantity_${index}`)"
              />
            </div>

            <div class="col-md-5">
              <label class="form-label">价格</label>
              <input
                type="text"
                class="form-control"
                v-model="detail.price"
                :ref="el => setPriceRef(el, index)"
                @keydown="handleKeyNavigation($event, `price_${index}`)"
                :class="{ 'is-invalid': errors[`price_${index}`] }"
              />
              <div class="invalid-feedback">{{ errors[`price_${index}`] }}</div>
            </div>

            <div class="col-md-2 d-flex align-items-end">
              <button
                type="button"
                class="btn btn-outline-danger w-100"
                @click="removeDetail(index)"
                :disabled="form.details.length === 1"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 费用明细 -->
      <div class="mb-4">
        <label class="form-label">费用明细</label>
        <div class="border rounded p-3">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label">经纪佣金</label>
              <input
                type="text"
                class="form-control"
                v-model="form.broker_fee"
                :ref="el => inputRefs.broker_fee.value = el"
                @keydown="handleKeyNavigation($event, 'broker_fee')"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">交易征费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.transaction_levy"
                :ref="el => inputRefs.transaction_levy.value = el"
                @keydown="handleKeyNavigation($event, 'transaction_levy')"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">印花税</label>
              <input
                type="text"
                class="form-control"
                v-model="form.stamp_duty"
                :ref="el => inputRefs.stamp_duty.value = el"
                @keydown="handleKeyNavigation($event, 'stamp_duty')"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">交易费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.trading_fee"
                :ref="el => inputRefs.trading_fee.value = el"
                @keydown="handleKeyNavigation($event, 'trading_fee')"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">存入证券费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.deposit_fee"
                :ref="el => inputRefs.deposit_fee.value = el"
                @keydown="handleKeyNavigation($event, 'deposit_fee')"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 按钮组 -->
      <div class="d-flex justify-content-end gap-2">
        <button 
          type="button" 
          class="btn btn-secondary" 
          @click="$router.back()"
          :ref="el => inputRefs.cancelBtn.value = el"
        >
          取消
        </button>
        <button 
          type="button"
          class="btn btn-primary" 
          :disabled="submitting"
          :ref="el => inputRefs.saveBtn.value = el"
          @click="submitForm"
        >
          <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
          保存
        </button>
        <button 
          type="button" 
          class="btn btn-success" 
          :disabled="submitting" 
          @click="saveAndAdd"
          :ref="el => inputRefs.saveAndAddBtn.value = el"
        >
          <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
          保存并添加下一条
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useDateInput } from '../composables/useDateInput'
import StockSelector from '../components/StockSelector.vue'
import axios from 'axios'
import useMessage from '../composables/useMessage'
import { debounce } from 'lodash'

const router = useRouter()
const message = useMessage()
const submitting = ref(false)
const saveAndAddNext = ref(false)

// 表单数据
const form = ref({
  transaction_date: '',
  stock_code: '',
  stock_name: '',
  transaction_code: '',
  transaction_type: '',
  details: [{ quantity: null, price: null }],
  broker_fee: '',
  transaction_levy: '',
  stamp_duty: '',
  trading_fee: '',
  deposit_fee: '',
  market: 'HK'
})

// 错误信息
const errors = ref({})

// 日期处理
const { 
  displayValue: dateDisplayValue, 
  handleInput: handleDateInputChange,
  handleBlur: handleDateBlurChange,
  validateDateString,
  isValid: dateIsValid
} = useDateInput('', {
  onBlur: () => {
    if (!dateIsValid.value) {
      errors.value.transaction_date = '请输入有效的交易日期'
    } else {
      delete errors.value.transaction_date
    }
  }
})

// 修改 refs 对象的定义方式
const inputRefs = {
  transaction_date: ref(null),
  stock_code: ref(null),
  transaction_code: ref(null),
  transaction_type: ref(null),
  broker_fee: ref(null),
  transaction_levy: ref(null),
  stamp_duty: ref(null),
  trading_fee: ref(null),
  deposit_fee: ref(null),
  cancelBtn: ref(null),
  saveBtn: ref(null),
  saveAndAddBtn: ref(null),
  addDetailBtn: ref(null),
  quantityRefs: [],
  priceRefs: []
}

// 股票搜索相关
const showStockList = ref(false)
const filteredStocks = ref([])
const currentStockIndex = ref(-1)

// 方法
const addDetail = () => {
  form.value.details.push({ quantity: null, price: null })
}

const removeDetail = (index) => {
  if (form.value.details.length > 1) {
    form.value.details.splice(index, 1)
  }
}

// 修改日期处理相关代码
const handleDateInput = (event) => {
  const newValue = handleDateInputChange(event)
  form.value.transaction_date = newValue
}

const handleDateBlur = () => {
  const input = form.value.transaction_date
  if (!input) return handleDateBlurChange()

  // 处理简单数字输入
  if (/^\d{1,2}$/.test(input)) {
    // 如果输入1-31的数字，自动补充为当前年月
    const day = input.padStart(2, '0')
    const today = new Date()
    const year = today.getFullYear()
    const month = (today.getMonth() + 1).toString().padStart(2, '0')
    form.value.transaction_date = `${year}-${month}-${day}`
  } else if (/^\d{1,2}-\d{1,2}$/.test(input)) {
    // 如果输入月-日格式，自动补充年份
    const [month, day] = input.split('-').map(num => num.padStart(2, '0'))
    const year = new Date().getFullYear()
    form.value.transaction_date = `${year}-${month}-${day}`
  } else if (/^\d{1,2}-\d{1,2}-\d{2}$/.test(input)) {
    // 如果输入月-日-年格式（两位年份），自动补充为20xx
    const [month, day, shortYear] = input.split('-').map(num => num.padStart(2, '0'))
    form.value.transaction_date = `20${shortYear}-${month}-${day}`
  }

  handleDateBlurChange()
}

// 表单验证
const validateForm = () => {
  errors.value = {}
  let isValid = true

  // 验证日期
  if (!form.value.transaction_date || !dateIsValid.value) {
    errors.value.transaction_date = '请输入有效的交易日期'
    isValid = false
  }

  // 验证股票代码
  if (!form.value.stock_code) {
    errors.value.stock_code = '请选择股票'
    isValid = false
  }

  // 验证交易编号
  if (!form.value.transaction_code) {
    errors.value.transaction_code = '请输入交易编号'
    isValid = false
  }

  // 验证交易类型
  if (!form.value.transaction_type) {
    errors.value.transaction_type = '请选择交易类型'
    isValid = false
  }

  // 验证明细
  form.value.details.forEach((detail, index) => {
    const price = parseFloat(detail.price)
    if (isNaN(price) || price <= 0) {
      errors.value[`price_${index}`] = '请输入有效的价格'
      isValid = false
    }
    
    const quantity = parseFloat(detail.quantity)
    if (isNaN(quantity) || quantity <= 0) {
      errors.value[`quantity_${index}`] = '请输入有效的数量'
      isValid = false
    }
  })

  return isValid
}

// 监听交易类型变化，但不自动计算印花税
watch(() => form.value.transaction_type, () => {
  if (form.value.transaction_type === 'buy') {
    form.value.stamp_duty = ''
  }
})

// 处理交易编号输入
const handleTransactionCodeInput = (event) => {
  const code = event.target.value.toUpperCase()
  form.value.transaction_code = code
  
  // 根据交易编号自动判断买卖类型
  if (code.startsWith('P')) {
    form.value.transaction_type = 'buy'
  } else if (code.startsWith('S')) {
    form.value.transaction_type = 'sell'
  }
}

// 添加交易编号失去焦点事件处理
const handleTransactionCodeBlur = async (event) => {
  const code = form.value.transaction_code.trim()
  if (!code) return

  try {
    const response = await axios.get(`/api/stock/transactions/check-code?code=${encodeURIComponent(code)}`)
    if (response.data.exists) {
      errors.value.transaction_code = '交易编号已存在，请重新输入'
      // 保持焦点在输入框
      event.target.focus()
    } else {
      delete errors.value.transaction_code
    }
  } catch (error) {
    console.error('检查交易编号失败:', error)
    message.error('检查交易编号失败，请重试')
  }
}

// 处理股票选择
const handleStockSelect = () => {
  if (showStockList.value && filteredStocks.value.length > 0) {
    const selectedStock = currentStockIndex.value >= 0 && currentStockIndex.value < filteredStocks.value.length
      ? filteredStocks.value[currentStockIndex.value]
      : filteredStocks.value[0]
    selectStock(selectedStock)
  }
}

// 选择股票
const selectStock = (stock) => {
  if (stock && stock.code) {
    form.value.stock_code = stock.code
    form.value.stock_name = stock.name || ''
    form.value.market = stock.market || 'HK'
  }
  showStockList.value = false
  filteredStocks.value = []
  currentStockIndex.value = -1
}

// 提交表单
const submitForm = async () => {
  try {
    if (!validateForm() || submitting.value) return

    submitting.value = true
    
    const submitData = {
      transaction_date: form.value.transaction_date,
      stock_code: form.value.stock_code,
      transaction_code: form.value.transaction_code,
      transaction_type: form.value.transaction_type.toUpperCase(),
      details: form.value.details.map(d => ({
        quantity: parseFloat(d.quantity) || 0,
        price: parseFloat(d.price) || 0
      })),
      broker_fee: parseFloat(form.value.broker_fee) || 0,
      transaction_levy: parseFloat(form.value.transaction_levy) || 0,
      stamp_duty: parseFloat(form.value.stamp_duty) || 0,
      trading_fee: parseFloat(form.value.trading_fee) || 0,
      deposit_fee: parseFloat(form.value.deposit_fee) || 0,
      market: form.value.market
    }
    
    const response = await axios.post('/api/stock/transactions', submitData)

    if (response.data.success) {
      message.success('交易记录添加成功')
      if (saveAndAddNext.value) {
        resetForm()
        saveAndAddNext.value = false
      } else {
        router.push('/transactions')
      }
    } else {
      throw new Error(response.data.message || '操作失败')
    }
  } catch (error) {
    message.error(error.response?.data?.message || error.message || '操作失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 保存并继续添加
const saveAndAdd = () => {
  saveAndAddNext.value = true
  submitForm()
}

// 重置表单
const resetForm = () => {
  form.value = {
    transaction_date: '',
    stock_code: '',
    stock_name: '',
    transaction_code: '',
    transaction_type: '',
    details: [{ quantity: null, price: null }],
    broker_fee: '',
    transaction_levy: '',
    stamp_duty: '',
    trading_fee: '',
    deposit_fee: '',
    market: 'HK'
  }
  errors.value = {}
}

// 在组件挂载后检查所有ref
onMounted(() => {
  nextTick(() => {
    console.log("检查所有输入框的 ref 是否绑定成功:", {
      transaction_date: inputRefs.transaction_date.value,
      stock_code: inputRefs.stock_code.value,
      transaction_code: inputRefs.transaction_code.value,
      transaction_type: inputRefs.transaction_type.value,
      broker_fee: inputRefs.broker_fee.value,
      transaction_levy: inputRefs.transaction_levy.value,
      stamp_duty: inputRefs.stamp_duty.value,
      trading_fee: inputRefs.trading_fee.value,
      deposit_fee: inputRefs.deposit_fee.value,
      cancelBtn: inputRefs.cancelBtn.value,
      saveBtn: inputRefs.saveBtn.value,
      saveAndAddBtn: inputRefs.saveAndAddBtn.value,
      addDetailBtn: inputRefs.addDetailBtn.value,
      quantityRefs: inputRefs.quantityRefs,
      priceRefs: inputRefs.priceRefs,
    });

    // 检查动态数组的长度是否匹配
    console.log("动态数组长度检查:", {
      details_length: form.value.details.length,
      quantityRefs_length: inputRefs.quantityRefs.length,
      priceRefs_length: inputRefs.priceRefs.length,
    });

    // 检查所有可聚焦元素的顺序
    const focusableElements = document.querySelectorAll(
      'input:not([disabled]), button:not([disabled])'
    );
    console.log("可聚焦元素数量:", focusableElements.length);
    
    // 检查每个动态行的ref
    form.value.details.forEach((_, index) => {
      console.log(`第 ${index + 1} 行明细的ref:`, {
        quantity: inputRefs.quantityRefs[index],
        price: inputRefs.priceRefs[index],
      });
    });
  });

  document.addEventListener('click', handleClickOutside)
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 修改动态ref的处理
const setQuantityRef = (el, index) => {
  if (el) {
    // 确保数组长度足够
    while (inputRefs.quantityRefs.length <= index) {
      inputRefs.quantityRefs.push(null);
    }
    inputRefs.quantityRefs[index] = el;
  }
}

const setPriceRef = (el, index) => {
  if (el) {
    // 确保数组长度足够
    while (inputRefs.priceRefs.length <= index) {
      inputRefs.priceRefs.push(null);
    }
    inputRefs.priceRefs[index] = el;
  }
}

// 监听明细数量变化，更新refs数组
watch(() => form.value.details.length, (newLength) => {
  nextTick(() => {
    // 重置refs数组并保持现有的引用
    const newQuantityRefs = new Array(newLength).fill(null);
    const newPriceRefs = new Array(newLength).fill(null);
    
    // 复制现有的引用
    inputRefs.quantityRefs.forEach((ref, index) => {
      if (index < newLength) {
        newQuantityRefs[index] = ref;
      }
    });
    
    inputRefs.priceRefs.forEach((ref, index) => {
      if (index < newLength) {
        newPriceRefs[index] = ref;
      }
    });
    
    inputRefs.quantityRefs = newQuantityRefs;
    inputRefs.priceRefs = newPriceRefs;
  })
})

// 键盘导航处理
const handleKeyNavigation = (event, fieldName) => {
  // Enter键导航逻辑
  if (event.key === 'Enter') {
    event.preventDefault();
    console.log('Enter键导航 - 当前字段:', fieldName);

    // 处理动态字段的导航
    if (fieldName.startsWith('quantity_')) {
      const index = parseInt(fieldName.split('_')[1]);
      inputRefs.priceRefs[index]?.focus();
      return;
    }
    
    if (fieldName.startsWith('price_')) {
      // 如果是最后一行的价格，跳转到经纪佣金
      const index = parseInt(fieldName.split('_')[1]);
      if (index === form.value.details.length - 1) {
        inputRefs.broker_fee.value?.focus();
      }
      return;
    }

    // Enter键特定导航映射
    const enterKeyMap = {
      'transaction_date': () => inputRefs.stock_code.value?.focus(),
      'stock_code': () => inputRefs.transaction_code.value?.focus(),
      'transaction_code': () => inputRefs.quantityRefs[0]?.focus(),
      'broker_fee': () => inputRefs.transaction_levy.value?.focus(),
      'transaction_levy': () => inputRefs.stamp_duty.value?.focus(),
      'stamp_duty': () => inputRefs.trading_fee.value?.focus(),
      'trading_fee': () => inputRefs.deposit_fee.value?.focus(),
      'deposit_fee': () => inputRefs.saveAndAddBtn.value?.click()
    };

    // 执行Enter键导航
    if (enterKeyMap[fieldName]) {
      enterKeyMap[fieldName]();
    }
    return;
  }

  // Tab键导航逻辑
  if (event.key === 'Tab') {
    event.preventDefault();
    console.log('Tab键导航 - 当前字段:', fieldName);

    // 处理动态字段的Tab导航
    if (fieldName.startsWith('quantity_')) {
      const index = parseInt(fieldName.split('_')[1]);
      inputRefs.priceRefs[index]?.focus();
      return;
    }
    
    if (fieldName.startsWith('price_')) {
      // 点击添加按钮并聚焦到新行
      addDetail();
      nextTick(() => {
        const newIndex = form.value.details.length - 1;
        inputRefs.quantityRefs[newIndex]?.focus();
      });
      return;
    }

    // Tab键特定导航映射
    const tabKeyMap = {
      'transaction_date': () => inputRefs.stock_code.value?.focus(),
      'stock_code': () => inputRefs.transaction_code.value?.focus(),
      'transaction_code': () => inputRefs.quantityRefs[0]?.focus(),
      'broker_fee': () => inputRefs.transaction_levy.value?.focus(),
      'transaction_levy': () => inputRefs.stamp_duty.value?.focus(),
      'stamp_duty': () => inputRefs.trading_fee.value?.focus(),
      'trading_fee': () => inputRefs.deposit_fee.value?.focus(),
      'deposit_fee': () => inputRefs.cancelBtn.value?.focus()
    };

    // 执行Tab键导航
    if (tabKeyMap[fieldName]) {
      tabKeyMap[fieldName]();
    }
  }
};

// 处理股票代码输入
const handleStockCodeInput = debounce(async (event) => {
  const query = event.target.value.trim()
  if (!query) {
    showStockList.value = false
    filteredStocks.value = []
    return
  }

  try {
    const response = await axios.get(`/api/stock/stocks/search?query=${encodeURIComponent(query)}`)
    if (response.data.success && Array.isArray(response.data.data)) {
      filteredStocks.value = response.data.data
      showStockList.value = filteredStocks.value.length > 0
      currentStockIndex.value = -1
    } else {
      filteredStocks.value = []
      showStockList.value = false
    }
  } catch (error) {
    console.error('搜索股票失败:', error)
    filteredStocks.value = []
    showStockList.value = false
  }
}, 300)

// 导航股票列表
const navigateStockList = (direction) => {
  if (!showStockList.value || filteredStocks.value.length === 0) return

  if (direction === 'up') {
    currentStockIndex.value = currentStockIndex.value <= 0 
      ? filteredStocks.value.length - 1 
      : currentStockIndex.value - 1
  } else {
    currentStockIndex.value = currentStockIndex.value >= filteredStocks.value.length - 1
      ? 0 
      : currentStockIndex.value + 1
  }
}

// 关闭股票列表
const closeStockList = () => {
  showStockList.value = false
  currentStockIndex.value = -1
}

// 点击外部关闭股票列表
const handleClickOutside = (event) => {
  if (!event.target.closest('.position-relative')) {
    closeStockList()
  }
}
</script>

<style scoped>
.card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: none;
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
}

.card-header h5 {
  font-size: 1rem;
}

.card-body {
  padding: 1rem;
}

.form-label {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.input-group-text {
  background-color: #f8f9fa;
  min-width: 80px;
  border-color: #dee2e6;
  color: #495057;
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.form-control,
.form-select {
  border-color: #dee2e6;
  padding: 0.25rem 0.5rem;
  height: calc(2rem + 2px);
  font-size: 0.875rem;
}

.form-control:focus,
.form-select:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.15rem rgba(0, 123, 255, 0.25);
}

.border {
  border-color: #dee2e6 !important;
}

.rounded {
  border-radius: 0.25rem !important;
}

.btn {
  padding: 0.25rem 0.75rem;
  font-weight: 500;
  font-size: 0.875rem;
}

.btn-sm {
  padding: 0.2rem 0.5rem;
  font-size: 0.8125rem;
}

.btn-outline-primary {
  border-color: #dee2e6;
  color: #0d6efd;
  &:hover {
    background-color: #0d6efd;
    border-color: #0d6efd;
    color: #fff;
  }
}

.btn-outline-danger {
  padding: 0.25rem 0.5rem;
  border-color: #dc3545;
}

.invalid-feedback {
  font-size: 0.75rem;
  margin-top: 0.125rem;
}

.mb-4 {
  margin-bottom: 1rem !important;
}

.mb-2 {
  margin-bottom: 0.5rem !important;
}

.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}

.g-3 {
  --bs-gutter-x: 0.75rem;
  --bs-gutter-y: 0.75rem;
}

.p-3 {
  padding: 0.75rem !important;
}

.gap-2 {
  gap: 0.5rem !important;
}

.input-group > .form-control,
.input-group > .form-select {
  height: calc(2rem + 2px);
}

.btn-outline-danger {
  height: calc(2rem + 2px);
  line-height: 1;
}

.row > [class*="col-"] {
  padding-right: calc(var(--bs-gutter-x) * 0.5);
  padding-left: calc(var(--bs-gutter-x) * 0.5);
}

/* 添加股票搜索相关样式 */
.stock-input-wrapper {
  position: relative;
}

.stock-input-wrapper input {
  padding-right: 120px;
}

.selected-stock {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.875rem;
  color: #666;
  max-width: 70%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
}

.market-tag {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  margin-right: 0.5rem;
}

.market-tag.hk {
  background-color: #ffebee;
  color: #d32f2f;
}

.market-tag.usa {
  background-color: #e3f2fd;
  color: #1976d2;
}

.stock-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.stock-item {
  display: block;
  padding: 0.5rem;
  color: #212529;
  text-decoration: none;
  border-bottom: 1px solid #dee2e6;
}

.stock-item:last-child {
  border-bottom: none;
}

.stock-item:hover,
.stock-item.active {
  background-color: #f8f9fa;
}

.stock-item:active {
  background-color: #e9ecef;
}
</style> 