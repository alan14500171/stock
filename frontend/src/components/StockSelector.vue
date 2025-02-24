<template>
  <div class="stock-selector">
    <div class="selected-items form-control" @click="showDropdown = !showDropdown">
      <div v-for="code in modelValue" :key="code" class="selected-tag">
        {{ getStockLabel(code) }}
        <button type="button" class="btn-close" @click.stop="removeStock(code)"></button>
      </div>
      <small v-if="modelValue.length === 0" class="text-muted">{{ placeholder }}</small>
    </div>
    <div class="dropdown-menu" :class="{ show: showDropdown }">
      <!-- 搜索框 -->
      <div class="search-container">
        <input
          type="text"
          class="search-input"
          :value="searchText"
          @input="handleInput"
          @keydown.enter="handleEnter"
          @keydown.up.prevent="navigateList('up')"
          @keydown.down.prevent="navigateList('down')"
          :placeholder="'搜索股票代码或名称...'"
          ref="input"
          @click="handleInputClick"
        />
      </div>

      <!-- 全选/取消全选和清空选择 -->
      <div class="dropdown-header d-flex justify-content-between align-items-center">
        <div class="select-all">
          <input 
            type="checkbox" 
            class="form-check-input me-2" 
            :checked="isAllSelected"
            @change="toggleSelectAll"
            :indeterminate="isIndeterminate"
          >
          <span>全选</span>
        </div>
        <div class="d-flex align-items-center gap-3">
          <small class="text-muted">已选 {{ modelValue.length }} 项</small>
          <button 
            v-if="modelValue.length > 0"
            type="button" 
            class="btn btn-link btn-sm p-0 text-danger" 
            @click="clearSelected"
          >
            清空选择
          </button>
        </div>
      </div>

      <!-- 股票列表 -->
      <div class="stock-list">
        <template v-if="filteredStocks.length > 0">
          <a
            v-for="(stock, index) in filteredStocks"
            :key="stock.code"
            class="dropdown-item"
            :class="{ 'active': index === currentIndex }"
            href="#"
            @click.prevent="toggleStock(stock)"
            @mouseover="currentIndex = index"
          >
            <input 
              type="checkbox" 
              class="form-check-input me-2" 
              :checked="isSelected(stock.code)"
            >
            {{ stock.code }} - {{ stock.name }}
          </a>
        </template>
        <div v-else class="dropdown-item text-muted">
          无匹配结果
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { debounce } from 'lodash'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  stocks: {
    type: Array,
    default: () => []
  },
  market: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '输入代码或名称搜索'
  }
})

const emit = defineEmits(['update:modelValue', 'enter'])

// 搜索和过滤
const searchText = ref('')
const showDropdown = ref(false)
const input = ref(null)

// 添加键盘导航相关的状态
const currentIndex = ref(-1)

// 计算过滤后的股票列表
const filteredStocks = computed(() => {
  let result = props.stocks
  if (props.market) {
    result = result.filter(stock => stock.market === props.market)
  }
  if (searchText.value) {
    const searchValue = searchText.value.toLowerCase()
    result = result.filter(stock => 
      stock.code.toLowerCase().includes(searchValue) || 
      stock.name.toLowerCase().includes(searchValue)
    )
  }
  return result
})

// 全选状态
const isAllSelected = computed(() => {
  return filteredStocks.value.length > 0 && 
         filteredStocks.value.every(stock => isSelected(stock.code))
})

const isIndeterminate = computed(() => {
  const selectedCount = filteredStocks.value.filter(stock => isSelected(stock.code)).length
  return selectedCount > 0 && selectedCount < filteredStocks.value.length
})

// 获取股票显示标签
const getStockLabel = (code) => {
  const stock = props.stocks.find(s => s.code === code)
  return stock ? `${stock.code} - ${stock.name}` : code
}

// 检查股票是否已选中
const isSelected = (code) => {
  return props.modelValue.includes(code)
}

// 切换全选/取消全选
const toggleSelectAll = () => {
  const newValue = [...props.modelValue]
  if (isAllSelected.value) {
    // 取消全选
    filteredStocks.value.forEach(stock => {
      const index = newValue.indexOf(stock.code)
      if (index !== -1) {
        newValue.splice(index, 1)
      }
    })
  } else {
    // 全选
    filteredStocks.value.forEach(stock => {
      if (!newValue.includes(stock.code)) {
        newValue.push(stock.code)
      }
    })
  }
  emit('update:modelValue', newValue)
}

// 清空所有选择
const clearSelected = () => {
  emit('update:modelValue', [])
}

// 切换单个股票选中状态
const toggleStock = (stock) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(stock.code)
  if (index === -1) {
    newValue.push(stock.code)
  } else {
    newValue.splice(index, 1)
  }
  emit('update:modelValue', newValue)
}

// 处理键盘导航
const navigateList = (direction) => {
  if (!showDropdown.value || filteredStocks.value.length === 0) {
    return
  }

  if (direction === 'up') {
    currentIndex.value = currentIndex.value <= 0 
      ? filteredStocks.value.length - 1 
      : currentIndex.value - 1
  } else {
    currentIndex.value = currentIndex.value >= filteredStocks.value.length - 1 
      ? 0 
      : currentIndex.value + 1
  }

  // 确保当前选中项在可视区域内
  const stockList = document.querySelector('.stock-list')
  const activeItem = stockList.querySelector('.dropdown-item.active')
  if (activeItem) {
    activeItem.scrollIntoView({ block: 'nearest' })
  }
}

// 处理回车键
const handleEnter = (event) => {
  if (showDropdown.value && filteredStocks.value.length > 0) {
    event.preventDefault()
    if (currentIndex.value >= 0) {
      toggleStock(filteredStocks.value[currentIndex.value])
    } else {
      toggleStock(filteredStocks.value[0])
    }
  } else {
    emit('enter', event)
  }
}

// 处理输入
const handleInput = (event) => {
  searchText.value = event.target.value
  showDropdown.value = true
  currentIndex.value = -1  // 重置选中索引
}

// 监听下拉框显示状态
watch(showDropdown, (newValue) => {
  if (!newValue) {
    currentIndex.value = -1  // 关闭下拉框时重置选中索引
    searchText.value = ''
  }
})

// 删除已选择的股票
const removeStock = (code) => {
  const newValue = props.modelValue.filter(item => item !== code)
  emit('update:modelValue', newValue)
}

// 处理输入框点击
const handleInputClick = (event) => {
  event.stopPropagation()
  if (!showDropdown.value) {
    showDropdown.value = true
  }
}

// 点击外部关闭下拉框
const handleClickOutside = (event) => {
  if (!event.target.closest('.stock-selector')) {
    showDropdown.value = false
    searchText.value = ''
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.stock-selector {
  position: relative;
  min-width: 300px;
  width: 100%;
}

.selected-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  min-height: calc(1.5em + 0.75rem + 2px);
  max-height: calc(4.5em + 0.75rem + 2px);
  padding: 0.25rem;
  cursor: pointer;
  background-color: #fff;
  align-items: flex-start;
  overflow-y: auto;
}

.selected-items::-webkit-scrollbar {
  width: 4px;
}

.selected-items::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.selected-items::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  padding: 0.125rem 0.375rem;
  font-size: 0.75rem;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 1px;
  border: 1px solid #dee2e6;
  flex-shrink: 0;
  color: #495057;
}

.selected-tag .btn-close {
  font-size: 0.675rem;
  margin-left: 0.375rem;
  padding: 0.125rem;
  opacity: 0.5;
  min-width: 12px;
  min-height: 12px;
}

.selected-tag .btn-close:hover {
  opacity: 1;
}

.search-input {
  width: 100%;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #212529;
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.search-input:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
}

.dropdown-menu {
  width: 100%;
  margin-top: 1px;
  padding: 0;
  max-height: 350px;
  overflow-y: hidden;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  display: none;
  flex-direction: column;
}

.dropdown-menu.show {
  display: flex;
}

.dropdown-menu::-webkit-scrollbar {
  width: 6px;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.sticky-top {
  position: sticky;
  top: 0;
  background-color: #fff;
  z-index: 1;
  border-bottom: 1px solid #dee2e6;
}

.dropdown-header {
  font-size: 0.75rem;
  color: #6c757d;
  padding: 0.5rem 0.75rem;
  background-color: #f8f9fa;
}

.select-all {
  display: flex;
  align-items: center;
  user-select: none;
}

.select-all input[type="checkbox"] {
  cursor: pointer;
}

.dropdown-divider {
  margin: 0;
  border-color: #dee2e6;
}

.dropdown-item {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  color: #212529;
  text-decoration: none;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item input[type="checkbox"] {
  cursor: pointer;
}

.form-check-input {
  margin: 0;
}

.stock-list {
  overflow-y: auto;
  flex: 1;
}

.gap-3 {
  gap: 0.75rem;
}

.btn-link {
  text-decoration: none;
  font-size: 0.75rem;
  cursor: pointer;
}

.btn-link:hover {
  text-decoration: underline;
}

.text-danger {
  color: #dc3545;
}

.text-danger:hover {
  color: #bb2d3b;
}

.dropdown-item.active {
  background-color: #e9ecef;
  color: #212529;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item.active:hover {
  background-color: #e9ecef;
}
</style> 