<template>
  <div class="modal fade" id="transactionSplitModal" tabindex="-1" aria-labelledby="transactionSplitModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">交易分单</h5>
          <button type="button" class="btn-close" @click="hideModal"></button>
        </div>
        <div class="modal-body">
          <!-- 交易详情区域 -->
          <div class="card mb-3" v-if="transaction">
            <div class="card-header bg-light">
              <h5 class="mb-0">交易详情</h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">交易编号</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ transaction.transaction_code }}</p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">交易日期</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ formatTransactionDate(transaction.transaction_date) }}</p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">股票代码</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">
                        <span class="badge me-1" :class="transaction.market === 'HK' ? 'bg-danger' : 'bg-primary'">
                          {{ transaction.market }}
                        </span>
                        {{ transaction.stock_code }}
                      </p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">股票名称</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ transaction.stock_name }}</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">交易类型</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">
                        <span class="badge" :class="transaction.transaction_type.toLowerCase() === 'buy' ? 'bg-success' : 'bg-danger'">
                          {{ transaction.transaction_type.toLowerCase() === 'buy' ? '买入' : '卖出' }}
                        </span>
                      </p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">总数量</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ formatNumber(transaction.total_quantity) }}</p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">总金额</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ formatCurrency(transaction.total_amount) }}</p>
                    </div>
                  </div>
                  <div class="mb-3 row">
                    <label class="col-sm-4 col-form-label">总费用</label>
                    <div class="col-sm-8">
                      <p class="form-control-plaintext">{{ formatCurrency(transaction.total_fees) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 分单表单区域 -->
          <div class="card mb-3" v-if="transaction">
            <div class="card-header bg-light d-flex justify-content-between align-items-center">
              <h5 class="mb-0">分单设置</h5>
              <button class="btn btn-sm btn-outline-primary" @click="addSplitItem">
                <i class="bi bi-plus-circle"></i> 添加持有人
              </button>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th style="width: 30%">持有人</th>
                      <th style="width: 15%">分配比例 (%)</th>
                      <th style="width: 15%">数量</th>
                      <th style="width: 15%">金额</th>
                      <th style="width: 15%">费用</th>
                      <th style="width: 10%">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in splitItems" :key="index">
                      <td>
                        <select class="form-select" v-model="item.holder_id" @change="onHolderChange(item, index)">
                          <option value="">请选择持有人</option>
                          <option v-for="holder in holders" :key="holder.id" :value="holder.id">
                            {{ holder.display_name }}
                          </option>
                        </select>
                      </td>
                      <td>
                        <div class="input-group">
                          <input
                            type="number"
                            class="form-control"
                            v-model="item.ratio"
                            min="0"
                            max="100"
                            step="0.01"
                            @input="onRatioChange(item, index)"
                          />
                          <span class="input-group-text">%</span>
                        </div>
                      </td>
                      <td>
                        <input
                          type="number"
                          class="form-control"
                          v-model="item.quantity"
                          min="0"
                          :max="transaction.total_quantity"
                          @input="onQuantityChange(item, index)"
                        />
                      </td>
                      <td>
                        <p class="form-control-plaintext text-end">{{ formatCurrency(item.amount) }}</p>
                      </td>
                      <td>
                        <p class="form-control-plaintext text-end">{{ formatCurrency(item.fees) }}</p>
                      </td>
                      <td>
                        <button
                          class="btn btn-sm btn-outline-danger"
                          @click="removeSplitItem(index)"
                          :disabled="splitItems.length <= 1"
                        >
                          <i class="bi bi-trash"></i>
                        </button>
                      </td>
                    </tr>
                    <tr class="table-light">
                      <td class="fw-bold">合计</td>
                      <td class="text-end fw-bold" :class="Math.abs(totalRatio - 100) > 0.01 ? 'text-danger' : ''">
                        {{ totalRatio.toFixed(2) }}%
                      </td>
                      <td class="text-end fw-bold" :class="totalQuantity !== transaction.total_quantity ? 'text-danger' : ''">
                        {{ formatNumber(totalQuantity) }}
                      </td>
                      <td class="text-end fw-bold">{{ formatCurrency(totalAmount) }}</td>
                      <td class="text-end fw-bold">{{ formatCurrency(totalFees) }}</td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="alert alert-warning" v-if="Math.abs(totalRatio - 100) > 0.01">
                <i class="bi bi-exclamation-triangle"></i> 分配比例总和必须等于100%
              </div>
              <div class="alert alert-warning" v-if="totalQuantity !== transaction.total_quantity">
                <i class="bi bi-exclamation-triangle"></i> 分配数量总和必须等于交易总数量
              </div>
            </div>
          </div>

          <!-- 分单历史区域 -->
          <div class="card" v-if="transaction && splitHistory && splitHistory.length > 0">
            <div class="card-header bg-light">
              <h5 class="mb-0">分单历史</h5>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-bordered mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>持有人</th>
                      <th>分配比例</th>
                      <th>数量</th>
                      <th>金额</th>
                      <th>费用</th>
                      <th>创建时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in splitHistory" :key="index">
                      <td>{{ item.holder_display_name || item.holder_name }}</td>
                      <td>{{ formatSplitRatio(item.split_ratio) }}%</td>
                      <td>{{ formatNumber(item.total_quantity) }}</td>
                      <td>{{ formatCurrency(item.total_amount) }}</td>
                      <td>{{ formatCurrency(item.total_fees) }}</td>
                      <td>{{ item.created_at }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- 加载中状态 -->
          <div class="text-center py-5" v-if="loading">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在加载交易数据...</p>
          </div>

          <!-- 未找到交易记录 -->
          <div class="alert alert-warning" v-if="notFound">
            <i class="bi bi-exclamation-triangle"></i> 未找到交易记录，请检查交易编号是否正确
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="hideModal">关闭</button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="saveSplit" 
            :disabled="saveDisabled || savingData"
            v-if="transaction"
          >
            <span class="spinner-border spinner-border-sm me-1" v-if="savingData"></span>
            保存分单
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import * as bootstrap from 'bootstrap'

const props = defineProps({
  transactionId: {
    type: [Number, String],
    default: null
  },
  transactionCode: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['saved', 'hidden'])

const toast = useToast()

// 数据状态
const transaction = ref(null)
const splitItems = ref([])
const holders = ref([])
const splitHistory = ref([])
const loading = ref(false)
const notFound = ref(false)
const savingData = ref(false)
const splitModal = ref(null)

// 格式化数字
const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString()
}

// 格式化货币
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

// 格式化交易日期
const formatTransactionDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 计算属性
const totalRatio = computed(() => {
  return splitItems.value.reduce((sum, item) => sum + Number(item.ratio || 0), 0)
})

const totalQuantity = computed(() => {
  return splitItems.value.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
})

const totalAmount = computed(() => {
  return splitItems.value.reduce((sum, item) => sum + Number(item.amount || 0), 0)
})

const totalFees = computed(() => {
  return splitItems.value.reduce((sum, item) => sum + Number(item.fees || 0), 0)
})

const saveDisabled = computed(() => {
  return (
    !transaction.value ||
    Math.abs(totalRatio.value - 100) > 0.01 ||
    totalQuantity.value !== transaction.value?.total_quantity ||
    splitItems.value.some(item => !item.holder_id)
  )
})

// 初始化模态框
const initModal = () => {
  if (typeof window !== 'undefined' && window.bootstrap) {
    const modalElement = document.getElementById('transactionSplitModal');
    if (modalElement) {
      // 销毁旧的模态框实例
      const oldModal = bootstrap.Modal.getInstance(modalElement);
      if (oldModal) {
        oldModal.dispose();
      }
      
      // 创建新模态框实例
      splitModal.value = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: false
      });
      
      // 监听模态框关闭事件
      modalElement.addEventListener('hidden.bs.modal', handleModalHidden);
    }
  }
};

// 处理模态框隐藏事件
const handleModalHidden = () => {
  // 重置表单状态
  resetSplitItems();
  transaction.value = null;
  splitHistory.value = [];
  notFound.value = false;
  loading.value = false;
  savingData.value = false;
  
  // 通知父组件模态框已关闭
  emit('hidden');
};

// 重置分单项
const resetSplitItems = () => {
  console.log('重置分单项，当前交易数据:', transaction.value);
  
  if (!transaction.value) {
    console.log('交易数据为空，设置空分单项');
    splitItems.value = [];
    return;
  }
  
  // 创建一个默认的100%分单
  splitItems.value = [{
    holder_id: '',
    holder_name: '',
    ratio: 100,
    quantity: transaction.value.total_quantity || 0,
    amount: transaction.value.total_amount || 0,
    fees: transaction.value.total_fees || 0
  }];
  
  console.log('已创建默认分单项:', splitItems.value);
};

// 加载持有人列表
const loadHolders = async () => {
  try {
    const response = await axios.get('/api/transaction/get_users');
    if (response.data.success) {
      holders.value = response.data.data;
      console.log('加载持有人列表成功:', holders.value);
    } else {
      console.error('加载持有人列表失败:', response.data.message);
      toast.error('加载持有人列表失败: ' + response.data.message);
    }
  } catch (error) {
    console.error('加载持有人列表失败:', error);
    toast.error('加载持有人列表失败，请稍后重试');
  }
};

// 显示模态框
const showModal = async (data) => {
  console.log('showModal被调用，传入数据:', data);
  
  if (!splitModal.value) {
    initModal();
  }
  
  // 重置状态
  loading.value = true;
  notFound.value = false;
  transaction.value = null;
  splitItems.value = [];
  splitHistory.value = []; // 确保初始化为空数组
  
  try {
    // 加载持有人列表
    await loadHolders();
    
    if (data) {
      // 直接使用传入的交易数据
      transaction.value = data;
      console.log('设置交易数据:', transaction.value);
      
      // 检查交易是否存在分单记录
      if (data.has_splits && data.transaction_code) {
        try {
          await loadSplitHistory(data.transaction_code);
        } catch (error) {
          console.error('加载分单历史记录失败:', error);
          splitHistory.value = []; // 确保初始化为空数组
          resetSplitItems();
        }
      } else {
        // 创建一个默认的100%分单
        splitHistory.value = []; // 确保初始化为空数组
        resetSplitItems();
      }
    } else if (props.transactionId || props.transactionCode) {
      // 如果没有传入数据，但有ID或编号，则加载交易记录
      await loadTransaction();
    } else {
      console.warn('没有提供交易数据，无法显示分单模态框');
      return;
    }
  } catch (error) {
    console.error('初始化分单模态框失败:', error);
    toast.error('初始化分单模态框失败: ' + error.message);
  } finally {
    loading.value = false;
  }
  
  // 显示模态框
  if (splitModal.value) {
    splitModal.value.show();
  }
};

// 隐藏模态框
const hideModal = () => {
  if (splitModal.value) {
    splitModal.value.hide();
  }
};

// 加载交易记录
const loadTransaction = async (transactionCode = null) => {
  // 优先使用传入的参数，其次使用props
  const code = transactionCode || props.transactionCode
  const id = props.transactionId
  
  if (!code && !id) {
    return
  }

  loading.value = true
  notFound.value = false
  transaction.value = null
  splitItems.value = []
  splitHistory.value = [] // 确保初始化为空数组

  try {
    let response
    if (code) {
      response = await axios.get(`/api/transaction/get_by_code`, {
        params: { transaction_code: code }
      })
    } else if (id) {
      response = await axios.get(`/api/transaction/${id}`)
    }

    if (response && response.data.success) {
      transaction.value = response.data.data
      
      // 确保持有人列表已加载
      await loadUsers()
      
      // 加载分单历史
      if (transaction.value && transaction.value.transaction_code) {
        await loadSplitHistory(transaction.value.transaction_code)
      } else {
        console.warn('交易记录缺少transaction_code，无法加载分单历史')
        splitHistory.value = [] // 确保初始化为空数组
        resetSplitItems()
      }
      
      // 如果已有分单记录，自动填充到表单中
      if (splitHistory.value && splitHistory.value.length > 0) {
        // 清空现有分单项
        splitItems.value = []
        
        // 将历史分单记录填充到表单中
        splitHistory.value.forEach(historyItem => {
          // 查找完整的持有人信息
          const holder = holders.value.find(h => h.id === historyItem.holder_id)
          
          // 处理比例值，确保正确显示
          let ratio = historyItem.split_ratio;
          
          // 验证split_ratio
          if (typeof ratio === 'string') {
            ratio = parseFloat(ratio);
          }
          
          // 确保值在合理范围内
          if (ratio > 100) {
            console.warn(`比例值超过100: ${ratio}，将重置为100`);
            ratio = 100;
          } else if (ratio < 0) {
            console.warn(`检测到负比例值: ${ratio}，将重置为0`);
            ratio = 0;
          }
          
          console.log(`处理后的比例值: ${ratio}`);
          
          const splitItem = {
            holder_id: historyItem.holder_id,
            holder_name: holder ? holder.display_name : historyItem.holder_name || `持有人ID: ${historyItem.holder_id}`,
            ratio: ratio, // 使用处理后的比例值
            quantity: historyItem.total_quantity,
            amount: historyItem.total_amount,
            fees: historyItem.total_fees
          }
          splitItems.value.push(splitItem)
          
          console.log(`填充持有人: ID=${splitItem.holder_id}, 名字=${splitItem.holder_name}, 比例=${splitItem.ratio}%`)
        })
        
        console.log('已填充历史分单记录:', splitItems.value)
      } else {
        // 如果没有分单记录，初始化一个分单项目
        addSplitItem()
      }
    }
  } catch (error) {
    console.error('查询交易记录失败:', error)
    if (error.response && error.response.status === 404) {
      notFound.value = true
      toast.error('未找到交易记录，请检查交易编号是否正确')
    } else {
      toast.error('查询交易记录失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const response = await axios.get('/api/transaction/get_users')
    if (response.data.success) {
      holders.value = response.data.data
      console.log('加载持有人列表成功:', holders.value)
      
      // 检查每个持有人的display_name
      holders.value.forEach(holder => {
        if (!holder.display_name) {
          console.warn(`警告: 持有人 ID=${holder.id} 没有display_name`)
        }
      })
    }
  } catch (error) {
    console.error('加载持有人列表失败:', error)
    toast.error('加载持有人列表失败，请稍后重试')
  }
}

// 加载分单历史记录
const loadSplitHistory = async (transactionCode) => {
  if (!transactionCode) {
    console.error('加载分单历史记录失败: 交易编号为空');
    splitHistory.value = []; // 确保初始化为空数组
    resetSplitItems();
    return;
  }

  console.log(`正在加载交易编号 ${transactionCode} 的分单历史记录`);
  
  try {
    const response = await axios.get(`/api/transaction/split/${transactionCode}`);
    console.log('分单历史记录API响应:', response.data);
    
    if (response.data.success) {
      splitHistory.value = response.data.data || []; // 确保即使返回null也初始化为空数组
      console.log('获取到分单历史记录:', splitHistory.value);
      
      // 如果有历史记录，用它来初始化当前的分单项
      if (splitHistory.value && splitHistory.value.length > 0) {
        // 转换历史记录格式到当前使用的格式
        splitItems.value = splitHistory.value.map(item => ({
          holder_id: item.holder_id,
          holder_name: item.holder_name,
          ratio: parseFloat(item.split_ratio) * 100, // 转换为百分比
          quantity: item.total_quantity,
          amount: item.total_amount,
          fees: item.total_fees
        }));
        console.log('已填充历史分单记录:', splitItems.value);
      } else {
        console.log('没有分单历史记录，使用默认分单');
        resetSplitItems();
      }
    } else {
      console.warn('获取分单历史记录失败:', response.data.message);
      splitHistory.value = []; // 确保初始化为空数组
      resetSplitItems();
    }
  } catch (error) {
    console.error('获取分单历史记录失败:', error);
    splitHistory.value = []; // 确保初始化为空数组
    resetSplitItems();
    toast.error('获取分单历史记录失败，将使用默认分单');
  }
};

// 添加分单项
const addSplitItem = () => {
  const remainingRatio = 100 - totalRatio.value
  const remainingQuantity = transaction.value ? transaction.value.total_quantity - totalQuantity.value : 0
  
  const newItem = {
    holder_id: '',
    holder_name: '',
    ratio: remainingRatio > 0 ? remainingRatio : 0,
    quantity: remainingQuantity > 0 ? remainingQuantity : 0,
    amount: 0,
    fees: 0
  }
  
  calculateSplitItemValues(newItem)
  splitItems.value.push(newItem)
}

// 移除分单项
const removeSplitItem = (index) => {
  if (splitItems.value.length <= 1) return
  
  splitItems.value.splice(index, 1)
  
  // 重新计算剩余项的值
  splitItems.value.forEach(item => {
    calculateSplitItemValues(item)
  })
}

// 持有人变更
const onHolderChange = (item, index) => {
  if (item.holder_id) {
    const holder = holders.value.find(h => h.id === item.holder_id)
    if (holder) {
      item.holder_name = holder.display_name
      console.log(`设置持有人名字: ID=${item.holder_id}, 名字=${item.holder_name}, 原始数据=`, holder)
    } else {
      console.warn(`未找到持有人: ID=${item.holder_id}`)
      item.holder_name = `持有人ID: ${item.holder_id}`
      
      // 尝试重新加载持有人列表
      loadUsers().then(() => {
        // 再次尝试查找持有人
        const reloadedHolder = holders.value.find(h => h.id === item.holder_id)
        if (reloadedHolder) {
          item.holder_name = reloadedHolder.display_name
          console.log(`重新加载后设置持有人名字: ID=${item.holder_id}, 名字=${item.holder_name}, 原始数据=`, reloadedHolder)
        }
      })
    }
  } else {
    item.holder_name = ''
    console.log('清除持有人名字')
  }
}

// 比例变更
const onRatioChange = (item, index) => {
  // 输入值限制
  let ratioValue = Number(item.ratio);
  
  if (isNaN(ratioValue)) {
    console.warn(`比例输入非数字: ${item.ratio}，已重置为0`);
    ratioValue = 0;
  }
  
  if (ratioValue < 0) {
    ratioValue = 0;
  }
  
  if (ratioValue > 100) {
    console.warn(`比例输入值超过100%: ${ratioValue}，已重置为100`);
    ratioValue = 100;
  }
  
  // 更新为处理后的值
  item.ratio = ratioValue;
  
  // 根据比例计算数量
  if (transaction.value) {
    item.quantity = Math.round(transaction.value.total_quantity * (item.ratio / 100))
  }
  
  calculateSplitItemValues(item)
}

// 数量变更
const onQuantityChange = (item, index) => {
  if (item.quantity < 0) item.quantity = 0
  if (transaction.value && item.quantity > transaction.value.total_quantity) {
    item.quantity = transaction.value.total_quantity
  }
  
  // 根据数量计算比例
  if (transaction.value && transaction.value.total_quantity > 0) {
    item.ratio = (item.quantity / transaction.value.total_quantity) * 100
  }
  
  calculateSplitItemValues(item)
}

// 计算分单项的金额和费用
const calculateSplitItemValues = (item) => {
  if (!transaction.value) return
  
  const ratio = Number(item.ratio) / 100
  
  // 计算金额
  item.amount = Number((transaction.value.total_amount * ratio).toFixed(2))
  
  // 计算费用
  item.fees = Number((transaction.value.total_fees * ratio).toFixed(2))
}

// 保存分单
const saveSplit = async () => {
  if (saveDisabled.value) return
  
  savingData.value = true
  
  try {
    // 确保每个分单项都有持有人名称
    splitItems.value.forEach(item => {
      if (item.holder_id && (!item.holder_name || item.holder_name.trim() === '')) {
        const holder = holders.value.find(h => h.id === item.holder_id)
        if (holder) {
          item.holder_name = holder.display_name || holder.name
          console.log(`设置缺失的持有人名称: ID=${item.holder_id}, 名称=${item.holder_name}`)
        } else {
          item.holder_name = `持有人ID: ${item.holder_id}`
          console.warn(`未找到持有人信息: ID=${item.holder_id}, 使用默认名称`)
        }
      }
    })
    
    // 准备提交的数据
    const data = {
      transaction_id: transaction.value.id,
      splits: splitItems.value.map(item => {
        // 确保ratio是0-1之间的小数
        let ratio = Number(item.ratio) / 100;
        
        // 验证处理后的ratio
        if (isNaN(ratio)) {
          console.warn(`比例转换错误: ${item.ratio} -> ${ratio}，将重置为0`);
          ratio = 0;
        } else if (ratio < 0) {
          console.warn(`比例小于0: ${ratio}，将重置为0`);
          ratio = 0;
        } else if (ratio > 1) {
          console.warn(`比例大于1: ${ratio}，将重置为1`);
          ratio = 1.0;
        }
        
        console.log(`提交分单项: 持有人=${item.holder_name}, 原始比例=${item.ratio}%, 转换后比例=${ratio}`);
        
        return {
          holder_id: item.holder_id,
          holder_name: item.holder_name, // 确保包含持有人名称
          ratio: ratio, // 转换为0-1之间的小数
          quantity: item.quantity,
          amount: item.amount,
          fees: item.fees
        };
      })
    }
    
    console.log('提交分单数据:', JSON.stringify(data))
    
    // 检查每个分单项的持有人名称
    data.splits.forEach((split, index) => {
      console.log(`分单项 #${index+1}: holder_id=${split.holder_id}, holder_name=${split.holder_name}`)
      if (!split.holder_name) {
        console.warn(`警告: 分单项 #${index+1} 的持有人名称为空`)
      }
    })
    
    const response = await axios.post('/api/transaction/split', data)
    
    console.log('分单保存响应:', response.data)
    
    if (response.data.success) {
      toast.success('分单保存成功')
      
      // 重新加载分单历史
      await loadSplitHistory()
      
      // 重新加载交易记录
      await loadTransaction(transaction.value.transaction_code)
      
      // 通知父组件保存成功
      emit('saved')
    } else {
      toast.error(`保存失败: ${response.data.message}`)
    }
  } catch (error) {
    console.error('保存分单失败:', error)
    if (error.response) {
      console.error('错误响应:', error.response.data)
    }
    toast.error(`保存分单失败: ${error.response?.data?.message || error.message || '未知错误'}`)
  } finally {
    savingData.value = false
  }
}

// 监听交易数据变化，重新计算分单项
watch(transaction, () => {
  if (transaction.value) {
    splitItems.value.forEach(item => {
      calculateSplitItemValues(item)
    })
  }
}, { deep: true })

// 监听props变化，加载交易记录
watch(() => [props.transactionId, props.transactionCode], () => {
  if (props.transactionId || props.transactionCode) {
    loadTransaction()
  }
}, { immediate: true })

// 组件挂载时初始化
onMounted(() => {
  console.log('组件挂载，开始初始化')
  // 使用setTimeout确保DOM已完全渲染
  setTimeout(() => {
    initModal()
    loadUsers()
  }, 100)
})

// 格式化分单比例
const formatSplitRatio = (ratioValue) => {
  // 检查是否为有效数字
  const ratio = parseFloat(ratioValue);
  if (isNaN(ratio)) return '';
  
  // 将比例值乘以100转换为百分比形式，保留2位小数
  return (ratio * 100).toFixed(2);
};

// 根据持有人ID设置持有人名称
const setHolderName = (item) => {
  const holder = holders.value.find(h => h.id === item.holder_id);
  if (holder) {
    item.holder_name = holder.name;
  } else if (item.holder_id && loadingHolders.value) {
    // 如果正在加载持有人，可能持有人列表还未完成加载
    // 在加载完成后重新尝试设置名称
    nextTick(() => {
      const reloadedHolder = holders.value.find(h => h.id === item.holder_id);
      if (reloadedHolder) {
        item.holder_name = reloadedHolder.name;
      }
    });
  } else {
    // 清除持有人名称，如果没有找到对应的持有人
    item.holder_name = '';
  }
};

// 检查并补全所有缺失的持有人名称
const ensureAllHolderNames = () => {
  splitItems.value.forEach(item => {
    if (item.holder_id && !item.holder_name) {
      setHolderName(item);
    }
  });
};

// 对外暴露方法
defineExpose({
  showModal,
  hideModal,
  loadTransaction,
  loadUsers
})
</script>

<style scoped>
.modal-xl {
  max-width: 1140px;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.table th {
  background-color: #f8f9fa;
}

.input-group-text {
  background-color: #f8f9fa;
}

.form-control-plaintext {
  padding-top: 0.375rem;
  padding-bottom: 0.375rem;
}
</style> 