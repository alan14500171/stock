<template>
  <div class="container-fluid" v-permission="'dashboard:view'">
    <div class="row mb-4">
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">持仓总览</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0">{{ formatCurrency(totalValue) }}</h3>
                <small class="text-muted">当前总市值</small>
              </div>
              <div class="text-end">
                <div :class="['fs-5', getProfitLossClass(totalProfitLoss)]">
                  {{ formatProfitLoss(totalProfitLoss) }}
                </div>
                <small class="text-muted">总盈亏</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">今日变动</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0">{{ formatCurrency(todayChange) }}</h3>
                <small class="text-muted">金额变动</small>
              </div>
              <div class="text-end">
                <div :class="['fs-5', getProfitLossClass(todayChangePercent)]">
                  {{ formatPercent(todayChangePercent) }}
                </div>
                <small class="text-muted">百分比</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">持仓数量</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0">{{ totalStocks }}</h3>
                <small class="text-muted">股票数量</small>
              </div>
              <div class="text-end">
                <div class="fs-5">{{ totalTransactions }}</div>
                <small class="text-muted">交易记录</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">市场分布</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0">{{ formatCurrency(hkValue) }}</h3>
                <small class="text-muted">港股市值</small>
              </div>
              <div class="text-end">
                <h3 class="mb-0">{{ formatCurrency(usValue) }}</h3>
                <small class="text-muted">美股市值</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row mb-4">
      <div class="col-lg-8 mb-3">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">持仓分布</h5>
            <div class="btn-group">
              <button 
                class="btn btn-sm" 
                :class="chartView === 'value' ? 'btn-primary' : 'btn-outline-primary'"
                @click="chartView = 'value'"
              >
                市值
              </button>
              <button 
                class="btn btn-sm" 
                :class="chartView === 'profit' ? 'btn-primary' : 'btn-outline-primary'"
                @click="chartView = 'profit'"
              >
                盈亏
              </button>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:300px;">
              <canvas id="portfolioChart"></canvas>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-lg-4 mb-3">
        <div class="card h-100">
          <div class="card-header">
            <h5 class="mb-0">市场占比</h5>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:300px;">
              <canvas id="marketChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">持仓明细</h5>
            <button class="btn btn-sm btn-outline-primary" @click="refreshData">
              <i class="bi bi-arrow-clockwise me-1"></i>刷新数据
            </button>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>股票</th>
                    <th>持仓数量</th>
                    <th>平均成本</th>
                    <th>当前价格</th>
                    <th>市值</th>
                    <th>盈亏</th>
                    <th>盈亏比例</th>
                    <th>今日变动</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="position in positions" :key="position.stock_id">
                    <td>
                      <div class="d-flex align-items-center">
                        <span class="badge me-2" :class="position.market === 'HK' ? 'bg-danger' : 'bg-primary'">
                          {{ position.market }}
                        </span>
                        <div>
                          <div class="fw-bold">{{ position.stock_code }}</div>
                          <small class="text-muted">{{ position.stock_name }}</small>
                        </div>
                      </div>
                    </td>
                    <td>{{ formatNumber(position.quantity) }}</td>
                    <td>{{ formatPrice(position.avg_cost, position.market) }}</td>
                    <td>{{ formatPrice(position.current_price, position.market) }}</td>
                    <td>{{ formatCurrency(position.market_value) }}</td>
                    <td :class="getProfitLossClass(position.profit_loss)">
                      {{ formatCurrency(position.profit_loss) }}
                    </td>
                    <td :class="getProfitLossClass(position.profit_loss_percent)">
                      {{ formatPercent(position.profit_loss_percent) }}
                    </td>
                    <td :class="getProfitLossClass(position.today_change_percent)">
                      {{ formatPercent(position.today_change_percent) }}
                    </td>
                  </tr>
                  <tr v-if="positions.length === 0">
                    <td colspan="8" class="text-center py-3">
                      <div class="text-muted">暂无持仓数据</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 