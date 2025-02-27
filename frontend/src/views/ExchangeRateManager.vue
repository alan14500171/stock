<template>
  <div class="container-fluid">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">汇率管理</h5>
        <div class="btn-group">
          <button class="btn btn-primary btn-sm" @click="showAddDialog" v-permission="'exchange:rate:add'">
            <i class="bi bi-plus-lg"></i> 添加汇率
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="fetchMissingRates" v-permission="'exchange:rate:fetch'">
            <i class="bi bi-cloud-download"></i> 获取缺失汇率
          </button>
        </div>
      </div>

      <div class="card-body p-0" v-permission="'exchange:rate:view'">
        <div class="table-responsive">
          <table class="table table-hover table-sm mb-0">
            <thead class="table-light">
              <tr>
                <th>日期</th>
                <th>USD/HKD</th>
                <th>HKD/USD</th>
                <th>更新时间</th>
                <th class="text-end">操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="!loading">
                <template v-if="rates.length > 0">
                  <tr v-for="rate in rates" :key="rate.id">
                    <td>{{ formatDate(rate.date) }}</td>
                    <td>{{ formatNumber(rate.usd_to_hkd) }}</td>
                    <td>{{ formatNumber(rate.hkd_to_usd) }}</td>
                    <td>{{ formatDateTime(rate.updated_at) }}</td>
                    <td>
                      <div class="d-flex justify-content-end gap-1">
                        <button 
                          class="btn btn-link btn-xs p-0 text-primary" 
                          title="编辑" 
                          @click="editRate(rate)"
                          v-permission="'exchange:rate:edit'"
                        >
                          编辑
                        </button>
                        <button 
                          class="btn btn-link btn-xs p-0 text-danger ms-2" 
                          title="删除" 
                          @click="confirmDelete(rate)"
                          v-permission="'exchange:rate:delete'"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr v-else>
                  <td colspan="5" class="text-center py-3">
                    <div class="text-muted">暂无数据</div>
                  </td>
                </tr>
              </template>
              <tr v-else>
                <td colspan="5" class="text-center py-3">
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
                  <i class="bi bi-chevron-left"></i>
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
                  <i class="bi bi-chevron-right"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>

    <!-- 添加/编辑汇率对话框 -->
    <div class="modal fade" id="rateModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editData ? '编辑汇率' : '添加汇率' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-permission="editData ? 'exchange:rate:edit' : 'exchange:rate:add'">
            <form @submit.prevent="submitForm">
              <div class="mb-3">
                <label class="form-label">日期</label>
                <input 
                  type="date" 
                  class="form-control" 
                  v-model="form.date"
                  :class="{ 'is-invalid': errors.date }"
                  :readonly="!!editData"
                />
                <div class="invalid-feedback" v-if="errors.date">{{ errors.date }}</div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">USD/HKD 汇率</label>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="form.usd_to_hkd"
                  :class="{ 'is-invalid': errors.usd_to_hkd }"
                  step="0.0001"
                  min="0"
                />
                <div class="invalid-feedback" v-if="errors.usd_to_hkd">{{ errors.usd_to_hkd }}</div>
                <small class="form-text text-muted">1美元可兑换多少港元</small>
              </div>
              
              <div class="mb-3">
                <label class="form-label">HKD/USD 汇率</label>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="form.hkd_to_usd"
                  :class="{ 'is-invalid': errors.hkd_to_usd }"
                  step="0.0001"
                  min="0"
                />
                <div class="invalid-feedback" v-if="errors.hkd_to_usd">{{ errors.hkd_to_usd }}</div>
                <small class="form-text text-muted">1港元可兑换多少美元</small>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="submitForm"
              :disabled="submitting"
              v-permission="editData ? 'exchange:rate:edit' : 'exchange:rate:add'"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              {{ editData ? '保存' : '添加' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>确定要删除 <strong>{{ formatDate(selectedRate?.date) }}</strong> 的汇率记录吗？</p>
            <div class="alert alert-warning">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              此操作不可恢复！删除汇率可能会影响相关日期的交易记录计算。
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button 
              type="button" 
              class="btn btn-danger" 
              @click="deleteRate"
              :disabled="submitting"
              v-permission="'exchange:rate:delete'"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              确认删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Modal } from 'bootstrap/dist/js/bootstrap.bundle.min.js'
import DateInput from '../components/DateInput.vue'
import axios from 'axios'

// 状态
const loading = ref(false)
const submitting = ref(false)
const searchVisible = ref(false)
const isEdit = ref(false)
const exchangeRates = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 15
let modal = null

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  currency: ''
})

// 编辑表单
const form = reactive({
  id: null,
  rateDate: '',
  currency: '',
  rate: '',
  source: ''
})

// 表单错误
const errors = reactive({
  rateDate: '',
  currency: '',
  rate: ''
})

// 分页计算
const displayedPages = computed(() => {
  const pages = []
  const maxDisplayed = 7
  const sidePages = 2
  
  if (totalPages.value <= maxDisplayed) {
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    if (currentPage.value <= sidePages + 3) {
      for (let i = 1; i <= sidePages + 3; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    } else if (currentPage.value >= totalPages.value - (sidePages + 2)) {
      pages.push(1)
      pages.push('...')
      for (let i = totalPages.value - (sidePages + 2); i <= totalPages.value; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = currentPage.value - sidePages; i <= currentPage.value + sidePages; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    }
  }
  
  return pages
})

// 获取汇率列表
const fetchRates = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.startDate) params.append('start_date', searchForm.startDate)
    if (searchForm.endDate) params.append('end_date', searchForm.endDate)
    if (searchForm.currency) params.append('currency', searchForm.currency)
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    const response = await axios.get(`/api/stock/exchange_rates?${params.toString()}`)
    if (response.data.success) {
      exchangeRates.value = response.data.data.items
      totalPages.value = Math.ceil(response.data.data.total / pageSize)
    }
  } catch (error) {
    console.error('获取汇率列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 更新临时汇率
const updateTemporaryRates = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await axios.post('/api/stock/exchange_rates/fetch_missing')
    if (response.data.success) {
      // 显示成功消息
      alert(`成功更新 ${response.data.data.updated_count} 条临时汇率记录`)
      // 重新加载数据
      await fetchRates()
    }
  } catch (error) {
    console.error('更新临时汇率失败:', error)
    alert('更新临时汇率失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 搜索相关
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

const search = () => {
  currentPage.value = 1
  fetchRates()
}

const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.currency = ''
  currentPage.value = 1
  fetchRates()
}

// 分页相关
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchRates()
  }
}

// 模态框相关
const initModal = () => {
  modal = new Modal(document.getElementById('rateModal'))
}

const openAddModal = () => {
  isEdit.value = false
  resetForm()
  modal.show()
}

const openEditModal = (rate) => {
  isEdit.value = true
  resetForm()
  form.id = rate.id
  form.rateDate = rate.rate_date
  form.currency = rate.currency
  form.rate = rate.rate
  form.source = rate.source || ''
  modal.show()
}

const resetForm = () => {
  form.id = null
  form.rateDate = ''
  form.currency = ''
  form.rate = ''
  form.source = 'MANUAL'
  Object.keys(errors).forEach(key => errors[key] = '')
}

// 表单提交
const submitForm = async () => {
  if (submitting.value) return
  
  // 验证表单
  let isValid = true
  if (!form.rateDate) {
    errors.rateDate = '请选择日期'
    isValid = false
  }
  if (!form.currency) {
    errors.currency = '请选择货币'
    isValid = false
  }
  if (!form.rate) {
    errors.rate = '请输入汇率'
    isValid = false
  }
  
  if (!isValid) return
  
  submitting.value = true
  try {
    let response;
    
    if (isEdit.value) {
      // 编辑模式 - 使用PUT方法
      response = await axios.put(`/api/stock/exchange_rates/${form.id}`, {
        rate: form.rate,
        source: form.source
      });
    } else {
      // 添加模式
      response = await axios.post('/api/stock/exchange_rates', {
        rate_date: form.rateDate,
        currency: form.currency,
        rate: form.rate,
        source: form.source
      });
    }
    
    if (response.data.success) {
      modal.hide()
      await fetchRates()
    } else {
      alert(response.data.message || '操作失败')
    }
  } catch (error) {
    console.error('保存汇率失败:', error)
    alert(error.response?.data?.message || '保存失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 删除汇率
const confirmDelete = async (rate) => {
  if (!confirm('确定要删除这条汇率记录吗？')) return
  
  try {
    const response = await axios.delete(`/api/stock/exchange_rates/${rate.id}`)
    if (response.data.success) {
      await fetchRates()
    } else {
      alert(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除汇率失败:', error)
    alert(error.response?.data?.message || '删除失败，请稍后重试')
  }
}

// 工具函数
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

const formatDateTime = (datetime) => {
  return new Date(datetime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(/\//g, '-')
}

const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// 数据来源映射
const getSourceName = (source) => {
  if (!source) return '-'
  
  const sourceMap = {
    'TEMPORARY': '临时数据',
    'MANUAL': '手动修改',
    'EXCHANGE_RATES_API': '自动更新'
  }
  
  return sourceMap[source] || source
}

// 日期处理
const startDateDisplayValue = ref('')
const endDateDisplayValue = ref('')

// 引用
const startDate = ref(null)
const endDate = ref(null)
const currency = ref(null)
const searchBtn = ref(null)

// 焦点控制
const focusNext = (event, target) => {
  event.preventDefault()
  switch(target) {
    case 'endDate':
      endDate.value?.focus()
      break
    case 'currency':
      currency.value?.focus()
      break
    case 'search':
      searchBtn.value?.focus()
      search()
      break
  }
}

const handleStartDateInput = (event) => {
  const value = event.target.value
  startDateDisplayValue.value = value
  searchForm.startDate = value
}

const handleStartDateBlur = () => {
  if (!startDateDisplayValue.value) {
    searchForm.startDate = ''
    return
  }

  const value = startDateDisplayValue.value.trim()
  let formattedDate = null

  // 处理快捷输入
  if (/^[a-zA-Z]+$/.test(value)) {
    const now = new Date()
    switch (value.toLowerCase()) {
      case 't':
      case 'today':
        formattedDate = formatDate(now)
        break
      case 'y':
      case 'yday':
        now.setDate(now.getDate() - 1)
        formattedDate = formatDate(now)
        break
      case 'tm':
      case 'tmr':
        now.setDate(now.getDate() + 1)
        formattedDate = formatDate(now)
        break
    }
  }

  // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
  if (/^[+-]\d+$/.test(value)) {
    const days = parseInt(value)
    const date = new Date()
    date.setDate(date.getDate() + days)
    formattedDate = formatDate(date)
  }

  // 处理 MMDD 格式
  if (/^\d{3,4}$/.test(value)) {
    const now = new Date()
    const year = now.getFullYear()
    let month, day

    if (value.length === 3) {
      month = parseInt(value[0])
      day = parseInt(value.slice(1))
    } else {
      month = parseInt(value.slice(0, 2))
      day = parseInt(value.slice(2))
    }

    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      const date = new Date(year, month - 1, day)
      if (isValidDate(date)) {
        formattedDate = formatDate(date)
      }
    }
  }

  // 处理 M-D、M.D 或 M/D 格式
  const separators = ['-', '.', '/']
  for (const separator of separators) {
    if (value.includes(separator)) {
      const [month, day] = value.split(separator).map(Number)
      const now = new Date()
      const year = now.getFullYear()

      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day)
        if (isValidDate(date)) {
          formattedDate = formatDate(date)
          break
        }
      }
    }
  }

  // 处理标准格式
  if (!formattedDate) {
    const date = new Date(value)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate) {
    startDateDisplayValue.value = formattedDate
    searchForm.startDate = formattedDate
    // 如果开始日期大于结束日期，更新结束日期
    if (searchForm.endDate && formattedDate > searchForm.endDate) {
      searchForm.endDate = formattedDate
      endDateDisplayValue.value = formattedDate
    }
  }
}

const handleEndDateInput = (event) => {
  const value = event.target.value
  endDateDisplayValue.value = value
  searchForm.endDate = value
}

const handleEndDateBlur = () => {
  if (!endDateDisplayValue.value) {
    searchForm.endDate = ''
    return
  }

  const value = endDateDisplayValue.value.trim()
  let formattedDate = null

  // 处理快捷输入
  if (/^[a-zA-Z]+$/.test(value)) {
    const now = new Date()
    switch (value.toLowerCase()) {
      case 't':
      case 'today':
        formattedDate = formatDate(now)
        break
      case 'y':
      case 'yday':
        now.setDate(now.getDate() - 1)
        formattedDate = formatDate(now)
        break
      case 'tm':
      case 'tmr':
        now.setDate(now.getDate() + 1)
        formattedDate = formatDate(now)
        break
    }
  }

  // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
  if (/^[+-]\d+$/.test(value)) {
    const days = parseInt(value)
    const date = new Date()
    date.setDate(date.getDate() + days)
    formattedDate = formatDate(date)
  }

  // 处理 MMDD 格式
  if (/^\d{3,4}$/.test(value)) {
    const now = new Date()
    const year = now.getFullYear()
    let month, day

    if (value.length === 3) {
      month = parseInt(value[0])
      day = parseInt(value.slice(1))
    } else {
      month = parseInt(value.slice(0, 2))
      day = parseInt(value.slice(2))
    }

    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      const date = new Date(year, month - 1, day)
      if (isValidDate(date)) {
        formattedDate = formatDate(date)
      }
    }
  }

  // 处理 M-D、M.D 或 M/D 格式
  const separators = ['-', '.', '/']
  for (const separator of separators) {
    if (value.includes(separator)) {
      const [month, day] = value.split(separator).map(Number)
      const now = new Date()
      const year = now.getFullYear()

      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day)
        if (isValidDate(date)) {
          formattedDate = formatDate(date)
          break
        }
      }
    }
  }

  // 处理标准格式
  if (!formattedDate) {
    const date = new Date(value)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate) {
    endDateDisplayValue.value = formattedDate
    searchForm.endDate = formattedDate
    // 如果结束日期小于开始日期，更新开始日期
    if (searchForm.startDate && formattedDate < searchForm.startDate) {
      searchForm.startDate = formattedDate
      startDateDisplayValue.value = formattedDate
    }
  }
}

// 验证日期是否有效
const isValidDate = (date) => {
  return date instanceof Date && !isNaN(date)
}

// 生命周期钩子
onMounted(() => {
  initModal()
  fetchRates()
})
</script>

<style scoped>
/* 表格样式 */
.table {
  margin-bottom: 0;
}

.table th {
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem;
  border-bottom: 2px solid #dee2e6;
  background-color: #f8f9fa;
  color: #495057;
}

.table td {
  padding: 0.5rem;
  font-size: 0.875rem;
  vertical-align: middle;
  border-bottom: 1px solid #dee2e6;
}

/* 按钮样式 */
.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

/* 分页样式 */
.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.page-item.active .page-link {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

/* 卡片样式 */
.card {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border-radius: 0.5rem;
  background-color: #fff;
  margin: 1.5rem auto;
  max-width: 1400px;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem 0.5rem 0 0;
}

.card-body {
  padding: 1rem;
}

.card-footer {
  background-color: #fff;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
  border-radius: 0 0 0.5rem 0.5rem;
}

/* 表单样式 */
.form-label {
  margin-bottom: 0.25rem;
  color: #495057;
}

.form-select-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

/* 图标样式 */
.fas {
  width: 1rem;
  text-align: center;
  margin-right: 0.25rem;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .btn-group {
    width: 100%;
    justify-content: space-between;
  }
}

.btn-xs {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1;
  border-radius: 0.2rem;
  background-color: #fff;
}

.btn-outline-primary {
  border: 1px solid #dee2e6;
  color: #0d6efd;
}

.btn-outline-primary:hover {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
}

.btn-outline-primary:hover i {
  color: #fff !important;
}

.btn-outline-danger {
  border: 1px solid #dee2e6;
  color: #dc3545;
}

.btn-outline-danger:hover {
  background-color: #dc3545;
  border-color: #dc3545;
  color: #fff;
}

.btn-outline-danger:hover i {
  color: #fff !important;
}

.gap-1 {
  gap: 0.25rem !important;
}

.text-primary {
  color: #0d6efd !important;
}

.text-danger {
  color: #dc3545 !important;
}
</style> 