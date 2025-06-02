<template>
  <el-card class="chain-analyzer-card">
    <template #header>
      <div class="card-header">
        <h2>Torn Ranked War Chain 查看器</h2>
      </div>
    </template>
    <p>输入Ranked War ID以获取对应rw参战帮派的chain报告。</p>
    
    <el-form :model="form" label-width="120px">
      <el-form-item label="RW War ID">
        <el-input 
          v-model="form.rankedWarId" 
          placeholder="请输入Ranked War ID，例如: 12345" 
        />
      </el-form-item>
      <el-form-item>
        <el-button 
          type="primary" 
          @click="fetchChainData" 
          :loading="loading"
          :disabled="!apiKey"
        >
          获取数据
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 状态显示 -->
    <div v-if="loading || statusMessage" class="status-section">
      <el-progress 
        v-if="loading" 
        :percentage="100" 
        status="active" 
        :indeterminate="true" 
        :duration="3" 
        :stroke-width="15"
        style="margin: 20px 0"
      />
      <el-alert 
        v-if="statusMessage"
        :title="statusMessage"
        :type="statusType"
        show-icon
        :closable="false"
        style="margin-top: 10px"
      />
    </div>

    <!-- 战争详情 -->
    <el-card v-if="warDetails" class="war-details-card" style="margin-top: 20px;">
      <template #header>
        <h3>战争详情</h3>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="战争开始时间">
          {{ formatTimestamp(warDetails.start) }}
        </el-descriptions-item>
        <el-descriptions-item label="战争结束时间">
          {{ formatTimestamp(warDetails.end) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 帮派Chain数据 -->
    <div v-if="factionChains.length > 0" class="faction-chains">
      <el-card 
        v-for="factionData in factionChains" 
        :key="factionData.factionId"
        class="faction-card"
        style="margin-top: 20px;"
      >
        <template #header>
          <h3>{{ factionData.factionName }} (ID: {{ factionData.factionId }}) Chains</h3>
        </template>
        
        <el-alert 
          v-if="factionData.message"
          :title="factionData.message"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <div v-if="factionData.chains.length > 0" class="chains-container">
          <el-collapse accordion>
            <el-collapse-item 
              v-for="chain in factionData.chains" 
              :key="chain.id"
              :title="`Chain ID: ${chain.id} - ${chain.details.chain} Hits - ${chain.details.respect.toFixed(2)} Respect`"
            >
              <div class="chain-details">
                <!-- 基本信息 -->
                <el-descriptions :column="2" border size="small" style="margin-bottom: 15px;">
                  <el-descriptions-item label="开始时间">
                    {{ formatTimestamp(chain.start) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="结束时间">
                    {{ formatTimestamp(chain.end) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="持续时间">
                    {{ formatDuration(chain.end - chain.start) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="参与成员">
                    {{ chain.details.members }}
                  </el-descriptions-item>
                </el-descriptions>

                <!-- 详细统计 -->
                <el-row :gutter="20" style="margin-top: 15px;">
                  <el-col :span="12">
                    <el-card class="stats-card">
                      <template #header>
                        <h4>攻击统计</h4>
                      </template>
                      <div class="stats-grid">
                        <div class="stat-item">
                          <span class="label">总 Hits:</span>
                          <span class="value">{{ chain.details.chain }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">总 Respect:</span>
                          <span class="value">{{ chain.details.respect.toFixed(2) }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">最佳 Respect:</span>
                          <span class="value">{{ chain.details.best.toFixed(2) }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">目标数量:</span>
                          <span class="value">{{ chain.details.targets }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">战争 Hits:</span>
                          <span class="value">{{ chain.details.war }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Assists:</span>
                          <span class="value">{{ chain.details.assists }}</span>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card class="stats-card">
                      <template #header>
                        <h4>其他统计</h4>
                      </template>
                      <div class="stats-grid">
                        <div class="stat-item">
                          <span class="label">Leave:</span>
                          <span class="value">{{ chain.details.leave }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Mug:</span>
                          <span class="value">{{ chain.details.mug }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Hospitalize:</span>
                          <span class="value">{{ chain.details.hospitalize }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Retaliations:</span>
                          <span class="value">{{ chain.details.retaliations }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Overseas:</span>
                          <span class="value">{{ chain.details.overseas }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Draws:</span>
                          <span class="value">{{ chain.details.draws }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Escapes:</span>
                          <span class="value">{{ chain.details.escapes }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="label">Losses:</span>
                          <span class="value">{{ chain.details.losses }}</span>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>

                <!-- 奖励加成表格 -->
                <el-card v-if="chain.bonuses && chain.bonuses.length > 0" class="section-card" style="margin-top: 15px;">
                  <template #header>
                    <h4>奖励加成 ({{ chain.bonuses.length }})</h4>
                  </template>
                  <el-table :data="chain.bonuses" stripe size="small" max-height="300">
                    <el-table-column prop="attacker_id" label="攻击者ID" width="100" />
                    <el-table-column prop="defender_id" label="防守者ID" width="100" />
                    <el-table-column prop="chain" label="Chain Hits" width="120" />
                    <el-table-column prop="respect" label="Respect" width="100" />
                  </el-table>
                </el-card>

                <!-- 攻击者表格 -->
                <el-card v-if="chain.attackers && chain.attackers.length > 0" class="section-card" style="margin-top: 15px;">
                  <template #header>
                    <h4>攻击者 ({{ chain.attackers.length }})</h4>
                  </template>
                  <el-table :data="chain.attackers" stripe size="small" max-height="300">
                    <el-table-column prop="id" label="攻击者ID" width="100" />
                    <el-table-column label="总攻击" width="100">
                      <template #default="{ row }">
                        {{ row.attacks.total }}
                      </template>
                    </el-table-column>
                    <el-table-column label="总Respect" width="120">
                      <template #default="{ row }">
                        {{ row.respect.total.toFixed(2) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="平均Respect" width="120">
                      <template #default="{ row }">
                        {{ row.respect.average.toFixed(2) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="最佳Respect" width="120">
                      <template #default="{ row }">
                        {{ row.respect.best.toFixed(2) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>

                <!-- 未攻击成员 -->
                <el-card v-if="chain.non_attackers && chain.non_attackers.length > 0" class="section-card" style="margin-top: 15px;">
                  <template #header>
                    <h4>未攻击成员 ({{ chain.non_attackers.length }})</h4>
                  </template>
                  <div class="non-attackers">
                    <el-tag v-for="memberId in chain.non_attackers" :key="memberId" style="margin: 2px;">
                      {{ memberId }}
                    </el-tag>
                  </div>
                </el-card>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-card>
    </div>

    <!-- 注意事项 -->
    <el-alert 
      title="注意事项"
      type="warning"
      :closable="false"
      style="margin-top: 20px"
    >
      <template #default>
        <p>此工具用于查看rw参战帮派的chain报告。目前主要用途是识别假赛，当你看到chain报告中很少有hos和复仇时，基本上可以判断为假赛。</p>
      </template>
    </el-alert>
  </el-card>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const props = defineProps({
  apiKey: {
    type: String,
    default: ''
  }
})

const API_BASE_URL = 'https://api.torn.com/v2'

const form = reactive({
  rankedWarId: ''
})

const loading = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const warDetails = ref(null)
const factionChains = ref([])

const fetchApi = async (endpoint, apiKey) => {
  let url = `${API_BASE_URL}${endpoint}`
  if (url.includes('?')) {
    url += `&key=${apiKey}`
  } else {
    url += `?key=${apiKey}`
  }
  
  try {
    const response = await axios.get(url)
    if (response.data.error) {
      throw new Error(`Torn API 错误: ${response.data.error.error} (代码: ${response.data.error.code})`)
    }
    return response.data
  } catch (error) {
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

const fetchChainData = async () => {
  if (!form.rankedWarId) {
    statusMessage.value = '请输入Ranked War ID'
    statusType.value = 'error'
    return
  }
  
  if (!props.apiKey) {
    statusMessage.value = '请先在侧边栏输入API密钥'
    statusType.value = 'error'
    return
  }
  
  loading.value = true
  statusMessage.value = '正在获取战争报告...'
  statusType.value = 'info'
  warDetails.value = null
  factionChains.value = []
  
  try {
    // 获取战争报告
    const warReportEndpoint = `/faction/${form.rankedWarId}/rankedwarreport`
    const warData = await fetchApi(warReportEndpoint, props.apiKey)
    
    if (!warData.rankedwarreport || !warData.rankedwarreport.factions || warData.rankedwarreport.factions.length < 2) {
      throw new Error('无法获取有效的战争报告或帮派信息。请检查Ranked War ID是否正确，以及API密钥是否有权限访问此报告。')
    }
    
    const warReport = warData.rankedwarreport
    warDetails.value = {
      start: warReport.start,
      end: warReport.end
    }
    
    const factionsInvolved = warReport.factions
    
    // 处理每个帮派的chain数据
    for (const factionInfo of factionsInvolved) {
      await processFactionChains(factionInfo, warReport.start, warReport.end)
    }
    
    statusMessage.value = '所有数据获取完成'
    statusType.value = 'success'
    
  } catch (error) {
    console.error('Error in fetchChainData:', error)
    statusMessage.value = `获取数据失败: ${error.message}`
    statusType.value = 'error'
  } finally {
    loading.value = false
  }
}

const processFactionChains = async (factionInfo, warStartTime, warEndTime) => {
  statusMessage.value = `正在获取 ${factionInfo.name} 的基础chain列表...`
  
  const factionData = {
    factionId: factionInfo.id,
    factionName: factionInfo.name,
    message: '',
    chains: []
  }
  
  try {
    const chainsSummaryEndpoint = `/faction/${factionInfo.id}/chains?from=${warStartTime}&to=${warEndTime}&limit=100`
    const chainsSummaryData = await fetchApi(chainsSummaryEndpoint, props.apiKey)
    const chainSummaries = chainsSummaryData.chains || []
    
    if (chainSummaries.length === 0) {
      factionData.message = '在此战争期间未找到chain'
      factionChains.value.push(factionData)
      return
    }
    
    factionData.message = `找到 ${chainSummaries.length} 条基础chain记录${chainSummaries.length === 100 ? ' (已显示最近的100条)' : ''}`
    
    // 获取每个chain的详细报告
    for (let i = 0; i < chainSummaries.length; i++) {
      const summary = chainSummaries[i]
      statusMessage.value = `正在获取 ${factionInfo.name} 的 Chain ID: ${summary.id} 详细报告 (${i + 1}/${chainSummaries.length})...`
      
      try {
        const chainReportEndpoint = `/faction/${summary.id}/chainreport`
        const reportData = await fetchApi(chainReportEndpoint, props.apiKey)
        
        if (reportData.chainreport) {
          factionData.chains.push(reportData.chainreport)
        }
      } catch (reportError) {
        console.error(`获取 Chain ID ${summary.id} 详细报告失败:`, reportError)
      }
      
      // 添加延迟避免触发API频率限制
      if (i < chainSummaries.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
    
    factionData.message = `已加载 ${factionData.chains.length} 条chain的详细报告${chainSummaries.length === 100 ? ' (已显示最近的100条)' : ''}`
    
  } catch (error) {
    console.error(`处理帮派 ${factionInfo.name} chains失败:`, error)
    factionData.message = `处理 ${factionInfo.name} 的chain数据失败: ${error.message}`
  }
  
  factionChains.value.push(factionData)
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit', 
    hour12: false, 
    timeZone: 'UTC' 
  })
}

const formatDuration = (seconds) => {
  if (isNaN(seconds) || seconds < 0) return 'N/A'
  const d = Math.floor(seconds / (3600 * 24))
  const h = Math.floor(seconds % (3600 * 24) / 3600)
  const m = Math.floor(seconds % 3600 / 60)
  const s = Math.floor(seconds % 60)
  
  let parts = []
  if (d > 0) parts.push(d + "天")
  if (h > 0) parts.push(h + "小时")
  if (m > 0) parts.push(m + "分钟")
  if (s > 0 || parts.length === 0) parts.push(s + "秒")
  
  return parts.join(' ')
}
</script>

<style scoped>
.chain-analyzer-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-section {
  margin: 20px 0;
}

.faction-card {
  border: 1px solid #e4e7ed;
}

.chain-details {
  padding: 10px 0;
}

.stats-card {
  height: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.stat-item .label {
  font-weight: 500;
  color: #606266;
}

.stat-item .value {
  font-weight: 600;
  color: #303133;
}

.section-card {
  border: 1px solid #ebeef5;
}

.non-attackers {
  max-height: 200px;
  overflow-y: auto;
}

.war-details-card {
  border: 1px solid #e4e7ed;
}

.chains-container {
  margin-top: 10px;
}
</style> 