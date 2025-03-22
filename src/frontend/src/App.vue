<template>
  <el-container class="app-container">
    <el-aside width="200px">
      <el-menu
        :router="true"
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#fff"
        active-text-color="#409EFF">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>监控面板</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Warning /></el-icon>
          <span>告警管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-left">
          <h2>IP监控系统</h2>
          <el-tag :type="systemStatus.type">{{ systemStatus.text }}</el-tag>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="el-dropdown-link">
              管理员<el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人信息</el-dropdown-item>
                <el-dropdown-item>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Monitor, Warning, Setting, ArrowDown } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    Monitor,
    Warning,
    Setting,
    ArrowDown
  },
  setup() {
    const systemStatus = ref({
      type: 'success',
      text: '系统正常'
    })

    const checkSystemStatus = async () => {
      try {
        const response = await axios.get('/api/status')
        const status = response.data
        systemStatus.value = {
          type: status.monitor.is_running ? 'success' : 'danger',
          text: status.monitor.is_running ? '系统正常' : '系统异常'
        }
      } catch (error) {
        systemStatus.value = {
          type: 'danger',
          text: '系统异常'
        }
      }
    }

    onMounted(() => {
      checkSystemStatus()
      setInterval(checkSystemStatus, 30000)
    })

    return {
      systemStatus
    }
  }
}
</script>

<style lang="scss">
.app-container {
  height: 100vh;
  
  .el-aside {
    background-color: #304156;
    
    .el-menu {
      border-right: none;
    }
  }
  
  .el-header {
    background-color: #fff;
    border-bottom: 1px solid #dcdfe6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 20px;
      
      h2 {
        margin: 0;
      }
    }
    
    .header-right {
      .el-dropdown-link {
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 5px;
      }
    }
  }
  
  .el-main {
    background-color: #f0f2f5;
    padding: 20px;
  }
}
</style> 