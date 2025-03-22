<template>
  <div class="alerts">
    <!-- 告警统计 -->
    <el-row :gutter="20" class="alert-stats">
      <el-col :span="6" v-for="stat in alertStats" :key="stat.title">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-title">{{ stat.title }}</div>
            <div class="stat-value" :class="stat.type">{{ stat.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <el-card class="alert-list">
      <template #header>
        <div class="list-header">
          <span>告警历史</span>
          <div class="header-actions">
            <el-button-group>
              <el-button 
                v-for="status in alertStatuses" 
                :key="status.value"
                :type="status.value === currentStatus ? 'primary' : ''"
                @click="currentStatus = status.value">
                {{ status.label }}
              </el-button>
            </el-button-group>
            <el-button type="danger" @click="clearAlerts">清理告警</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredAlerts" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getAlertTypeTag(scope.row.type)">
              {{ getAlertTypeLabel(scope.row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警信息" />
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getSeverityType(scope.row.severity)">
              {{ scope.row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'danger' : 'success'">
              {{ scope.row.status === 'active' ? '活跃' : '已解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status === 'active'"
              type="success" 
              size="small"
              @click="resolveAlert(scope.row)">
              解决
            </el-button>
            <el-button 
              type="primary" 
              size="small"
              @click="viewAlertDetails(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalAlerts"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 告警详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="告警详情"
      width="50%">
      <div v-if="selectedAlert" class="alert-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">{{ selectedAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="告警时间">{{ formatTime(selectedAlert.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="告警类型">{{ getAlertTypeLabel(selectedAlert.type) }}</el-descriptions-item>
          <el-descriptions-item label="告警级别">{{ selectedAlert.severity }}</el-descriptions-item>
          <el-descriptions-item label="告警信息" :span="2">{{ selectedAlert.message }}</el-descriptions-item>
          <el-descriptions-item label="当前值">{{ selectedAlert.value }}</el-descriptions-item>
          <el-descriptions-item label="阈值">{{ getAlertThreshold(selectedAlert.type) }}</el-descriptions-item>
          <el-descriptions-item label="持续时间" :span="2">{{ getAlertDuration(selectedAlert) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import moment from 'moment'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Alerts',
  setup() {
    const alerts = ref([])
    const currentStatus = ref('all')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const dialogVisible = ref(false)
    const selectedAlert = ref(null)
    let updateTimer = null

    const alertStatuses = [
      { label: '全部', value: 'all' },
      { label: '活跃', value: 'active' },
      { label: '已解决', value: 'resolved' }
    ]

    const alertStats = computed(() => {
      const activeAlerts = alerts.value.filter(a => a.status === 'active')
      const criticalAlerts = activeAlerts.filter(a => a.severity === 'critical')
      const warningAlerts = activeAlerts.filter(a => a.severity === 'warning')
      
      return [
        {
          title: '活跃告警',
          value: activeAlerts.length,
          type: 'danger'
        },
        {
          title: '严重告警',
          value: criticalAlerts.length,
          type: 'danger'
        },
        {
          title: '警告',
          value: warningAlerts.length,
          type: 'warning'
        },
        {
          title: '已解决',
          value: alerts.value.filter(a => a.status === 'resolved').length,
          type: 'success'
        }
      ]
    })

    const filteredAlerts = computed(() => {
      let filtered = alerts.value
      
      if (currentStatus.value !== 'all') {
        filtered = filtered.filter(a => a.status === currentStatus.value)
      }
      
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      
      return filtered.slice(start, end)
    })

    const totalAlerts = computed(() => {
      if (currentStatus.value === 'all') {
        return alerts.value.length
      }
      return alerts.value.filter(a => a.status === currentStatus.value).length
    })

    const getAlertTypeTag = (type) => {
      const types = {
        response_time: 'warning',
        error_rate: 'danger',
        connection_count: 'info',
        bandwidth: 'warning'
      }
      return types[type] || 'info'
    }

    const getAlertTypeLabel = (type) => {
      const labels = {
        response_time: '响应时间',
        error_rate: '错误率',
        connection_count: '连接数',
        bandwidth: '带宽'
      }
      return labels[type] || type
    }

    const getSeverityType = (severity) => {
      const types = {
        critical: 'danger',
        warning: 'warning',
        info: 'info'
      }
      return types[severity] || 'info'
    }

    const getAlertThreshold = (type) => {
      const thresholds = {
        response_time: '1000ms',
        error_rate: '5%',
        connection_count: '1000',
        bandwidth: '100Mbps'
      }
      return thresholds[type] || 'N/A'
    }

    const getAlertDuration = (alert) => {
      if (!alert.start_time) return 'N/A'
      const duration = moment.duration(moment().diff(alert.start_time))
      return `${duration.hours()}小时${duration.minutes()}分钟`
    }

    const formatTime = (timestamp) => {
      return moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    }

    const updateAlerts = async () => {
      try {
        const response = await axios.get('/api/alerts')
        alerts.value = response.data
      } catch (error) {
        console.error('Error updating alerts:', error)
        ElMessage.error('获取告警数据失败')
      }
    }

    const resolveAlert = async (alert) => {
      try {
        await axios.post(`/api/alerts/${alert.id}/resolve`)
        ElMessage.success('告警已解决')
        updateAlerts()
      } catch (error) {
        console.error('Error resolving alert:', error)
        ElMessage.error('解决告警失败')
      }
    }

    const clearAlerts = async () => {
      try {
        await ElMessageBox.confirm('确定要清理所有已解决的告警吗？', '提示', {
          type: 'warning'
        })
        await axios.post('/api/alerts/clear')
        ElMessage.success('告警已清理')
        updateAlerts()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Error clearing alerts:', error)
          ElMessage.error('清理告警失败')
        }
      }
    }

    const viewAlertDetails = (alert) => {
      selectedAlert.value = alert
      dialogVisible.value = true
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
    }

    onMounted(() => {
      updateAlerts()
      updateTimer = setInterval(updateAlerts, 30000)
    })

    onUnmounted(() => {
      if (updateTimer) {
        clearInterval(updateTimer)
      }
    })

    return {
      alerts,
      currentStatus,
      currentPage,
      pageSize,
      dialogVisible,
      selectedAlert,
      alertStatuses,
      alertStats,
      filteredAlerts,
      totalAlerts,
      getAlertTypeTag,
      getAlertTypeLabel,
      getSeverityType,
      getAlertThreshold,
      getAlertDuration,
      formatTime,
      resolveAlert,
      clearAlerts,
      viewAlertDetails,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style lang="scss" scoped>
.alerts {
  .alert-stats {
    margin-bottom: 20px;
    
    .stat-card {
      .stat-content {
        text-align: center;
        
        .stat-title {
          font-size: 14px;
          color: #909399;
          margin-bottom: 10px;
        }
        
        .stat-value {
          font-size: 24px;
          font-weight: bold;
          
          &.danger {
            color: #f56c6c;
          }
          
          &.warning {
            color: #e6a23c;
          }
          
          &.success {
            color: #67c23a;
          }
        }
      }
    }
  }
  
  .alert-list {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        gap: 10px;
      }
    }
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .alert-details {
    .el-descriptions {
      margin-bottom: 20px;
    }
  }
}
</style> 