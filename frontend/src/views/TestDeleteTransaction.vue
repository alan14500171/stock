<template>
  <div class="container mt-4">
    <h2>交易记录删除测试</h2>
    
    <div class="alert alert-info" v-if="message">
      {{ message }}
    </div>
    
    <div class="mb-3">
      <label for="transactionId" class="form-label">交易记录ID</label>
      <input type="number" class="form-control" id="transactionId" v-model="transactionId" placeholder="输入要删除的交易记录ID">
    </div>
    
    <button class="btn btn-danger" @click="deleteTransaction" :disabled="loading">
      <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
      删除交易记录
    </button>
    
    <div class="mt-4">
      <h4>删除结果</h4>
      <pre v-if="result" class="bg-light p-3 rounded">{{ JSON.stringify(result, null, 2) }}</pre>
      <div v-if="error" class="alert alert-danger">
        <strong>错误:</strong> {{ error }}
      </div>
    </div>
    
    <div class="mt-4">
      <h4>交易记录列表</h4>
      <button class="btn btn-primary mb-3" @click="fetchTransactions" :disabled="loadingList">
        <span v-if="loadingList" class="spinner-border spinner-border-sm me-2"></span>
        刷新列表
      </button>
      
      <div class="table-responsive">
        <table class="table table-striped table-bordered">
          <thead>
            <tr>
              <th>ID</th>
              <th>日期</th>
              <th>股票代码</th>
              <th>市场</th>
              <th>交易类型</th>
              <th>数量</th>
              <th>金额</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in transactions" :key="transaction.id">
              <td>{{ transaction.id }}</td>
              <td>{{ formatDate(transaction.transaction_date) }}</td>
              <td>{{ transaction.stock_code }}</td>
              <td>{{ transaction.market }}</td>
              <td>{{ transaction.transaction_type }}</td>
              <td>{{ transaction.total_quantity }}</td>
              <td>{{ transaction.total_amount }}</td>
              <td>
                <button class="btn btn-sm btn-danger" @click="deleteTransactionById(transaction.id)">
                  删除
                </button>
              </td>
            </tr>
            <tr v-if="transactions.length === 0">
              <td colspan="8" class="text-center">没有交易记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const transactionId = ref('')
const loading = ref(false)
const loadingList = ref(false)
const message = ref('')
const result = ref(null)
const error = ref('')
const transactions = ref([])

// 获取交易记录列表
const fetchTransactions = async () => {
  loadingList.value = true
  error.value = ''
  
  try {
    const response = await axios.get('/api/stock/transactions/', {
      params: {
        _t: Date.now() + Math.random() // 防止缓存
      },
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
    
    if (response.data && response.data.success) {
      transactions.value = response.data.data.items || []
      console.log('获取到交易记录:', transactions.value.length)
    } else {
      error.value = '获取交易记录失败: ' + (response.data?.message || '未知错误')
    }
  } catch (err) {
    console.error('获取交易记录出错:', err)
    error.value = '获取交易记录出错: ' + (err.message || '未知错误')
  } finally {
    loadingList.value = false
  }
}

// 删除交易记录
const deleteTransaction = async () => {
  if (!transactionId.value) {
    message.value = '请输入交易记录ID'
    return
  }
  
  loading.value = true
  message.value = '正在删除交易记录...'
  result.value = null
  error.value = ''
  
  try {
    const response = await axios.delete(`/api/stock/transactions/${transactionId.value}`, {
      headers: {
        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
      }
    })
    
    result.value = response.data
    message.value = '删除成功: ' + (response.data?.message || '交易记录已删除')
    
    // 删除成功后刷新列表
    await new Promise(resolve => setTimeout(resolve, 1000))
    await fetchTransactions()
    
  } catch (err) {
    console.error('删除交易记录出错:', err)
    error.value = '删除交易记录出错: ' + (err.response?.data?.message || err.message || '未知错误')
    result.value = err.response?.data || null
  } finally {
    loading.value = false
  }
}

// 通过ID删除交易记录
const deleteTransactionById = async (id) => {
  if (!confirm(`确定要删除ID为 ${id} 的交易记录吗？`)) {
    return
  }
  
  transactionId.value = id
  await deleteTransaction()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

// 页面加载时获取交易记录
onMounted(() => {
  fetchTransactions()
})
</script> 