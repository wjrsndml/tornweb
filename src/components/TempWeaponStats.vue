<template>
  <el-card class="temp-weapon-stats-card">
    <template #header>
      <div class="card-header">
        <h2>临时武器使用统计工具</h2>
      </div>
    </template>
    <p>输入Ranked War ID和用户ID来统计特定用户在该RW中使用的临时武器。</p>
    
    <el-form :model="form" label-width="120px">
      <el-form-item label="RW War ID">
        <el-input 
          v-model="form.rwId" 
          placeholder="请输入Ranked War ID，例如: 12345" 
        />
      </el-form-item>
      <el-form-item label="用户 ID">
        <el-input 
          v-model="form.userId" 
          placeholder="请输入用户ID，例如: 123456" 
        />
      </el-form-item>
      <el-form-item>
        <el-button 
          type="primary" 
          @click="analyzeWeapons" 
          :loading="loading"
          :disabled="!apiKey || !form.rwId || !form.userId"
        >
          开始分析
        </el-button>
        <el-button 
          v-if="loading"
          @click="stopAnalysis"
        >
          停止分析
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 进度显示 -->
    <div v-if="loading || statusMessage" class="progress-section">
      <el-card class="progress-card">
        <template #header>
          <h4>分析进度</h4>
        </template>
        
        <!-- 总体进度 -->
        <div class="progress-item">
          <div class="progress-label">{{ progressLabel }}</div>
          <el-progress 
            :percentage="overallProgress" 
            :status="loading ? '' : 'success'"
            :stroke-width="20"
          />
          <div class="progress-text">{{ progressText }}</div>
        </div>

        <!-- 状态消息 -->
        <el-alert 
          v-if="statusMessage"
          :title="statusMessage"
          :type="statusType"
          show-icon
          :closable="false"
          style="margin-top: 15px"
        />
      </el-card>
    </div>

    <!-- 分析结果 -->
    <div v-if="analysisResult" class="analysis-result">
      <el-card class="result-card" style="margin-top: 20px;">
        <template #header>
          <h3>临时武器使用统计</h3>
        </template>
        
        <!-- 基本信息 -->
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="用户名">{{ analysisResult.userName }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ form.userId }}</el-descriptions-item>
          <el-descriptions-item label="RW ID">{{ form.rwId }}</el-descriptions-item>
          <el-descriptions-item label="分析的攻击记录">{{ analysisResult.totalAttacks }}</el-descriptions-item>
          <el-descriptions-item label="获取的Log数量">{{ analysisResult.processedLogs }}</el-descriptions-item>
          <el-descriptions-item label="临时武器使用次数">{{ analysisResult.totalTempWeapons }}</el-descriptions-item>
        </el-descriptions>

        <!-- 临时武器统计表格 -->
        <h4 style="margin: 20px 0 10px 0;">临时武器使用详情</h4>
        <el-table 
          :data="analysisResult.weaponStats" 
          border 
          style="width: 100%; margin-bottom: 20px;"
          empty-text="未找到临时武器使用记录"
        >
          <el-table-column prop="itemName" label="临时武器名称" width="200" />
          <el-table-column prop="itemId" label="物品ID" width="100" />
          <el-table-column prop="usage" label="使用次数" width="120" />
          <el-table-column prop="percentage" label="使用占比" width="120">
            <template #default="{ row }">
              {{ row.percentage }}%
            </template>
          </el-table-column>
        </el-table>

        <!-- Log链接（折叠形式） -->
        <el-collapse v-if="analysisResult.logLinks.length > 0">
          <el-collapse-item :title="`查看所有Log链接 (${analysisResult.logLinks.length}条)`" name="logs">
            <div class="log-links-container">
              <div 
                v-for="(link, index) in analysisResult.logLinks" 
                :key="index"
                class="log-link-item"
              >
                <div class="log-link-main">
                  <el-link 
                    :href="link.url" 
                    target="_blank" 
                    type="primary"
                    style="margin-right: 10px;"
                  >
                    <el-icon style="margin-right: 5px;"><Link /></el-icon>
                    Log {{ index + 1 }} ({{ link.timestamp }})
                  </el-link>
                  <span class="log-details">{{ link.details }}</span>
                </div>
                
                <!-- 显示这次攻击使用的临时武器 -->
                <div v-if="link.tempWeapons && link.tempWeapons.length > 0" class="temp-weapons-used">
                  <el-icon class="weapon-icon" style="margin-right: 5px;"><Operation /></el-icon>
                  <span class="weapons-label">使用临时武器:</span>
                  <el-tag 
                    v-for="(weapon, wIndex) in link.tempWeapons" 
                    :key="wIndex"
                    size="small" 
                    type="success"
                    style="margin-left: 5px;"
                  >
                    {{ weapon.name }}
                    <span v-if="weapon.id > 0" class="weapon-id">(ID: {{ weapon.id }})</span>
                  </el-tag>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>

    <!-- 错误信息 -->
    <el-alert 
      v-if="error" 
      :title="error" 
      type="error" 
      show-icon
      style="margin-top: 20px"
    />
  </el-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import axios from 'axios'
import { Link, Operation } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
  apiKey: {
    type: String,
    required: true
  }
})

// API基础URL
const API_BASE_URL = 'https://api.torn.com/v2'

// 表单数据
const form = reactive({
  rwId: '',
  userId: ''
})

// 状态变量
const loading = ref(false)
const error = ref(null)
const statusMessage = ref('')
const statusType = ref('info')
const overallProgress = ref(0)
const progressLabel = ref('准备开始...')
const progressText = ref('')
const analysisResult = ref(null)

// 中止控制器
let abortController = null

// 限流相关
const RATE_LIMIT = 50 // 每分钟最多50个请求，留一些余量
let requestCount = 0
let lastResetTime = Date.now()

// API请求函数
const fetchApi = async (endpoint, apiKey) => {
  let url = `${API_BASE_URL}${endpoint}`
  if (url.includes('?')) {
    url += `&key=${apiKey}`
  } else {
    url += `?key=${apiKey}`
  }
  
  try {
    const response = await axios.get(url, {
      signal: abortController?.signal,
      timeout: 30000
    })
    
    if (response.data.error) {
      throw new Error(`Torn API 错误: ${response.data.error.error} (代码: ${response.data.error.code})`)
    }
    
    return response.data
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('请求被取消')
    }
    
    if (error.response) {
      const errorData = error.response.data
      let errorMessage = `API请求失败，状态码: ${error.response.status}.`
      if (errorData && errorData.error && errorData.error.error) {
        errorMessage += ` 错误: ${errorData.error.error}`
      }
      throw new Error(errorMessage)
    }
    throw error
  }
}

// 智能限流请求函数
const rateLimitedRequest = async (requestFn) => {
  // 检查是否需要重置计数器（每分钟重置一次）
  const now = Date.now()
  if (now - lastResetTime >= 60000) {
    requestCount = 0
    lastResetTime = now
  }
  
  // 如果达到限制，等待到下一分钟
  if (requestCount >= RATE_LIMIT) {
    const waitTime = 60000 - (now - lastResetTime) + 1000 // 多等1秒确保安全
    console.log(`达到API频率限制，等待 ${Math.ceil(waitTime / 1000)} 秒...`)
    
    // 更新状态消息告知用户正在等待
    statusMessage.value = `已达到API频率限制，等待 ${Math.ceil(waitTime / 1000)} 秒后继续...`
    
    await new Promise(resolve => setTimeout(resolve, waitTime))
    
    // 重置计数器
    requestCount = 0
    lastResetTime = Date.now()
  }
  
  requestCount++
  return await requestFn()
}

// 获取攻击日志
const fetchAttackLog = async (logCode) => {
  return await rateLimitedRequest(async () => {
    const response = await axios.get(
      `https://api.torn.com/v2/torn/attacklog?log=${logCode}&offset=0&striptags=true&key=${props.apiKey}`,
      {
        signal: abortController?.signal,
        timeout: 30000
      }
    )
    
    if (response.data.error) {
      throw new Error(`获取攻击日志失败: ${response.data.error.error}`)
    }
    
    return response.data
  })
}

// 开始分析
const analyzeWeapons = async () => {
  if (!props.apiKey) {
    error.value = '请先输入API Key'
    return
  }
  
  if (!form.rwId || !form.userId) {
    error.value = '请输入RW ID和用户ID'
    return
  }
  
  loading.value = true
  error.value = null
  statusMessage.value = ''
  analysisResult.value = null
  overallProgress.value = 0
  
  // 重置频率限制计数器
  requestCount = 0
  lastResetTime = Date.now()
  
  // 创建中止控制器
  abortController = new AbortController()
  
  try {
    // 步骤1: 获取RW战争报告
    progressLabel.value = '获取RW战争报告'
    progressText.value = '正在获取战争报告数据...'
    statusMessage.value = '正在获取RW战争报告...'
    overallProgress.value = 10
    
    const warReportData = await fetchApi(`/faction/${form.rwId}/rankedwarreport`, props.apiKey)
    
    if (!warReportData.rankedwarreport || !warReportData.rankedwarreport.factions) {
      throw new Error('无法获取RW战争报告，请检查RW ID是否正确')
    }
    
    const warReport = warReportData.rankedwarreport
    const warStartTime = warReport.start
    const warEndTime = warReport.end || Math.floor(Date.now() / 1000) // 如果战争还在进行，使用当前时间
    
    // 步骤2: 获取攻击记录
    progressLabel.value = '获取攻击记录'
    progressText.value = '正在获取战争期间的攻击记录...'
    statusMessage.value = '正在获取攻击记录...'
    overallProgress.value = 15
    
    // 分页获取所有攻击记录
    const allAttacks = []
    let currentTimestamp = warStartTime
    let hasMore = true
    let requestCounter = 0
    
    while (hasMore && currentTimestamp < warEndTime) {
      try {
        // 为避免API限流，每次请求间隔1秒
        if (requestCounter > 0) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
        requestCounter++
        
        progressText.value = `正在获取从 ${new Date(currentTimestamp * 1000).toLocaleString('zh-CN')} 开始的攻击记录...`
        
        const attacksResponse = await axios.get(
          `https://api.torn.com/v2/faction/attacksfull?from=${currentTimestamp}&sort=ASC&key=${props.apiKey}`,
          {
            signal: abortController?.signal,
            timeout: 30000
          }
        )
        
        if (attacksResponse.data.error) {
          throw new Error(`获取攻击记录失败: ${attacksResponse.data.error.error}`)
        }
        
        const attacks = Object.values(attacksResponse.data.attacks || {})
        
        if (attacks.length === 0) {
          hasMore = false
          break
        }
        
        // 筛选出RW期间的攻击
        const rwAttacks = attacks.filter(attack => 
          attack.started >= warStartTime && attack.started <= warEndTime
        )
        
        allAttacks.push(...rwAttacks)
        
        // 获取最后一条记录的时间戳作为下一次查询的起始时间
        const lastAttackTimestamp = Math.max(...attacks.map(attack => parseInt(attack.started)))
        
        // 如果已经超过战争结束时间，或者没有更多数据，停止获取
        if (lastAttackTimestamp <= currentTimestamp || lastAttackTimestamp > warEndTime) {
          hasMore = false
        } else {
          currentTimestamp = lastAttackTimestamp + 1 // 加1秒避免重复
        }
        
        // 更新进度
        progressText.value = `已获取 ${allAttacks.length} 条RW攻击记录...`
        
        // 如果获取的攻击记录已经很多，可以考虑限制
        if (allAttacks.length > 10000) { // 限制最多1万条记录
          hasMore = false
          statusMessage.value = '已达到记录数量限制，停止获取更多数据'
        }
        
      } catch (e) {
        console.error('获取攻击记录失败:', e)
        if (e.name === 'AbortError') {
          throw new Error('请求被取消')
        }
        // 如果是单次请求失败，记录错误但继续
        console.warn(`获取时间戳 ${currentTimestamp} 的攻击记录失败:`, e.message)
        hasMore = false
      }
    }
         
    // 步骤3: 筛选用户攻击记录
    progressLabel.value = '筛选用户攻击记录'
    progressText.value = `从${allAttacks.length}条记录中筛选用户攻击...`
    statusMessage.value = `正在筛选用户ID ${form.userId} 的攻击记录...`
    overallProgress.value = 25
    
    const userAttacks = allAttacks.filter(attack => 
      attack.attacker && String(attack.attacker.id) === String(form.userId)
    )
    
    if (userAttacks.length === 0) {
      throw new Error(`未找到用户ID ${form.userId} 的攻击记录`)
    }
    
    statusMessage.value = `找到${userAttacks.length}条用户攻击记录`
    
    // 步骤4: 获取用户名
    let userName = '未知用户'
    try {
      const userData = await fetchApi(`/user/${form.userId}`, props.apiKey)
      userName = userData.name || '未知用户'
    } catch (e) {
      console.warn('无法获取用户名:', e.message)
    }
    
    // 步骤5: 获取攻击日志并分析临时武器
    progressLabel.value = '分析攻击日志'
    statusMessage.value = '正在获取攻击日志，限制每分钟50条...'
    overallProgress.value = 35
    
    const weaponUsage = new Map()
    const logLinks = []
    let processedCount = 0
    const maxLogsPerBatch = Math.min(RATE_LIMIT, userAttacks.length)
    
    for (let i = 0; i < userAttacks.length; i++) {
      if (abortController.signal.aborted) {
        throw new Error('分析被取消')
      }
      
      const attack = userAttacks[i]
      const logCode = attack.code
      
      if (!logCode) continue
      
      try {
        // 更新进度
        const progressPercent = 35 + (i / userAttacks.length) * 50
        overallProgress.value = Math.round(progressPercent)
        progressText.value = `处理第${i + 1}/${userAttacks.length}条攻击记录`
        
        // 显示当前请求状态
        const remainingRequests = RATE_LIMIT - requestCount
        statusMessage.value = `正在分析Log ${i + 1}/${userAttacks.length} (剩余请求: ${remainingRequests}/${RATE_LIMIT})`
        
        // 获取攻击日志
        const logData = await fetchAttackLog(logCode)
        processedCount++
        
        if (logData.attacklog && logData.attacklog.log) {
          const logEntries = logData.attacklog.log
          let hasSpecialTemp = false
          const tempWeaponsUsedInThisLog = []
          
          // 查找specialTemp动作
          for (const entry of logEntries) {
            if (entry.action === 'specialTemp' && 
                entry.attacker && 
                String(entry.attacker.id) === String(form.userId)) {
              
              hasSpecialTemp = true
              const itemName = entry.attacker.item?.name || '未知临时武器'
              const itemId = entry.attacker.item?.id || 0
              
              // 记录这次攻击中使用的临时武器
              tempWeaponsUsedInThisLog.push({
                name: itemName,
                id: itemId
              })
              
              // 统计总使用次数
              if (weaponUsage.has(itemName)) {
                weaponUsage.set(itemName, {
                  ...weaponUsage.get(itemName),
                  usage: weaponUsage.get(itemName).usage + 1
                })
              } else {
                weaponUsage.set(itemName, {
                  itemName,
                  itemId,
                  usage: 1
                })
              }
            }
          }
          
          // 如果找到临时武器使用，添加到链接列表
          if (hasSpecialTemp) {
            // 去重临时武器列表（同一次攻击可能使用多个相同武器）
            const uniqueWeapons = tempWeaponsUsedInThisLog.reduce((acc, weapon) => {
              if (!acc.find(w => w.name === weapon.name)) {
                acc.push(weapon)
              }
              return acc
            }, [])
            
            logLinks.push({
              url: `https://www.torn.com/loader.php?sid=attackLog&ID=${logCode}`,
              timestamp: new Date(attack.started * 1000).toLocaleString('zh-CN'),
              details: `${attack.result || '攻击'} - ${attack.respect_gain || 0} Respect`,
              tempWeapons: uniqueWeapons // 新增：记录这次攻击使用的临时武器
            })
          }
        }
        
        // 添加适当的延迟，避免过于频繁的请求
        if (i < userAttacks.length - 1) {
          // 如果还有很多请求余量，可以稍快一些
          const delay = remainingRequests > 10 ? 800 : 1500
          await new Promise(resolve => setTimeout(resolve, delay))
        }
        
      } catch (logError) {
        console.warn(`获取Log ${logCode} 失败:`, logError.message)
        
        // 如果是频率限制错误，在状态中显示
        if (logError.message.includes('频率限制')) {
          statusMessage.value = `API频率限制中，正在等待...`
        } else {
          // 对于其他错误，记录并继续
          console.warn(`跳过Log ${logCode}，原因: ${logError.message}`)
        }
        
        // 继续处理下一个，不要因为单个log失败而停止
        // 即使失败也要添加延迟，避免连续失败导致的快速循环
        if (i < userAttacks.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
    }
    
    // 步骤6: 整理结果
    overallProgress.value = 90
    progressLabel.value = '整理分析结果'
    statusMessage.value = '正在整理分析结果...'
    
    const weaponStats = Array.from(weaponUsage.values())
    const totalTempWeapons = weaponStats.reduce((sum, weapon) => sum + weapon.usage, 0)
    
    // 计算百分比
    weaponStats.forEach(weapon => {
      weapon.percentage = totalTempWeapons > 0 ? 
        ((weapon.usage / totalTempWeapons) * 100).toFixed(1) : 0
    })
    
    // 按使用次数排序
    weaponStats.sort((a, b) => b.usage - a.usage)
    
    analysisResult.value = {
      userName,
      totalAttacks: userAttacks.length,
      processedLogs: processedCount,
      totalTempWeapons,
      weaponStats,
      logLinks
    }
    
    overallProgress.value = 100
    statusMessage.value = '分析完成！'
    statusType.value = 'success'
    
  } catch (e) {
    console.error('分析失败:', e)
    error.value = e.message
    statusMessage.value = `分析失败: ${e.message}`
    statusType.value = 'error'
  } finally {
    loading.value = false
  }
}

// 停止分析
const stopAnalysis = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  
  loading.value = false
  statusMessage.value = '分析已取消'
  statusType.value = 'warning'
}
</script>

<style scoped>
.temp-weapon-stats-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-section {
  margin: 20px 0;
}

.progress-card {
  border: 1px solid #e4e7ed;
}

.progress-item {
  margin-bottom: 15px;
}

.progress-label {
  font-weight: 500;
  margin-bottom: 5px;
  color: #606266;
}

.progress-text {
  margin-top: 5px;
  font-size: 14px;
  color: #909399;
}

.analysis-result {
  margin-top: 20px;
}

.result-card {
  border: 1px solid #e4e7ed;
}

.log-links-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
}

.log-link-item {
  margin-bottom: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.log-link-main {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.log-details {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

.temp-weapons-used {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 6px 0;
  border-top: 1px solid #e4e7ed;
}

.weapon-icon {
  color: #67c23a;
}

.weapons-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.weapon-id {
  color: #909399;
  font-size: 11px;
}
</style> 