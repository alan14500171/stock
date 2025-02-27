<template>
  <div class="transaction-add-container">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">添加交易记录</h5>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleSubmit">
          <!-- 股票选择 -->
          <div class="mb-3">
            <label for="stock" class="form-label">选择股票</label>
            <select 
              id="stock" 
              v-model="form.stock_id" 
              class="form-select" 
              required
              :disabled="loading"
            >
              <option value="" disabled selected>请选择股票</option>
              <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
                {{ stock.code }} - {{ stock.name }}
              </option>
            </select>
          </div>

          <!-- 交易类型 -->
          <div class="mb-3">
            <label class="form-label">交易类型</label>
            <div class="btn-group w-100" role="group">
              <input 
                type="radio" 
                class="btn-check" 
                name="transaction_type" 
                id="type-buy" 
                value="buy" 
                v-model="form.transaction_type"
                :disabled="loading"
              >
              <label class="btn btn-outline-success" for="type-buy">买入</label>

              <input 
                type="radio" 
                class="btn-check" 
                name="transaction_type" 
                id="type-sell" 
                value="sell" 
                v-model="form.transaction_type"
                :disabled="loading"
              >
              <label class="btn btn-outline-danger" for="type-sell">卖出</label>
            </div>
          </div>

          <!-- 交易日期 -->
          <div class="mb-3">
            <label for="transaction_date" class="form-label">交易日期</label>
            <input 
              type="date" 
              id="transaction_date" 
              v-model="form.transaction_date" 
              class="form-control" 
              required
              :disabled="loading"
            >
          </div>

          <!-- 价格和数量 -->
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="price" class="form-label">价格</label>
              <div class="input-group">
                <input 
                  type="number" 
                  id="price" 
                  v-model="form.price" 
                  class="form-control" 
                  step="0.001" 
                  min="0" 
                  required
                  :disabled="loading"
                >
                <span class="input-group-text">元</span>
              </div>
            </div>
            <div class="col-md-6 mb-3">
              <label for="quantity" class="form-label">数量</label>
              <div class="input-group">
                <input 
                  type="number" 
                  id="quantity" 
                  v-model="form.quantity" 
                  class="form-control" 
                  step="1" 
                  min="1" 
                  required
                  :disabled="loading"
                >
                <span class="input-group-text">股</span>
              </div>
            </div>
          </div>

          <!-- 手续费 -->
          <div class="mb-3">
            <label for="fee" class="form-label">手续费</label>
            <div class="input-group">
              <input 
                type="number" 
                id="fee" 
                v-model="form.fee" 
                class="form-control" 
                step="0.01" 
                min="0"
                :disabled="loading"
              >
              <span class="input-group-text">元</span>
            </div>
          </div>

          <!-- 备注 -->
          <div class="mb-4">
            <label for="remarks" class="form-label">备注</label>
            <textarea 
              id="remarks" 
              v-model="form.remarks" 
              class="form-control" 
              rows="3"
              :disabled="loading"
            ></textarea>
          </div>

          <!-- 提交按钮 -->
          <div class="d-grid gap-2 d-md-flex justify-content-md-end">
            <router-link to="/transaction/list" class="btn btn-outline-secondary" :disabled="loading">
              取消
            </router-link>
            <button type="submit" class="btn btn-primary" :disabled="loading || !isFormValid">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? '提交中...' : '提交' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'

const router = useRouter()
const message = useMessage()

// 股票列表
const stocks = ref([])
// 加载状态
const loading = ref(false)

// 表单数据
const form = ref({
  stock_id: '',
  transaction_type: 'buy',
  transaction_date: new Date().toISOString().split('T')[0], // 默认今天
  price: '',
  quantity: '',
  fee: 0,
  remarks: ''
})

// 计算属性：表单是否有效
const isFormValid = computed(() => {
  return form.value.stock_id && 
         form.value.transaction_type && 
         form.value.transaction_date && 
         form.value.price > 0 && 
         form.value.quantity > 0
})

// 加载股票列表
const loadStocks = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/stock/list')
    if (response.data.success) {
      stocks.value = response.data.data || []
    } else {
      message.error('加载股票列表失败')
    }
  } catch (error) {
    console.error('加载股票列表失败:', error)
    message.error('加载股票列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!isFormValid.value || loading.value) return
  
  try {
    loading.value = true
    const response = await axios.post('/api/transaction/add', form.value)
    
    if (response.data.success) {
      message.success('交易记录添加成功')
      router.push('/transaction/list')
    } else {
      message.error(response.data.message || '添加失败')
    }
  } catch (error) {
    console.error('添加交易记录失败:', error)
    message.error(error.response?.data?.message || '添加失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载股票列表
onMounted(() => {
  loadStocks()
})
</script>

<style scoped>
.transaction-add-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  border: none;
  border-radius: 10px;
  overflow: hidden;
}

.card-header {
  background-color: #0d6efd;
  padding: 15px 20px;
}

.card-body {
  padding: 25px;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.btn-check:checked + .btn-outline-success {
  background-color: #198754;
  color: white;
}

.btn-check:checked + .btn-outline-danger {
  background-color: #dc3545;
  color: white;
}

.btn-group {
  border-radius: 0.375rem;
  overflow: hidden;
}

.btn-group .btn {
  flex: 1;
  padding: 0.5rem 0;
}

@media (max-width: 768px) {
  .transaction-add-container {
    padding: 10px;
  }
  
  .card-body {
    padding: 15px;
  }
}
</style> 