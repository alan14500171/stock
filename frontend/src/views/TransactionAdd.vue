<template>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">{{ isEdit ? '编辑交易记录' : '添加交易记录' }}</h5>
    </div>
    
    <div class="card-body">
      <form @submit.prevent="submitForm">
        <!-- 基本信息 -->
        <div class="row mb-4">
          <div class="col-md-4">
            <label class="form-label">交易日期</label>
            <div class="date-input">
              <input
                type="text"
                class="form-control"
                :value="dateDisplayValue"
                @input="handleDateInput"
                @blur="handleDateBlur"
                @keydown.enter="focusNext($event, 'stock_code')"
                :class="{ 'is-invalid': errors.transaction_date }"
                placeholder="YYYY-MM-DD"
                ref="transaction_date"
              />
              <div class="invalid-feedback">{{ errors.transaction_date }}</div>
            </div>
          </div>

          <div class="col-md-4">
            <label class="form-label">股票代码</label>
            <stock-selector
              v-model="form.stock_code"
              :class="{ 'is-invalid': errors.stock_code }"
              ref="stock_code"
              placeholder="输入代码或名称搜索"
              @enter="focusNext($event, 'transaction_code')"
            />
            <div class="invalid-feedback">{{ errors.stock_code }}</div>
          </div>

          <div class="col-md-4">
            <label class="form-label">交易编号</label>
            <input
              type="text"
              class="form-control"
              v-model="form.transaction_code"
              :class="{ 'is-invalid': errors.transaction_code }"
              ref="transaction_code"
              @input="handleTransactionCodeInput"
              @keydown.enter="focusNext($event, 'transaction_type')"
            />
            <div class="invalid-feedback">{{ errors.transaction_code }}</div>
          </div>
        </div>

        <div class="row mb-4">
          <div class="col-md-4">
            <label class="form-label">买卖</label>
            <select
              class="form-select"
              v-model="form.transaction_type"
              :class="{ 'is-invalid': errors.transaction_type }"
              ref="transaction_type"
              @keydown.enter="focusNext($event, 'quantity_0')"
            >
              <option value="">请选择类型</option>
              <option value="buy">买入</option>
              <option value="sell">卖出</option>
            </select>
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
              ref="addDetailBtn"
            >
              添加成交记录
            </button>
          </div>

          <div class="border rounded p-3">
            <div v-for="(detail, index) in form.details" :key="index" class="row g-2 mb-2">
              <div class="col-md-5">
                <div class="input-group">
                  <span class="input-group-text">数量</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="detail.quantity"
                    :ref="`quantity_${index}`"
                    @keydown.enter="focusNext($event, `price_${index}`)"
                  />
                </div>
              </div>

              <div class="col-md-5">
                <div class="input-group">
                  <span class="input-group-text">价格</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="detail.price"
                    min="0"
                    step="0.001"
                    :class="{ 'is-invalid': errors[`price_${index}`] }"
                    :ref="`price_${index}`"
                    @keydown.enter="handlePriceEnter($event, index)"
                    @keydown.tab="focusNext($event, 'addDetailBtn')"
                  />
                  <div class="invalid-feedback">{{ errors[`price_${index}`] }}</div>
                </div>
              </div>

              <div class="col-md-2">
                <button
                  type="button"
                  class="btn btn-outline-danger"
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
                <div class="input-group">
                  <span class="input-group-text">经纪佣金</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="form.broker_fee"
                    min="0"
                    step="0.01"
                    ref="broker_fee"
                    @keydown.enter="focusNext($event, 'transaction_levy')"
                    @keydown.tab="focusNext($event, 'saveBtn')"
                  />
                </div>
              </div>

              <div class="col-md-4">
                <div class="input-group">
                  <span class="input-group-text">交易征费</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="form.transaction_levy"
                    min="0"
                    step="0.01"
                    ref="transaction_levy"
                    @keydown.enter="focusNext($event, 'stamp_duty')"
                    @keydown.tab="focusNext($event, 'stamp_duty')"
                  />
                </div>
              </div>

              <div class="col-md-4">
                <div class="input-group">
                  <span class="input-group-text">印花税</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="form.stamp_duty"
                    min="0"
                    step="0.01"
                    ref="stamp_duty"
                    @keydown.enter="focusNext($event, 'trading_fee')"
                    @keydown.tab="focusNext($event, 'trading_fee')"
                  />
                </div>
              </div>

              <div class="col-md-4">
                <div class="input-group">
                  <span class="input-group-text">交易费</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="form.trading_fee"
                    min="0"
                    step="0.01"
                    ref="trading_fee"
                    @keydown.enter="focusNext($event, 'deposit_fee')"
                    @keydown.tab="focusNext($event, 'deposit_fee')"
                  />
                </div>
              </div>

              <div class="col-md-4">
                <div class="input-group">
                  <span class="input-group-text">存入证券费</span>
                  <input
                    type="number"
                    class="form-control"
                    v-model="form.deposit_fee"
                    min="0"
                    step="0.01"
                    ref="deposit_fee"
                    @keydown.enter="saveAndAdd"
                    @keydown.tab="focusNext($event, 'cancelBtn')"
                  />
                </div>
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
            ref="cancelBtn"
          >
            取消
          </button>
          <button 
            type="submit" 
            class="btn btn-primary" 
            :disabled="submitting"
            ref="saveBtn"
          >
            <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
            保存
          </button>
          <button 
            type="button" 
            class="btn btn-success" 
            :disabled="submitting" 
            @click="saveAndAdd"
            ref="saveAndAddBtn"
          >
            <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
            保存并添加下一条
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDateInput } from '../composables/useDateInput'
import StockSelector from '../components/StockSelector.vue'
import axios from 'axios'
import useMessage from '../composables/useMessage'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const submitting = ref(false)
const saveAndAddNext = ref(false)
const isEdit = computed(() => route.params.id !== undefined)

// 表单数据
const form = ref({
  transaction_date: '',
  stock_code: '',
  stock_name: '',
  transaction_code: '',
  transaction_type: '',
  details: [{ quantity: null, price: null }],
  broker_fee: 0,
  transaction_levy: 0,
  stamp_duty: 0,
  trading_fee: 0,
  deposit_fee: 0
})

// 错误信息
const errors = ref({})

// 计算属性
const totalQuantity = computed(() => {
  return form.value.details.reduce((sum, detail) => {
    return sum + (Number(detail.quantity) || 0)
  }, 0)
})

const totalAmount = computed(() => {
  return form.value.details.reduce((sum, detail) => {
    return sum + (Number(detail.quantity) || 0) * (Number(detail.price) || 0)
  }, 0)
})

// 日期处理
const { 
  displayValue: dateDisplayValue, 
  handleInput: handleDateInputChange,
  handleBlur: handleDateBlurChange,
  setToday,
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

// 方法
const addDetail = () => {
  form.value.details.push({ quantity: null, price: null })
}

const removeDetail = (index) => {
  if (form.value.details.length > 1) {
    form.value.details.splice(index, 1)
  }
}

// TAB键焦点控制
const focusNext = (event, nextRef) => {
  event.preventDefault();
  
  const stockSelector = document.querySelector('.stock-selector input');
  if (nextRef === 'stock_code' && stockSelector) {
    stockSelector.focus();
    return;
  }
  
  const element = document.querySelector(`[ref="${nextRef}"]`);
  if (element) {
    if (element.tagName === 'INPUT' || element.tagName === 'SELECT') {
      element.focus();
    } else {
      const input = element.querySelector('input');
      if (input) {
        input.focus();
      }
    }
  }
}

// 处理日期输入
const handleDateInput = (event) => {
  const newValue = handleDateInputChange(event)
  form.value.transaction_date = newValue
}

// 处理日期失焦
const handleDateBlur = () => {
  handleDateBlurChange()
}

// 表单验证
const validateForm = () => {
  try {
    errors.value = {}
    let isValid = true

    // 检查form对象是否存在
    if (!form || !form.value) {
      console.error('表单对象不存在')
      return false
    }

    // 验证日期
    if (!form.value.transaction_date) {
      errors.value.transaction_date = '请输入交易日期'
      isValid = false
    } else if (dateIsValid && !dateIsValid.value) {
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
    if (!form.value.details || !Array.isArray(form.value.details)) {
      console.error('交易明细格式错误')
      return false
    }

    form.value.details.forEach((detail, index) => {
      if (!detail) {
        errors.value[`detail_${index}`] = '明细数据无效'
        isValid = false
        return
      }

      // 验证价格
      if (!detail.price || detail.price <= 0) {
        errors.value[`price_${index}`] = '请输入有效的价格'
        isValid = false
      }
    })

    return isValid
  } catch (error) {
    console.error('表单验证出错:', error)
    return false
  }
}

// 自动计算费用
const calculateFees = () => {
  // 移除自动计算功能
  return
}

// 监听交易类型变化，但不自动计算印花税
watch(() => form.value.transaction_type, () => {
  if (form.value.transaction_type === 'buy') {
    form.value.stamp_duty = 0
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

// 处理价格输入框的回车事件
const handlePriceEnter = (event, index) => {
  event.preventDefault()
  if (index === form.value.details.length - 1) {
    focusNext(event, 'broker_fee')
  } else {
    focusNext(event, `quantity_${index + 1}`)
  }
}

// 加载交易记录数据
const loadTransaction = async () => {
  if (!isEdit.value) return
  
  try {
    const response = await axios.get(`/api/stock/transactions/${route.params.id}`)
    if (response.data.success) {
      const transaction = response.data.data
      form.value = {
        transaction_date: transaction.transaction_date,
        stock_code: transaction.stock_code,
        stock_name: transaction.stock_name,
        transaction_code: transaction.transaction_code,
        transaction_type: transaction.transaction_type.toLowerCase(),
        details: transaction.details || [{ quantity: transaction.total_quantity, price: transaction.total_amount / transaction.total_quantity }],
        broker_fee: transaction.broker_fee,
        transaction_levy: transaction.transaction_levy,
        stamp_duty: transaction.stamp_duty,
        trading_fee: transaction.trading_fee,
        deposit_fee: transaction.deposit_fee
      }
    }
  } catch (error) {
    console.error('加载交易记录失败:', error)
  }
}

// 提交表单
const submitForm = async () => {
  try {
    if (!validateForm() || submitting.value) return

    submitting.value = true
    const url = isEdit.value 
      ? `/api/stock/transactions/${route.params.id}`
      : '/api/stock/transactions'
      
    const method = isEdit.value ? 'put' : 'post'
    
    const submitData = {
      transaction_date: form.value.transaction_date,
      stock_code: form.value.stock_code,
      transaction_code: form.value.transaction_code,
      transaction_type: form.value.transaction_type.toUpperCase(),
      details: form.value.details.map(d => ({
        quantity: Number(d.quantity),
        price: Number(d.price)
      })),
      broker_fee: Number(form.value.broker_fee) || 0,
      transaction_levy: Number(form.value.transaction_levy) || 0,
      stamp_duty: Number(form.value.stamp_duty) || 0,
      trading_fee: Number(form.value.trading_fee) || 0,
      deposit_fee: Number(form.value.deposit_fee) || 0
    }
    
    const response = await axios[method](url, submitData)

    if (response.data.success) {
      message.success(isEdit.value ? '交易记录更新成功' : '交易记录添加成功')
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
    transaction_date: setToday(),
    stock_code: '',
    stock_name: '',
    transaction_code: '',
    transaction_type: '',
    details: [{ quantity: null, price: null }],
    broker_fee: 0,
    transaction_levy: 0,
    stamp_duty: 0,
    trading_fee: 0,
    deposit_fee: 0
  }
  errors.value = {}
}

// 组件挂载时设置默认日期和加载数据
onMounted(() => {
  resetForm()
  loadTransaction()
})
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
}

.btn-outline-primary:hover {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
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

.stock-selector {
  position: relative;
}

.stock-selector .dropdown-menu {
  margin-top: 1px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  font-size: 0.875rem;
}

.date-input input[type="date"] {
  padding: 0.25rem 0.5rem;
  height: calc(2rem + 2px);
  font-size: 0.875rem;
}

.gap-2 {
  gap: 0.5rem !important;
}

/* 调整下拉菜单样式 */
.dropdown-item {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

/* 调整输入框组合样式 */
.input-group > .form-control,
.input-group > .form-select {
  height: calc(2rem + 2px);
}

/* 调整删除按钮大小 */
.btn-outline-danger {
  height: calc(2rem + 2px);
  line-height: 1;
}

/* 调整表单组间距 */
.row > [class*="col-"] {
  padding-right: calc(var(--bs-gutter-x) * 0.5);
  padding-left: calc(var(--bs-gutter-x) * 0.5);
}
</style> 