<template>
  <div class="container-fluid">
    <div class="card">
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">股票管理</h5>
          <button class="btn btn-primary btn-sm" @click="showAddDialog">
            添加股票
          </button>
        </div>
        
        <div class="d-flex align-items-center">
          <div class="me-3" style="width: 200px;">
            <select class="form-select form-select-sm" v-model="searchForm.market" @change="search">
              <option value="">市场</option>
              <option value="HK">港股</option>
              <option value="USA">美股</option>
            </select>
          </div>
          <div class="flex-grow-1 d-flex">
            <input
              type="text"
              class="form-control form-control-sm me-2"
              v-model="searchForm.search"
              placeholder="输入代码、名称搜索"
              @keyup.enter="search"
              style="max-width: 300px;"
            />
            <button class="btn btn-primary btn-sm px-4" type="button" @click="search">
              查询
            </button>
          </div>
        </div>
      </div>

      <div class="card-body p-1">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr>
                <th style="width: 60px">市场</th>
                <th style="width: 80px">代码</th>
                <th style="width: 120px">名称</th>
                <th style="width: 200px">谷歌查询代码</th>
                <th style="width: 100px">当前股价</th>
                <th style="width: 140px">更新时间</th>
                <th style="width: 80px" class="text-end">操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="!loading">
                <template v-if="stocks.length">
                  <tr v-for="stock in stocks" :key="stock.id">
                    <td class="text-center">
                      <span class="badge" :class="stock.market === 'HK' ? 'bg-danger' : 'bg-primary'">
                        {{ stock.market }}
                      </span>
                    </td>
                    <td class="font-monospace">{{ stock.code }}</td>
                    <td>{{ stock.name }}</td>
                    <td>{{ stock.full_name || '-' }}</td>
                    <td>{{ formatPrice(stock.current_price, stock.market) }}</td>
                    <td>{{ formatDateTime(stock.price_updated_at) }}</td>
                    <td>
                      <div class="d-flex justify-content-end gap-1">
                        <button class="btn btn-link btn-xs p-0 text-primary" title="编辑" @click="editStock(stock)">
                          编辑
                        </button>
                        <button class="btn btn-link btn-xs p-0 text-danger ms-2" title="删除" @click="confirmDelete(stock)">
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr v-else>
                  <td colspan="7" class="text-center py-3">
                    <div class="text-muted">暂无数据</div>
                  </td>
                </tr>
              </template>
              <tr v-else>
                <td colspan="7" class="text-center py-3">
                  <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                  加载中...
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="card-footer d-flex justify-content-between align-items-center py-2">
          <div class="small text-muted">
            共 {{ totalItems }} 条记录
          </div>
          <nav>
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)" title="上一页">
                  <i class="fas fa-chevron-left"></i>
                </a>
              </li>
              <li v-for="page in displayedPages" 
                  :key="page" 
                  class="page-item"
                  :class="{ active: currentPage === page, disabled: page === '...' }">
                <template v-if="page === '...'">
                  <span class="page-link">{{ page }}</span>
                </template>
                <template v-else>
                  <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
                </template>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)" title="下一页">
                  <i class="fas fa-chevron-right"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      <!-- 添加/编辑对话框 -->
      <stock-add-dialog
        v-model="showDialog"
        :edit-data="editData"
        @success="handleSuccess"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StockAddDialog from '../components/StockAddDialog.vue'

const loading = ref(false)
const showDialog = ref(false)
const editData = ref(null)
const stocks = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const pageSize = 15

// 搜索表单
const searchForm = ref({
  market: '',
  search: ''
})

// 显示添加对话框
const showAddDialog = () => {
  editData.value = null
  showDialog.value = true
}

// 编辑股票
const editStock = (stock) => {
  editData.value = stock
  showDialog.value = true
}

// 处理添加/编辑成功
const handleSuccess = () => {
  fetchStocks()
}

// 搜索
const search = () => {
  currentPage.value = 1
  fetchStocks()
}

// 获取股票列表
const fetchStocks = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.value.market) params.append('market', searchForm.value.market)
    if (searchForm.value.search) params.append('search', searchForm.value.search)
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    const response = await axios.get('/api/stock/stocks', { params })
    
    if (response.data.success) {
      stocks.value = response.data.data.items
      totalPages.value = Math.ceil(response.data.data.total / pageSize)
      totalItems.value = response.data.data.total
      currentPage.value = response.data.data.page
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    market: '',
    search: ''
  }
  currentPage.value = 1
  fetchStocks()
}

// 删除股票
const confirmDelete = async (stock) => {
  if (!confirm(`确定要删除股票 ${stock.code} - ${stock.name} 吗？`)) return
  
  try {
    const response = await axios.delete(`/api/stock/stocks/${stock.id}`)
    if (response.data.success) {
      fetchStocks()
    }
  } catch (error) {
    console.error('删除股票失败:', error)
  }
}

// 切换页码
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchStocks()
}

// 计算显示的页码
const displayedPages = computed(() => {
  const pages = []
  const maxPages = 5
  
  if (totalPages.value <= maxPages) {
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)
    
    let start = currentPage.value - 1
    let end = currentPage.value + 1
    
    if (start <= 2) {
      start = 2
      end = start + 2
    } else if (end >= totalPages.value - 1) {
      end = totalPages.value - 1
      start = end - 2
    }
    
    if (start > 2) pages.push('...')
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    if (end < totalPages.value - 1) pages.push('...')
    
    pages.push(totalPages.value)
  }
  
  return pages
})

// 添加格式化函数
const formatPrice = (price, market) => {
  if (!price) return '-'
  const currency = market === 'HK' ? 'HKD' : 'USD'
  return `${price} ${currency}`
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return new Date(datetime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-')
}

// 初始化
onMounted(() => {
  fetchStocks()
})
</script>

<style scoped>
.card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #dee2e6;
  background-color: #fff;
  margin: 1.5rem 2.5rem;
  border-radius: 0.5rem;
  max-width: 1600px;
}

.container-fluid {
  padding: 0;
  display: flex;
  justify-content: center;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 1.25rem 1.5rem;
  border-top-left-radius: 0.5rem;
  border-top-right-radius: 0.5rem;
}

.card-body {
  padding: 1rem 1.25rem !important;
}

.table-responsive {
  margin: 0;
  border: 1·px solid #dee2e6;
  border-radius: 0.375rem;
  background-color: #fff;
}

.table {
  margin-bottom: 0;
  font-size: 0.875rem;
  background-color: #fff;
}

.table th:first-child {
  border-top-left-radius: 0.375rem;
}

.table th:last-child {
  border-top-right-radius: 0.375rem;
}

.table tr:last-child td:first-child {
  border-bottom-left-radius: 0.375rem;
}

.table tr:last-child td:last-child {
  border-bottom-right-radius: 0.375rem;
}

.table th {
  padding: 0.75rem 1rem;
  font-weight: 500;
  border-bottom: 1px solid #dee2e6;
  background-color: #f8f9fa;
  white-space: nowrap;
  color: #495057;
}

.table td {
  padding: 0.75rem 1rem;
  vertical-align: middle;
  border-bottom: 1px solid #dee2e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-footer {
  background-color: #fff;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1.5rem;
  border-bottom-left-radius: 0.5rem;
  border-bottom-right-radius: 0.5rem;
}

.btn-link {
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}

.form-select,
.form-control {
  border-color: #dee2e6;
  padding: 0.375rem 0.75rem;
}

.form-select:focus,
.form-control:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

.btn-primary {
  padding: 0.375rem 1rem;
}

.text-primary {
  color: #0d6efd !important;
}

.text-danger {
  color: #dc3545 !important;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.25rem 0.4rem;
  font-size: 0.75rem;
}

.badge {
  font-weight: normal;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  min-width: 45px;
}

.bg-danger {
  background-color: #e6071d !important;
}

.bg-primary {
  background-color: #0d6efd !important;
}

.font-monospace {
  font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.875rem;
}

.btn-xs {
  padding: 0.1rem 0.3rem;
  font-size: 0.75rem;
  line-height: 1.2;
}

.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
</style> 