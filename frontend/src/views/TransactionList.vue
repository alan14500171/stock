<template>
  <div class="transaction-list-container">
    <div class="card shadow-sm mb-4">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h5 class="mb-0">交易记录</h5>
        <router-link to="/transaction/add" class="btn btn-light btn-sm">
          <i class="bi bi-plus-lg"></i> 添加交易
        </router-link>
      </div>
      <div class="card-body">
        <!-- 筛选条件 -->
        <div class="row mb-3">
          <div class="col-md-3 mb-2">
            <div class="input-group">
              <span class="input-group-text">股票</span>
              <select v-model="filters.stock_id" class="form-select" @change="loadTransactions(1)">
                <option value="">全部股票</option>
                <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
                  {{ stock.code }} - {{ stock.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="col-md-3 mb-2">
            <div class="input-group">
              <span class="input-group-text">类型</span>
              <select v-model="filters.transaction_type" class="form-select" @change="loadTransactions(1)">
                <option value="">全部类型</option>
                <option value="buy">买入</option>
                <option value="sell">卖出</option>
              </select>
            </div>
          </div>
          <div class="col-md-3 mb-2">
            <div class="input-group">
              <span class="input-group-text">开始日期</span>
              <input 
                type="date" 
                class="form-control" 
                v-model="filters.start_date"
                @change="loadTransactions(1)"
              >
            </div>
          </div>
          <div class="col-md-3 mb-2">
            <div class="input-group">
              <span class="input-group-text">结束日期</span>
              <input 
                type="date" 
                class="form-control" 
                v-model="filters.end_date"
                @change="loadTransactions(1)"
              >
            </div>
          </div>
        </div>

        <!-- 交易记录表格 -->
        <div class="table-responsive">
          <table class="table table-hover table-striped">
            <thead class="table-light">
              <tr>
                <th>日期</th>
                <th>股票</th>
                <th>类型</th>
                <th>价格</th>
                <th>数量</th>
                <th>总金额</th>
                <th>手续费</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody v-if="transactions.length > 0">
              <tr v-for="transaction in transactions" :key="transaction.id">
                <td>{{ formatDate(transaction.transaction_date) }}</td>
                <td>
                  <span class="stock-code">{{ transaction.stock_code }}</span>
                  <span class="stock-name">{{ transaction.stock_name }}</span>
                </td>
                <td>
                  <span :class="[
                    'badge', 
                    transaction.transaction_type === 'buy' ? 'bg-success' : 'bg-danger'
                  ]">
                    {{ transaction.transaction_type === 'buy' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td>{{ formatCurrency(transaction.price) }}</td>
                <td>{{ transaction.quantity }}</td>
                <td>{{ formatCurrency(transaction.total_amount) }}</td>
                <td>{{ formatCurrency(transaction.fee) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button 
                      class="btn btn-outline-primary" 
                      @click="viewTransaction(transaction.id)"
                      title="查看详情"
                    >
                      <i class="bi bi-eye"></i>
                    </button>
                    <button 
                      class="btn btn-outline-danger" 
                      @click="confirmDelete(transaction.id)"
                      title="删除"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="8" class="text-center py-4">
                  <div v-if="loading">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2">加载中，请稍候...</p>
                  </div>
                  <div v-else>
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="mt-2">暂无交易记录</p>
                    <router-link to="/transaction/add" class="btn btn-primary btn-sm mt-2">
                      添加交易记录
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="d-flex justify-content-between align-items-center mt-3" v-if="totalPages > 1">
          <div>
            共 <span class="fw-bold">{{ totalItems }}</span> 条记录
          </div>
          <nav aria-label="Page navigation">
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="loadTransactions(currentPage - 1)">上一页</a>
              </li>
              <li 
                v-for="page in displayedPages" 
                :key="page" 
                class="page-item"
                :class="{ active: page === currentPage }"
              >
                <a class="page-link" href="#" @click.prevent="loadTransactions(page)">{{ page }}</a>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link" href="#" @click.prevent="loadTransactions(currentPage + 1)">下一页</a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div class="modal fade" id="deleteModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="deleteModalLabel">确认删除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            确定要删除这条交易记录吗？此操作不可恢复。
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button 
              type="button" 
              class="btn btn-danger" 
              @click="deleteTransaction"
              :disabled="deleting"
            >
              <span v-if="deleting" class="spinner-border spinner-border-sm me-2"></span>
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'
import { Modal } from 'bootstrap'

const router = useRouter()
const message = useMessage()

// 状态变量
const transactions = ref([])
const stocks = ref([])
const loading = ref(false)
const deleting = ref(false)
const deleteId = ref(null)
const deleteModal = ref(null)

// 分页相关
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const pageSize = 10

// 筛选条件
const filters = ref({
  stock_id: '',
  transaction_type: '',
  start_date: '',
  end_date: ''
})

// 计算属性：显示的页码
const displayedPages = computed(() => {
  const pages = []
  const maxVisiblePages = 5
  
  if (totalPages.value <= maxVisiblePages) {
    // 如果总页数小于等于最大可见页数，显示所有页码
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // 否则，显示当前页附近的页码
    let startPage = Math.max(currentPage.value - Math.floor(maxVisiblePages / 2), 1)
    let endPage = startPage + maxVisiblePages - 1
    
    if (endPage > totalPages.value) {
      endPage = totalPages.value
      startPage = Math.max(endPage - maxVisiblePages + 1, 1)
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i)
    }
  }
  
  return pages
})

// 加载交易记录
const loadTransactions = async (page = 1) => {
  try {
    loading.value = true
    currentPage.value = page
    
    const params = {
      page,
      limit: pageSize,
      ...filters.value
    }
    
    const response = await axios.get('/api/transaction/list', { params })
    
    if (response.data.success) {
      transactions.value = response.data.data.items || []
      totalItems.value = response.data.data.total || 0
      totalPages.value = Math.ceil(totalItems.value / pageSize)
    } else {
      message.error('加载交易记录失败')
    }
  } catch (error) {
    console.error('加载交易记录失败:', error)
    message.error('加载交易记录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载股票列表
const loadStocks = async () => {
  try {
    const response = await axios.get('/api/stock/list')
    if (response.data.success) {
      stocks.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载股票列表失败:', error)
  }
}

// 查看交易详情
const viewTransaction = (id) => {
  router.push(`/transaction/detail/${id}`)
}

// 确认删除
const confirmDelete = (id) => {
  deleteId.value = id
  if (!deleteModal.value) {
    deleteModal.value = new Modal(document.getElementById('deleteModal'))
  }
  deleteModal.value.show()
}

// 删除交易记录
const deleteTransaction = async () => {
  if (!deleteId.value || deleting.value) return
  
  try {
    deleting.value = true
    const response = await axios.delete(`/api/transaction/delete/${deleteId.value}`)
    
    if (response.data.success) {
      message.success('交易记录删除成功')
      deleteModal.value.hide()
      loadTransactions(currentPage.value)
    } else {
      message.error(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除交易记录失败:', error)
    message.error(error.response?.data?.message || '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 格式化货币
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toFixed(2)
}

// 组件挂载时加载数据
onMounted(() => {
  loadStocks()
  loadTransactions(1)
})
</script>

<style scoped>
.transaction-list-container {
  padding: 20px;
}

.card {
  border: none;
  border-radius: 10px;
  overflow: hidden;
}

.card-header {
  padding: 15px 20px;
}

.table th {
  font-weight: 600;
  white-space: nowrap;
}

.table td {
  vertical-align: middle;
}

.stock-code {
  font-weight: 500;
}

.stock-name {
  display: block;
  font-size: 0.85rem;
  color: #6c757d;
}

.badge {
  padding: 0.5em 0.75em;
  font-weight: 500;
}

.btn-group-sm .btn {
  padding: 0.25rem 0.5rem;
}

.pagination .page-link {
  color: #0d6efd;
  border-color: #dee2e6;
}

.pagination .page-item.active .page-link {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: white;
}

@media (max-width: 768px) {
  .transaction-list-container {
    padding: 10px;
  }
  
  .card-body {
    padding: 15px;
  }
  
  .table {
    font-size: 0.9rem;
  }
}
</style> 