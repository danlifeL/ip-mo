<template>
  <div class="dashboard">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
          <el-button type="success" @click="showExportDialog">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          @change="handleAutoRefreshChange"
        />
        <el-select v-model="refreshInterval" size="small" style="width: 120px">
          <el-option label="5秒" :value="5000" />
          <el-option label="10秒" :value="10000" />
          <el-option label="30秒" :value="30000" />
          <el-option label="1分钟" :value="60000" />
        </el-select>
      </div>
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :xs="24" :sm="12" :md="6" v-for="(card, index) in overviewCards" :key="index">
        <el-card shadow="hover" :body-style="{ padding: '20px' }" @click="showDetailDialog(card)">
          <div class="card-content">
            <div class="card-icon" :class="card.status">
              <el-icon><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">{{ card.title }}</div>
              <div class="card-value">{{ card.value }}</div>
              <div class="card-trend" :class="card.trend">
                <el-icon><component :is="card.trend === 'up' ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                {{ card.change }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>响应时间趋势</span>
                <el-tag size="small" :type="getResponseTimeStatus(metricsData[0]?.response_time).type">
                  {{ getResponseTimeStatus(metricsData[0]?.response_time).text }}
                </el-tag>
              </div>
              <div class="chart-actions">
                <el-date-picker
                  v-model="dateRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  :shortcuts="dateShortcuts"
                  @change="handleDateRangeChange"
                  size="small"
                  class="date-picker"
                />
                <el-button-group>
                  <el-button size="small" @click="toggleChartType('responseTime')">
                    <el-icon><component :is="responseTimeChartType === 'line' ? 'PieChart' : 'LineChart'" /></el-icon>
                  </el-button>
                  <el-button size="small" @click="toggleChartFullscreen('responseTime')">
                    <el-icon><FullScreen /></el-icon>
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>
          <div class="chart" ref="responseTimeChart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>资源使用率</span>
                <el-tag size="small" :type="getResourceStatus(metricsData[0]?.resources).type">
                  {{ getResourceStatus(metricsData[0]?.resources).text }}
                </el-tag>
              </div>
              <el-button-group>
                <el-button size="small" @click="toggleChartType('resource')">
                  <el-icon><component :is="resourceChartType === 'pie' ? 'Histogram' : 'PieChart'" /></el-icon>
                </el-button>
                <el-button size="small" @click="toggleChartFullscreen('resource')">
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div class="chart" ref="resourceChart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>错误率趋势</span>
                <el-tag size="small" :type="getErrorRateStatus(metricsData[0]?.error_rate).type">
                  {{ getErrorRateStatus(metricsData[0]?.error_rate).text }}
                </el-tag>
              </div>
            </div>
          </template>
          <div class="chart" ref="errorRateChart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>带宽使用趋势</span>
                <el-tag size="small" :type="getBandwidthStatus(metricsData[0]?.bandwidth).type">
                  {{ getBandwidthStatus(metricsData[0]?.bandwidth).text }}
                </el-tag>
              </div>
            </div>
          </template>
          <div class="chart" ref="bandwidthChart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增统计图表 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>连接数分布</span>
                <el-tag size="small" :type="getConnectionStatus(metricsData[0]?.connection_count).type">
                  {{ getConnectionStatus(metricsData[0]?.connection_count).text }}
                </el-tag>
              </div>
            </div>
          </template>
          <div class="chart" ref="connectionChart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <div class="chart-title">
                <span>SSL证书状态</span>
                <el-tag size="small" :type="getSSLStatus(metricsData[0]?.ssl_status).type">
                  {{ getSSLStatus(metricsData[0]?.ssl_status).text }}
                </el-tag>
              </div>
            </div>
          </template>
          <div class="chart" ref="sslChart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细指标表格 -->
    <el-card class="metrics-table">
      <template #header>
        <div class="table-header">
          <span>详细指标</span>
          <div class="table-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索..."
              size="small"
              clearable
              @clear="handleSearch"
              @input="handleSearch"
              class="search-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button-group>
              <el-button type="primary" @click="exportMetrics">导出CSV</el-button>
              <el-button type="success" @click="exportMetrics('excel')">导出Excel</el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      <el-table 
        :data="filteredMetricsData" 
        style="width: 100%" 
        height="400" 
        border
        @sort-change="handleSortChange"
      >
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间(ms)" width="120">
          <template #default="scope">
            <span :class="getResponseTimeClass(scope.row.response_time)">
              {{ scope.row.response_time }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="connection_count" label="连接数" width="100" />
        <el-table-column prop="error_rate" label="错误率" width="120">
          <template #default="scope">
            <span :class="getErrorRateClass(scope.row.error_rate)">
              {{ (scope.row.error_rate * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="bandwidth" label="带宽使用(MB/s)" width="150">
          <template #default="scope">
            {{ (scope.row.bandwidth / 1000000).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="ssl_status" label="SSL状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.ssl_status.valid ? 'success' : 'danger'">
              {{ scope.row.ssl_status.valid ? '正常' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源使用" min-width="200">
          <el-table-column prop="resources.cpu_percent" label="CPU" width="100">
            <template #default="scope">
              <el-progress 
                :percentage="scope.row.resources.cpu_percent" 
                :status="getResourceProgressStatus(scope.row.resources.cpu_percent)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="resources.memory_percent" label="内存" width="100">
            <template #default="scope">
              <el-progress 
                :percentage="scope.row.resources.memory_percent" 
                :status="getResourceProgressStatus(scope.row.resources.memory_percent)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="resources.disk_percent" label="磁盘" width="100">
            <template #default="scope">
              <el-progress 
                :percentage="scope.row.resources.disk_percent" 
                :status="getResourceProgressStatus(scope.row.resources.disk_percent)"
              />
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredMetricsData.length"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedCard?.title"
      width="80%"
      class="detail-dialog"
    >
      <div class="detail-content">
        <div class="detail-chart" ref="detailChart"></div>
        <div class="detail-stats">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="当前值">{{ selectedCard?.value }}</el-descriptions-item>
            <el-descriptions-item label="变化趋势">
              <span :class="selectedCard?.trend">
                {{ selectedCard?.trend === 'up' ? '上升' : '下降' }} {{ selectedCard?.change }}%
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="selectedCard?.status">
                {{ getStatusText(selectedCard?.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatTime(metricsData[0]?.timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog
      v-model="exportDialogVisible"
      title="导出数据"
      width="500px"
    >
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="exportForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :shortcuts="dateShortcuts"
          />
        </el-form-item>
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="excel">Excel</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数据间隔">
          <el-select v-model="exportForm.interval">
            <el-option label="1分钟" value="60" />
            <el-option label="5分钟" value="300" />
            <el-option label="15分钟" value="900" />
            <el-option label="1小时" value="3600" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="exportDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleExport">导出</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { 
  ArrowUp, 
  ArrowDown, 
  PieChart, 
  LineChart, 
  Histogram,
  Refresh,
  Download,
  FullScreen,
  Search
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'
import moment from 'moment'
import * as XLSX from 'xlsx'
import { ElMessage } from 'element-plus'

export default {
  name: 'Dashboard',
  components: {
    ArrowUp,
    ArrowDown,
    PieChart,
    LineChart,
    Histogram,
    Refresh,
    Download,
    FullScreen,
    Search
  },
  setup() {
    const timeRange = ref('1h')
    const metricsData = ref([])
    const responseTimeChartType = ref('line')
    const resourceChartType = ref('pie')
    let responseTimeChart = null
    let resourceChart = null
    let errorRateChart = null
    let bandwidthChart = null
    let connectionChart = null
    let sslChart = null
    let updateTimer = null
    const dateRange = ref([])
    const dateShortcuts = [
      {
        text: '最近一小时',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 3600 * 1000)
          return [start, end]
        }
      },
      {
        text: '最近24小时',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 3600 * 1000 * 24)
          return [start, end]
        }
      },
      {
        text: '最近7天',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
          return [start, end]
        }
      }
    ]
    const autoRefresh = ref(true)
    const refreshInterval = ref(5000)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const detailDialogVisible = ref(false)
    const exportDialogVisible = ref(false)
    const selectedCard = ref(null)
    const detailChart = ref(null)
    const exportForm = ref({
      dateRange: [],
      format: 'csv',
      interval: '60'
    })

    const initCharts = () => {
      responseTimeChart = echarts.init(document.querySelector('.chart'))
      resourceChart = echarts.init(document.querySelector('.chart:nth-child(2)'))
      
      // 响应时间图表配置
      responseTimeChart.setOption({
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          name: '响应时间(ms)'
        },
        series: [{
          name: '响应时间',
          type: responseTimeChartType.value,
          smooth: true,
          data: []
        }]
      })
      
      // 资源使用图表配置
      resourceChart.setOption({
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [{
          name: '资源使用',
          type: resourceChartType.value,
          radius: '50%',
          data: [],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      })

      // 错误率图表配置
      errorRateChart = echarts.init(document.querySelector('.chart:nth-child(3)'))
      errorRateChart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: '{b}<br/>错误率: {c}%'
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          name: '错误率(%)',
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: [{
          name: '错误率',
          type: 'line',
          smooth: true,
          areaStyle: {
            opacity: 0.3
          },
          data: []
        }]
      })

      // 带宽使用图表配置
      bandwidthChart = echarts.init(document.querySelector('.chart:nth-child(4)'))
      bandwidthChart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: '{b}<br/>带宽: {c} MB/s'
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          name: '带宽(MB/s)'
        },
        series: [{
          name: '带宽使用',
          type: 'line',
          smooth: true,
          areaStyle: {
            opacity: 0.3
          },
          data: []
        }]
      })

      // 连接数分布图表配置
      connectionChart = echarts.init(document.querySelector('.chart:nth-child(5)'))
      connectionChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [{
          name: '连接数分布',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '20',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: 0, name: '活跃连接' },
            { value: 0, name: '等待连接' },
            { value: 0, name: '空闲连接' }
          ]
        }]
      })

      // SSL状态图表配置
      sslChart = echarts.init(document.querySelector('.chart:nth-child(6)'))
      sslChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [{
          name: 'SSL状态',
          type: 'pie',
          radius: '50%',
          data: [
            { value: 0, name: '有效' },
            { value: 0, name: '即将过期' },
            { value: 0, name: '已过期' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      })
    }

    const toggleChartType = (chartName) => {
      if (chartName === 'responseTime') {
        responseTimeChartType.value = responseTimeChartType.value === 'line' ? 'bar' : 'line'
        updateResponseTimeChart()
      } else if (chartName === 'resource') {
        resourceChartType.value = resourceChartType.value === 'pie' ? 'bar' : 'pie'
        updateResourceChart()
      }
    }

    const updateResponseTimeChart = () => {
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          name: '响应时间(ms)'
        },
        series: [{
          name: '响应时间',
          type: responseTimeChartType.value,
          data: metricsData.value.map(item => [item.timestamp, item.response_time])
        }]
      }
      responseTimeChart.setOption(option)
    }

    const updateResourceChart = () => {
      const data = [
        { value: metricsData.value[0]?.resources?.cpu_percent || 0, name: 'CPU' },
        { value: metricsData.value[0]?.resources?.memory_percent || 0, name: '内存' },
        { value: metricsData.value[0]?.resources?.disk_percent || 0, name: '磁盘' }
      ]

      const option = {
        tooltip: {
          trigger: resourceChartType.value === 'pie' ? 'item' : 'axis'
        },
        xAxis: resourceChartType.value === 'bar' ? {
          type: 'category',
          data: data.map(item => item.name)
        } : undefined,
        yAxis: resourceChartType.value === 'bar' ? {
          type: 'value',
          max: 100
        } : undefined,
        series: [{
          name: '资源使用',
          type: resourceChartType.value,
          data: resourceChartType.value === 'pie' ? data : data.map(item => item.value),
          radius: resourceChartType.value === 'pie' ? '50%' : undefined
        }]
      }
      resourceChart.setOption(option)
    }

    const updateData = async () => {
      try {
        const response = await axios.get('/api/metrics')
        const metrics = response.data
        
        // 更新概览卡片
        overviewCards.value[0].value = `${metrics.response_time.toFixed(2)}ms`
        overviewCards.value[1].value = metrics.connection_count
        overviewCards.value[2].value = `${(metrics.error_rate * 100).toFixed(2)}%`
        overviewCards.value[3].value = `${(metrics.bandwidth / 1000000).toFixed(2)}MB/s`
        
        // 更新图表数据
        const time = moment().valueOf()
        responseTimeChart.appendData({
          seriesIndex: 0,
          data: [[time, metrics.response_time]]
        })
        
        // 更新资源使用图表
        resourceChart.setOption({
          series: [{
            data: [
              { value: metrics.resources.cpu_percent, name: 'CPU' },
              { value: metrics.resources.memory_percent, name: '内存' },
              { value: metrics.resources.disk_percent, name: '磁盘' }
            ]
          }]
        })
        
        // 更新表格数据
        metricsData.value.unshift({
          timestamp: time,
          ...metrics
        })
        if (metricsData.value.length > 100) {
          metricsData.value.pop()
        }
        
        // 更新错误率图表
        errorRateChart.appendData({
          seriesIndex: 0,
          data: [[time, metrics.error_rate * 100]]
        })

        // 更新带宽图表
        bandwidthChart.appendData({
          seriesIndex: 0,
          data: [[time, metrics.bandwidth / 1000000]]
        })

        // 更新连接数分布图表
        connectionChart.setOption({
          series: [{
            data: [
              { value: metrics.connection_count * 0.7, name: '活跃连接' },
              { value: metrics.connection_count * 0.2, name: '等待连接' },
              { value: metrics.connection_count * 0.1, name: '空闲连接' }
            ]
          }]
        })

        // 更新SSL状态图表
        const sslStatus = metrics.ssl_status
        sslChart.setOption({
          series: [{
            data: [
              { value: sslStatus.valid ? 1 : 0, name: '有效' },
              { value: sslStatus.warning ? 1 : 0, name: '即将过期' },
              { value: !sslStatus.valid && !sslStatus.warning ? 1 : 0, name: '已过期' }
            ]
          }]
        })

      } catch (error) {
        console.error('Error updating metrics:', error)
      }
    }

    const formatTime = (timestamp) => {
      return moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    }

    const getResponseTimeClass = (value) => {
      if (value > 1000) return 'text-danger'
      if (value > 500) return 'text-warning'
      return 'text-success'
    }

    const getErrorRateClass = (value) => {
      if (value > 0.05) return 'text-danger'
      if (value > 0.01) return 'text-warning'
      return 'text-success'
    }

    const handleDateRangeChange = async (val) => {
      if (!val) return
      
      try {
        const [start, end] = val
        const response = await axios.get('/api/metrics/history', {
          params: {
            start_time: start.getTime(),
            end_time: end.getTime()
          }
        })
        
        const historyData = response.data
        updateChartsWithHistory(historyData)
      } catch (error) {
        console.error('Error fetching history data:', error)
        ElMessage.error('获取历史数据失败')
      }
    }

    const updateChartsWithHistory = (data) => {
      // 更新响应时间图表
      responseTimeChart.setOption({
        series: [{
          data: data.map(item => [item.timestamp, item.response_time])
        }]
      })

      // 更新错误率图表
      errorRateChart.setOption({
        series: [{
          data: data.map(item => [item.timestamp, item.error_rate * 100])
        }]
      })

      // 更新带宽图表
      bandwidthChart.setOption({
        series: [{
          data: data.map(item => [item.timestamp, item.bandwidth / 1000000])
        }]
      })

      // 更新表格数据
      metricsData.value = data
    }

    const exportMetrics = (type = 'csv') => {
      const data = metricsData.value.map(row => ({
        '时间': formatTime(row.timestamp),
        '响应时间(ms)': row.response_time,
        '连接数': row.connection_count,
        '错误率(%)': (row.error_rate * 100).toFixed(2),
        '带宽使用(MB/s)': (row.bandwidth / 1000000).toFixed(2),
        'SSL状态': row.ssl_status.valid ? '正常' : '异常',
        'CPU使用率(%)': row.resources.cpu_percent,
        '内存使用率(%)': row.resources.memory_percent,
        '磁盘使用率(%)': row.resources.disk_percent
      }))

      if (type === 'csv') {
        const headers = Object.keys(data[0])
        const csv = [
          headers.join(','),
          ...data.map(row => headers.map(header => row[header]).join(','))
        ].join('\n')
        
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `metrics_${moment().format('YYYYMMDD_HHmmss')}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
      } else if (type === 'excel') {
        const ws = XLSX.utils.json_to_sheet(data)
        const wb = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(wb, ws, '监控数据')
        XLSX.writeFile(wb, `metrics_${moment().format('YYYYMMDD_HHmmss')}.xlsx`)
      }
    }

    // 概览卡片数据
    const overviewCards = computed(() => [
      {
        title: '响应时间',
        value: `${metricsData.value[0]?.response_time || 0}ms`,
        icon: 'Timer',
        status: getResponseTimeStatus(metricsData.value[0]?.response_time).type,
        trend: metricsData.value[0]?.response_time > metricsData.value[1]?.response_time ? 'up' : 'down',
        change: calculateChange(metricsData.value[0]?.response_time, metricsData.value[1]?.response_time)
      },
      {
        title: '连接数',
        value: metricsData.value[0]?.connection_count || 0,
        icon: 'Connection',
        status: getConnectionStatus(metricsData.value[0]?.connection_count).type,
        trend: metricsData.value[0]?.connection_count > metricsData.value[1]?.connection_count ? 'up' : 'down',
        change: calculateChange(metricsData.value[0]?.connection_count, metricsData.value[1]?.connection_count)
      },
      {
        title: '错误率',
        value: `${((metricsData.value[0]?.error_rate || 0) * 100).toFixed(2)}%`,
        icon: 'Warning',
        status: getErrorRateStatus(metricsData.value[0]?.error_rate).type,
        trend: metricsData.value[0]?.error_rate > metricsData.value[1]?.error_rate ? 'up' : 'down',
        change: calculateChange(metricsData.value[0]?.error_rate, metricsData.value[1]?.error_rate)
      },
      {
        title: '带宽使用',
        value: `${((metricsData.value[0]?.bandwidth || 0) / 1000000).toFixed(2)}MB/s`,
        icon: 'DataLine',
        status: getBandwidthStatus(metricsData.value[0]?.bandwidth).type,
        trend: metricsData.value[0]?.bandwidth > metricsData.value[1]?.bandwidth ? 'up' : 'down',
        change: calculateChange(metricsData.value[0]?.bandwidth, metricsData.value[1]?.bandwidth)
      }
    ])

    // 计算变化百分比
    const calculateChange = (current, previous) => {
      if (!previous) return 0
      return ((current - previous) / previous * 100).toFixed(2)
    }

    // 获取资源进度条状态
    const getResourceProgressStatus = (value) => {
      if (value >= 90) return 'exception'
      if (value >= 70) return 'warning'
      return 'success'
    }

    // 刷新数据
    const refreshData = async () => {
      try {
        await updateData()
        ElMessage.success('数据已刷新')
      } catch (error) {
        console.error('Error refreshing data:', error)
        ElMessage.error('刷新数据失败')
      }
    }

    // 过滤后的表格数据
    const filteredMetricsData = computed(() => {
      let data = metricsData.value
      
      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        data = data.filter(item => 
          Object.values(item).some(value => 
            String(value).toLowerCase().includes(query)
          )
        )
      }
      
      // 分页
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return data.slice(start, end)
    })

    // 处理自动刷新
    const handleAutoRefreshChange = (value) => {
      if (value) {
        updateTimer = setInterval(updateData, refreshInterval.value)
      } else {
        clearInterval(updateTimer)
      }
    }

    // 处理刷新间隔变化
    watch(refreshInterval, (newValue) => {
      if (autoRefresh.value) {
        clearInterval(updateTimer)
        updateTimer = setInterval(updateData, newValue)
      }
    })

    // 显示详情对话框
    const showDetailDialog = (card) => {
      selectedCard.value = card
      detailDialogVisible.value = true
      
      nextTick(() => {
        const chart = echarts.init(detailChart.value)
        // 根据卡片类型设置不同的图表配置
        const option = getDetailChartOption(card)
        chart.setOption(option)
      })
    }

    // 获取详情图表配置
    const getDetailChartOption = (card) => {
      // 根据卡片类型返回不同的图表配置
      switch (card.title) {
        case '响应时间':
          return {
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'time' },
            yAxis: { type: 'value', name: '响应时间(ms)' },
            series: [{
              name: '响应时间',
              type: 'line',
              smooth: true,
              data: metricsData.value.map(item => [item.timestamp, item.response_time])
            }]
          }
        // ... 其他卡片类型的配置
        default:
          return {}
      }
    }

    // 切换图表全屏
    const toggleChartFullscreen = (chartName) => {
      const chart = getChartInstance(chartName)
      if (chart) {
        const container = chart.getDom()
        if (document.fullscreenElement) {
          document.exitFullscreen()
        } else {
          container.requestFullscreen()
        }
      }
    }

    // 获取图表实例
    const getChartInstance = (chartName) => {
      switch (chartName) {
        case 'responseTime': return responseTimeChart
        case 'resource': return resourceChart
        case 'errorRate': return errorRateChart
        case 'bandwidth': return bandwidthChart
        case 'connection': return connectionChart
        case 'ssl': return sslChart
        default: return null
      }
    }

    // 处理搜索
    const handleSearch = () => {
      currentPage.value = 1
    }

    // 处理排序
    const handleSortChange = ({ prop, order }) => {
      if (!prop) return
      
      metricsData.value.sort((a, b) => {
        const aValue = a[prop]
        const bValue = b[prop]
        
        if (order === 'ascending') {
          return aValue > bValue ? 1 : -1
        } else if (order === 'descending') {
          return aValue < bValue ? 1 : -1
        }
        return 0
      })
    }

    // 处理分页
    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
    }

    // 显示导出对话框
    const showExportDialog = () => {
      exportDialogVisible.value = true
    }

    // 处理导出
    const handleExport = async () => {
      try {
        const [start, end] = exportForm.value.dateRange
        await exportMetrics(exportForm.value.format, start, end, exportForm.value.interval)
        exportDialogVisible.value = false
        ElMessage.success('导出成功')
      } catch (error) {
        console.error('Error exporting data:', error)
        ElMessage.error('导出失败')
      }
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        success: '正常',
        warning: '警告',
        danger: '异常',
        info: '未知'
      }
      return statusMap[status] || '未知'
    }

    onMounted(() => {
      initCharts()
      updateData()
      updateTimer = setInterval(updateData, 5000)
    })

    onUnmounted(() => {
      if (updateTimer) {
        clearInterval(updateTimer)
      }
      if (responseTimeChart) {
        responseTimeChart.dispose()
      }
      if (resourceChart) {
        resourceChart.dispose()
      }
      if (errorRateChart) {
        errorRateChart.dispose()
      }
      if (bandwidthChart) {
        bandwidthChart.dispose()
      }
      if (connectionChart) {
        connectionChart.dispose()
      }
      if (sslChart) {
        sslChart.dispose()
      }
    })

    return {
      timeRange,
      metricsData,
      formatTime,
      getResponseTimeClass,
      getErrorRateClass,
      exportMetrics,
      responseTimeChartType,
      resourceChartType,
      toggleChartType,
      dateRange,
      dateShortcuts,
      handleDateRangeChange,
      overviewCards,
      refreshData,
      autoRefresh,
      refreshInterval,
      searchQuery,
      currentPage,
      pageSize,
      detailDialogVisible,
      exportDialogVisible,
      selectedCard,
      detailChart,
      exportForm,
      filteredMetricsData,
      handleAutoRefreshChange,
      showDetailDialog,
      toggleChartFullscreen,
      handleSearch,
      handleSortChange,
      handleSizeChange,
      handleCurrentChange,
      showExportDialog,
      handleExport,
      getStatusText
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 10px;

    .toolbar-left,
    .toolbar-right {
      display: flex;
      gap: 10px;
      align-items: center;
    }
  }

  .overview-cards {
    margin-bottom: 20px;

    .card-content {
      display: flex;
      align-items: center;
      gap: 20px;

      .card-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: #fff;

        &.success { background-color: #67c23a; }
        &.warning { background-color: #e6a23c; }
        &.danger { background-color: #f56c6c; }
        &.info { background-color: #909399; }
      }

      .card-info {
        flex: 1;

        .card-title {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }

        .card-value {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 4px;
        }

        .card-trend {
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 4px;

          &.up { color: #67c23a; }
          &.down { color: #f56c6c; }
        }
      }
    }
  }

  .chart-row {
    margin-bottom: 20px;
  }

  .chart-card {
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .chart-title {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .chart-actions {
        display: flex;
        gap: 10px;
      }
    }

    .chart {
      height: 300px;
    }
  }

  .metrics-table {
    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .table-actions {
        .search-input {
          width: 200px;
          @media screen and (max-width: 768px) {
            width: 150px;
          }
        }
      }
    }

    .table-footer {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .detail-dialog {
    .detail-content {
      display: flex;
      flex-direction: column;
      gap: 20px;

      .detail-chart {
        height: 400px;
      }

      .detail-stats {
        padding: 20px;
        background-color: #f5f7fa;
        border-radius: 4px;
      }
    }
  }
}

// 移动端适配
@media screen and (max-width: 768px) {
  .dashboard {
    padding: 10px;

    .overview-cards {
      .el-col {
        margin-bottom: 10px;
      }
    }

    .chart-row {
      .el-col {
        margin-bottom: 10px;
      }
    }

    .chart-card {
      .chart-header {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;

        .chart-actions {
          width: 100%;
          justify-content: space-between;
        }
      }
    }

    .metrics-table {
      .table-header {
        flex-direction: column;
        gap: 10px;

        .table-actions {
          width: 100%;
          flex-wrap: wrap;
        }
      }
    }
  }
}
</style> 