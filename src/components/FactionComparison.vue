<template>
  <el-card class="faction-comparison-card">
    <template #header>
      <div class="card-header">
        <h2>帮派实力对比分析器</h2>
      </div>
    </template>
    <p>输入两个帮派ID进行实力对比分析，包括最近四个月的RW数据、Chain数据和成员个人数据。</p>
    
    <!-- API Key 配置 -->
    <el-card class="api-config-card" style="margin-bottom: 20px;">
      <template #header>
        <h4>API 密钥配置</h4>
      </template>
      <el-form :model="apiForm" label-width="100px">
        <el-form-item label="API 密钥">
          <el-input
            v-model="apiForm.apiKeys"
            type="textarea"
            :rows="3"
            placeholder="请输入API密钥，多个密钥用换行分隔。支持多密钥并行加速获取数据。"
          />
          <div class="api-help-text">
            <el-text size="small" type="info">
              • 每行一个API密钥<br>
              • 支持多密钥并行请求加速<br>
              • 单个密钥限制50次/分钟
            </el-text>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 帮派输入 -->
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="帮派1 ID">
            <el-input 
              v-model="form.faction1Id" 
              placeholder="请输入帮派1的ID" 
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="帮派2 ID">
            <el-input 
              v-model="form.faction2Id" 
              placeholder="请输入帮派2的ID" 
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item>
        <el-button 
          type="primary" 
          @click="startComparison" 
          :loading="loading"
          :disabled="!canStartComparison"
        >
          开始分析
        </el-button>
        <el-button 
          v-if="loading"
          @click="stopComparison"
        >
          停止分析
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 进度显示 -->
    <div v-if="loading || statusMessage" class="progress-section">
      <el-card class="progress-card">
        <template #header>
          <h4>数据获取进度</h4>
        </template>
        
        <!-- 总体进度 -->
        <div class="progress-item">
          <div class="progress-label">总体进度</div>
          <el-progress 
            :percentage="overallProgress" 
            :status="loading ? '' : 'success'"
            :stroke-width="20"
          />
          <div class="progress-text">{{ progressText }}</div>
        </div>

        <!-- 详细进度 -->
        <div v-if="detailedProgress.length > 0" class="detailed-progress">
          <el-collapse>
            <el-collapse-item title="详细进度" name="details">
              <div v-for="item in detailedProgress" :key="item.key" class="progress-detail-item">
                <div class="progress-detail-label">{{ item.label }}</div>
                <el-progress 
                  :percentage="item.percentage" 
                  :status="item.status === 'active' ? '' : item.status"
                  :stroke-width="12"
                />
                <div class="progress-detail-text">{{ item.text }}</div>
              </div>
            </el-collapse-item>
          </el-collapse>
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

    <!-- 缓存信息 -->
    <el-card v-if="cacheInfo.length > 0" class="cache-info-card" style="margin-top: 20px;">
      <template #header>
        <div class="cache-header">
          <h4>缓存数据信息</h4>
          <div>
            <el-button size="small" @click="clearCache">清空缓存</el-button>
          </div>
        </div>
      </template>
      <el-collapse>
        <el-collapse-item title="查看缓存详情" name="cache">
          <el-table :data="cacheInfo" size="small">
            <el-table-column prop="type" label="数据类型" width="150" />
            <el-table-column prop="id" label="ID" width="100" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="lastUpdated" label="最后更新时间" width="180" />
            <el-table-column prop="dataSize" label="数据大小" width="120" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="viewCacheData(row.key)">查看</el-button>
                <el-button size="small" type="danger" @click="removeCacheItem(row.key)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 结果显示区域 -->
    <div v-if="comparisonResult" class="comparison-result">
      <el-card class="result-card" style="margin-top: 20px;">
        <template #header>
          <h3>对比分析结果</h3>
        </template>
        <div class="result-summary">
          <p>数据获取完成！共获取到：</p>
          <ul>
            <li>帮派1 ({{ comparisonResult.faction1.name }}): {{ getMemberCount(comparisonResult.faction1.members) }} 名成员</li>
            <li>帮派2 ({{ comparisonResult.faction2.name }}): {{ getMemberCount(comparisonResult.faction2.members) }} 名成员</li>
            <li>RW 数据: {{ comparisonResult.rwDataCount }} 条记录 ({{ comparisonResult.detailedRwCount }} 条详细报告)</li>
            <li>Chain 数据: {{ comparisonResult.chainDataCount }} 条记录 ({{ comparisonResult.detailedChainCount }} 条详细报告)</li>
            <li>个人统计数据: {{ comparisonResult.personalStatsCount }} 条记录</li>
          </ul>
          
          <div style="margin-top: 15px;">
            <h4>数据详情</h4>
            <el-row :gutter="20">
              <el-col :span="12">
                <h5>{{ comparisonResult.faction1.name }}</h5>
                <ul>
                  <li>RW: {{ comparisonResult.faction1.rankedWars.length }} 条</li>
                  <li>Chain: {{ comparisonResult.faction1.chains.length }} 条</li>
                  <li>成员个人数据: {{ Object.keys(comparisonResult.faction1.personalStats).filter(id => comparisonResult.faction1.personalStats[id]).length }} 条</li>
                </ul>
              </el-col>
              <el-col :span="12">
                <h5>{{ comparisonResult.faction2.name }}</h5>
                <ul>
                  <li>RW: {{ comparisonResult.faction2.rankedWars.length }} 条</li>
                  <li>Chain: {{ comparisonResult.faction2.chains.length }} 条</li>
                  <li>成员个人数据: {{ Object.keys(comparisonResult.faction2.personalStats).filter(id => comparisonResult.faction2.personalStats[id]).length }} 条</li>
                </ul>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-card>

      <!-- PVP胜率预测 -->
      <el-card v-if="comparisonResult.winRatePrediction" class="win-rate-card" style="margin-top: 20px;">
        <template #header>
          <h3>🏆 PVP胜率预测</h3>
        </template>
        <div class="win-rate-display">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="faction-win-rate faction-1">
                <h4>{{ comparisonResult.faction1.name }}</h4>
                <div class="win-percentage">
                  {{ comparisonResult.winRatePrediction.faction1WinRate }}%
                </div>
                <el-progress 
                  :percentage="comparisonResult.winRatePrediction.faction1WinRate" 
                  :stroke-width="20"
                  :color="comparisonResult.winRatePrediction.faction1WinRate > 50 ? '#67c23a' : '#f56c6c'"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="faction-win-rate faction-2">
                <h4>{{ comparisonResult.faction2.name }}</h4>
                <div class="win-percentage">
                  {{ comparisonResult.winRatePrediction.faction2WinRate }}%
                </div>
                <el-progress 
                  :percentage="comparisonResult.winRatePrediction.faction2WinRate" 
                  :stroke-width="20"
                  :color="comparisonResult.winRatePrediction.faction2WinRate > 50 ? '#67c23a' : '#f56c6c'"
                />
              </div>
            </el-col>
          </el-row>
          <div class="analysis-text">
            <el-alert 
              :title="comparisonResult.winRatePrediction.analysis"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </el-card>

      <!-- 帮派实力详细分析 -->
      <el-card v-if="comparisonResult.faction1Analysis && comparisonResult.faction2Analysis" class="strength-analysis-card" style="margin-top: 20px;">
        <template #header>
          <h3>📊 帮派实力详细分析</h3>
        </template>
        
        <!-- 整体对比 -->
        <div class="overall-comparison">
          <h4>整体实力对比</h4>
          <el-table :data="[
            {
              metric: '平均BS',
              faction1: Math.round(comparisonResult.faction1Analysis.averageBS),
              faction2: Math.round(comparisonResult.faction2Analysis.averageBS)
            },
            {
              metric: '四个月平均开枪数',
              faction1: Math.round(comparisonResult.faction1Analysis.averageAttacksFourMonth),
              faction2: Math.round(comparisonResult.faction2Analysis.averageAttacksFourMonth)
            },
            {
              metric: '最近一个月平均开枪数',
              faction1: Math.round(comparisonResult.faction1Analysis.averageAttacksPerMonth),
              faction2: Math.round(comparisonResult.faction2Analysis.averageAttacksPerMonth)
            },
            {
              metric: '综合活跃度分数',
              faction1: Math.round(comparisonResult.faction1Analysis.averageActivityScore),
              faction2: Math.round(comparisonResult.faction2Analysis.averageActivityScore)
            },
            {
              metric: '成员数量',
              faction1: comparisonResult.faction1Analysis.memberCount,
              faction2: comparisonResult.faction2Analysis.memberCount
            }
          ]" style="width: 100%">
            <el-table-column prop="metric" label="指标" width="200" />
            <el-table-column :label="comparisonResult.faction1.name" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.faction1 > row.faction2 ? '#67c23a' : '#909399' }">
                  {{ row.faction1 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column :label="comparisonResult.faction2.name" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.faction2 > row.faction1 ? '#67c23a' : '#909399' }">
                  {{ row.faction2 }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 成员详细分析 -->
        <div class="member-analysis" style="margin-top: 30px;">
          <h4>成员详细分析</h4>
          <el-tabs type="border-card">
            <el-tab-pane :label="comparisonResult.faction1.name">
              <div class="member-count-info">
                共 {{ comparisonResult.faction1Analysis.memberAnalysis.length }} 名成员
              </div>
              <el-table 
                :data="comparisonResult.faction1Analysis.memberAnalysis" 
                size="small"
                max-height="600"
                :default-sort="{ prop: 'activityScore', order: 'descending' }"
              >
                <el-table-column prop="name" label="成员名" width="120" fixed="left" />
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="estimatedBS" label="预估BS" width="100" align="center" sortable>
                  <template #default="{ row }">
                    <el-tag :type="row.confidence === 'high' ? 'success' : row.confidence === 'medium' ? 'warning' : 'info'" size="small">
                      {{ row.estimatedBS.toLocaleString() }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="fourMonthAttacks" label="四月开枪数" width="100" align="center" sortable />
                <el-table-column prop="oneMonthAttacks" label="一月开枪数" width="100" align="center" sortable />
                <el-table-column prop="hosPercentage" label="HOS占比" width="80" align="center" sortable>
                  <template #default="{ row }">
                    <span :style="{ color: row.hosPercentage > 20 ? '#67c23a' : '#909399' }">
                      {{ row.hosPercentage.toFixed(1) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="revengePercentage" label="复仇占比" width="80" align="center" sortable>
                  <template #default="{ row }">
                    <span :style="{ color: row.revengePercentage > 10 ? '#f56c6c' : '#909399' }">
                      {{ row.revengePercentage.toFixed(1) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="活跃时间段" min-width="120">
                  <template #default="{ row }">
                    <span v-if="row.peakHours.length > 0" class="peak-hours">
                      {{ formatPeakHours(row.peakHours) }}
                    </span>
                    <span v-else style="color: #909399;">无数据</span>
                  </template>
                </el-table-column>
                <el-table-column prop="activityScore" label="活跃度分数" width="100" align="center" sortable>
                  <template #default="{ row }">
                    <el-tag :type="row.activityScore > 100 ? 'success' : row.activityScore > 50 ? 'warning' : 'info'" size="small">
                      {{ Math.round(row.activityScore) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="comparisonResult.faction2.name">
              <div class="member-count-info">
                共 {{ comparisonResult.faction2Analysis.memberAnalysis.length }} 名成员
              </div>
              <el-table 
                :data="comparisonResult.faction2Analysis.memberAnalysis" 
                size="small"
                max-height="600"
                :default-sort="{ prop: 'activityScore', order: 'descending' }"
              >
                <el-table-column prop="name" label="成员名" width="120" fixed="left" />
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="estimatedBS" label="预估BS" width="100" align="center" sortable>
                  <template #default="{ row }">
                    <el-tag :type="row.confidence === 'high' ? 'success' : row.confidence === 'medium' ? 'warning' : 'info'" size="small">
                      {{ row.estimatedBS.toLocaleString() }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="fourMonthAttacks" label="四月开枪数" width="100" align="center" sortable />
                <el-table-column prop="oneMonthAttacks" label="一月开枪数" width="100" align="center" sortable />
                <el-table-column prop="hosPercentage" label="HOS占比" width="80" align="center" sortable>
                  <template #default="{ row }">
                    <span :style="{ color: row.hosPercentage > 20 ? '#67c23a' : '#909399' }">
                      {{ row.hosPercentage.toFixed(1) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="revengePercentage" label="复仇占比" width="80" align="center" sortable>
                  <template #default="{ row }">
                    <span :style="{ color: row.revengePercentage > 10 ? '#f56c6c' : '#909399' }">
                      {{ row.revengePercentage.toFixed(1) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="活跃时间段" min-width="120">
                  <template #default="{ row }">
                    <span v-if="row.peakHours.length > 0" class="peak-hours">
                      {{ formatPeakHours(row.peakHours) }}
                    </span>
                    <span v-else style="color: #909399;">无数据</span>
                  </template>
                </el-table-column>
                <el-table-column prop="activityScore" label="活跃度分数" width="100" align="center" sortable>
                  <template #default="{ row }">
                    <el-tag :type="row.activityScore > 100 ? 'success' : row.activityScore > 50 ? 'warning' : 'info'" size="small">
                      {{ Math.round(row.activityScore) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>
    </div>
  </el-card>
  
  <!-- 缓存数据查看对话框 -->
  <el-dialog
    v-model="showCacheDataDialog"
    title="缓存数据详情"
    width="80%"
    :show-close="true"
  >
    <div class="cache-data-content">
      <el-tabs>
        <el-tab-pane label="格式化JSON" name="formatted">
          <pre class="json-content">{{ formatJsonData(selectedCacheData) }}</pre>
        </el-tab-pane>
        <el-tab-pane label="原始数据" name="raw">
          <el-input
            v-model="rawJsonData"
            type="textarea"
            :rows="20"
            readonly
            style="font-family: 'Courier New', monospace;"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
    <template #footer>
      <el-button @click="showCacheDataDialog = false">关闭</el-button>
      <el-button type="primary" @click="copyCacheData">复制数据</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = 'https://api.torn.com/v2'
const RATE_LIMIT_PER_MINUTE = 50
const RATE_LIMIT_INTERVAL = 60000 // 1分钟

// BS预测算法常量
const BS_CONSTANTS = {
  L: [2, 2.8, 3.2, 3.2, 3.6, 3.8, 3.7, 4, 4.8, 4.8, 5.2, 5.2, 5.4, 5.8, 5.8, 6, 6.4, 6.6, 6.8, 7, 7, 7, 7, 7.3, 8],
  W: [200, 500, 1000, 2000, 2750, 3000, 3500, 4000, 6000, 7000, 8000, 11000, 12420, 18000, 18100, 24140, 31260, 36610, 46640, 56520, 67775, 84535, 106305, 100000, Number.MAX_SAFE_INTEGER],
  J: [2, 6, 11, 26, 31, 50, 71, 100],
  K: [100, 5000, 10000, 20000, 30000, 50000],
  V: [5000000, 50000000, 500000000, 5000000000, 50000000000],
  B: [2000, 20000, 200000, 2000000, 20000000, 200000000],
  R: [2500, 25000, 250000, 2500000, 35000000, 250000000],
  Y: {
    "Absolute beginner": 1, "Beginner": 2, "Inexperienced": 3, "Rookie": 4,
    "Novice": 5, "Below average": 6, "Average": 7, "Reasonable": 8,
    "Above average": 9, "Competent": 10, "Highly competent": 11,
    "Veteran": 12, "Distinguished": 13, "Highly distinguished": 14,
    "Professional": 15, "Star": 16, "Master": 17, "Outstanding": 18,
    "Celebrity": 19, "Supreme": 20, "Idolised": 21, "Champion": 22,
    "Heroic": 23, "Legendary": 24, "Elite": 25, "Invincible": 26
  }
}

// 表单数据
const apiForm = reactive({
  apiKeys: ''
})

const form = reactive({
  faction1Id: '',
  faction2Id: ''
})

// 状态管理
const loading = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const progressText = ref('')
const overallProgress = ref(0)
const detailedProgress = ref([])
const comparisonResult = ref(null)
const abortController = ref(null)

// 缓存管理
const dataCache = ref(new Map())
const cacheInfo = ref([])

// 缓存数据查看
const showCacheDataDialog = ref(false)
const selectedCacheData = ref(null)
const rawJsonData = ref('')

// API密钥管理
const apiKeyPool = ref([])
const apiKeyUsage = ref(new Map()) // 跟踪每个API密钥的使用情况

// 计算属性
const canStartComparison = computed(() => {
  return form.faction1Id && form.faction2Id && getValidApiKeys().length > 0
})

// 获取有效的API密钥列表
const getValidApiKeys = () => {
  return apiForm.apiKeys
    .split('\n')
    .map(key => key.trim())
    .filter(key => key.length > 0)
}

// API请求队列管理
class ApiRequestQueue {
  constructor(apiKeys) {
    this.apiKeys = apiKeys
    this.keyUsage = new Map()
    this.requestQueue = []
    this.isProcessing = false
    
    // 初始化每个API密钥的使用统计
    apiKeys.forEach(key => {
      this.keyUsage.set(key, {
        requests: [],
        lastReset: Date.now()
      })
    })
  }

  // 获取可用的API密钥
  getAvailableApiKey() {
    const now = Date.now()
    
    for (const apiKey of this.apiKeys) {
      const usage = this.keyUsage.get(apiKey)
      
      // 清理超过1分钟的请求记录
      usage.requests = usage.requests.filter(time => now - time < RATE_LIMIT_INTERVAL)
      
      // 如果该密钥的请求数未达到限制
      if (usage.requests.length < RATE_LIMIT_PER_MINUTE) {
        return apiKey
      }
    }
    
    return null
  }

  // 记录API密钥使用
  recordApiKeyUsage(apiKey) {
    const usage = this.keyUsage.get(apiKey)
    if (usage) {
      usage.requests.push(Date.now())
    }
  }

  // 添加请求到队列
  async addRequest(requestFn) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({ requestFn, resolve, reject })
      this.processQueue()
    })
  }

  // 处理请求队列
  async processQueue() {
    if (this.isProcessing || this.requestQueue.length === 0) {
      return
    }

    this.isProcessing = true

    while (this.requestQueue.length > 0) {
      const availableKey = this.getAvailableApiKey()
      
      if (!availableKey) {
        // 等待一段时间再重试
        await new Promise(resolve => setTimeout(resolve, 1000))
        continue
      }

      const { requestFn, resolve, reject } = this.requestQueue.shift()
      
      try {
        this.recordApiKeyUsage(availableKey)
        const result = await requestFn(availableKey)
        resolve(result)
      } catch (error) {
        reject(error)
      }

      // 添加小延迟避免过快请求
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    this.isProcessing = false
  }
}

// API请求函数
const fetchApi = async (endpoint, apiKey) => {
  let url = `${API_BASE_URL}${endpoint}`
  if (url.includes('?')) {
    url += `&key=${apiKey}`
  } else {
    url += `?key=${apiKey}`
  }
  
  console.log(`发起API请求: ${url.replace(/key=[^&]+/, 'key=***')}`)
  
  try {
    const response = await axios.get(url, {
      signal: abortController.value?.signal
    })
    
    console.log(`API响应成功:`, response.data)
    
    if (response.data.error) {
      throw new Error(`Torn API 错误: ${response.data.error.error} (代码: ${response.data.error.code})`)
    }
    
    return response.data
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('请求被取消')
    }
    
    console.error(`API请求失败:`, error)
    
    if (error.response) {
      const errorData = error.response.data
      console.error(`API错误响应:`, errorData)
      let errorMessage = `API请求失败，状态码: ${error.response.status}.`
      if (errorData && errorData.error && errorData.error.error) {
        errorMessage += ` 错误: ${errorData.error.error}`
      }
      throw new Error(errorMessage)
    }
    throw error
  }
}

// 缓存相关函数
const getCacheKey = (type, id, timeRange = '') => {
  return `${type}_${id}_${timeRange}`
}

const getCachedData = (key) => {
  const cached = dataCache.value.get(key)
  if (cached && Date.now() - cached.timestamp < 30 * 60 * 1000) { // 30分钟缓存
    return cached.data
  }
  return null
}

const setCachedData = (key, data, name = '') => {
  dataCache.value.set(key, {
    data,
    timestamp: Date.now(),
    name
  })
  updateCacheInfo()
}

const updateCacheInfo = () => {
  cacheInfo.value = Array.from(dataCache.value.entries()).map(([key, value]) => {
    const [type, id] = key.split('_')
    return {
      key,
      type: type === 'faction' ? '帮派信息' : 
            type === 'members' ? '成员列表' :
            type === 'personalstats' ? '个人数据' :
            type === 'rankedwars' ? 'RW数据' :
            type === 'chains' ? 'Chain数据' : type,
      id,
      name: value.name || '未知',
      lastUpdated: new Date(value.timestamp).toLocaleString('zh-CN'),
      dataSize: getDataSize(value.data)
    }
  })
}

const getDataSize = (data) => {
  const size = JSON.stringify(data).length
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const clearCache = () => {
  dataCache.value.clear()
  updateCacheInfo()
  ElMessage.success('缓存已清空')
}

const removeCacheItem = (key) => {
  dataCache.value.delete(key)
  updateCacheInfo()
  ElMessage.success('缓存项已删除')
}

// 查看缓存数据
const viewCacheData = (key) => {
  const cached = dataCache.value.get(key)
  if (cached) {
    selectedCacheData.value = cached.data
    rawJsonData.value = JSON.stringify(cached.data, null, 2)
    showCacheDataDialog.value = true
  }
}

// 格式化JSON数据显示
const formatJsonData = (data) => {
  if (!data) return ''
  try {
    return JSON.stringify(data, null, 2)
  } catch (error) {
    return String(data)
  }
}

// 复制缓存数据
const copyCacheData = () => {
  if (rawJsonData.value) {
    navigator.clipboard.writeText(rawJsonData.value).then(() => {
      ElMessage.success('数据已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}

// BS预测算法实现
const calculateBSPrediction = (userProfile, personalStats, criminalRecord) => {
  try {
    console.log('开始BS预测计算:', { userProfile, personalStats, criminalRecord })
    
    if (!userProfile || !personalStats) {
      console.warn('BS预测：缺少必要数据')
      return { bs: 0, bsScore: 0, confidence: 'low' }
    }
    
    // 1. 估算总能量消耗
    const totalEnergy = calculateTotalEnergy(userProfile, personalStats)
    console.log('总能量计算结果:', totalEnergy)
    
    // 2. 模拟健身房锻炼
    const totalStats = simulateGymTraining(totalEnergy, personalStats, userProfile)
    console.log('健身房模拟结果:', totalStats)
    
    // 3. 根据Rank进行修正
    const finalBS = applyRankCorrection(totalStats, userProfile, criminalRecord)
    console.log('Rank修正后结果:', finalBS)
    
    // 计算BS分数 (开根号再乘2)
    const bsScore = Math.sqrt(finalBS) * 2
    
    return {
      bs: Math.floor(finalBS),
      bsScore: Math.floor(bsScore),
      confidence: totalEnergy > 1000000 ? 'high' : totalEnergy > 100000 ? 'medium' : 'low'
    }
  } catch (error) {
    console.error('BS预测计算失败:', error)
    return { bs: 0, bsScore: 0, confidence: 'error' }
  }
}

// 计算总能量消耗
const calculateTotalEnergy = (profile, stats) => {
  const now = Math.floor(Date.now() / 1000)
  const startTimestamp = Math.floor(new Date('2011-11-22').getTime() / 1000)
  
  // 计算捐献者比例
  const m = Math.min(profile.age, (now - startTimestamp) / 86400)
  const donatorPercent = Math.min((stats.other?.donator_days || 0) / m, 1)
  
  // 估算活跃天数
  const y = 480 + 240 * donatorPercent
  const F = 611255 / y
  const a = (now - (profile.last_action?.timestamp || now)) / 86400
  const ageM = Math.max(1, 21 * (profile.age - a) / 24)
  
  const N = 3 * ((stats.other?.activity?.time || 0) / 86400) + (stats.travel?.time_spent || 0) / 86400
  
  // 药物能量估算 - 使用正确的API字段名
  const drugEnergy = (
    75 * (stats.drugs?.ecstasy || 0) +
    210 * (stats.drugs?.vicodin || 0) +
    150 * (stats.drugs?.xanax || 0) +
    75 * (stats.drugs?.lsd || 0) +
    150 * (stats.drugs?.ketamine || 0) +
    150 * (stats.drugs?.opium || 0) +
    150 * (stats.drugs?.pcp || 0) +
    150 * (stats.drugs?.shrooms || 0) +
    150 * (stats.drugs?.speed || 0) +
    150 * (stats.drugs?.cannabis || 0)
  ) / 1440
  
  // 犯罪活跃度估算 - 使用正确的API字段名
  let crimeEnergy = 0
  if (stats.crimes) {
    const crimes = stats.crimes
    crimeEnergy = (
      (crimes.theft || 0) * 2 +
      (crimes.sell_illegal_goods || 0) * 3 +
      (crimes.drug_deals || 0) * 4 +
      (crimes.computer || 0) * 5 +
      (crimes.murder || 0) * 10 +
      (crimes.fraud || 0) * 6 +
      (crimes.auto_theft || 0) * 3 +
      (crimes.other || 0) * 3 +
      (crimes.organized_crimes || 0) * 8
    ) / 1440
  }
  
  if (crimeEnergy < F) {
    const correctionFactor = Math.min(F / crimeEnergy, 3)
    crimeEnergy *= correctionFactor
  }
  
  const estimateActiveDays = Math.min(ageM, Math.max(N, drugEnergy, crimeEnergy))
  
  // 计算各部分能量 - 使用正确的API字段名
  const natureEnergy = y * estimateActiveDays
  const itemEnergy = (
    150 * (stats.other?.refills?.energy || 0) +
    250 * (stats.drugs?.xanax || 0) +
    50 * (stats.drugs?.lsd || 0) +
    20 * (stats.items?.used?.energy_drinks || 0) +
    150 * (stats.items?.used?.boosters || 0)
  )
  const expendEnergy = (
    25 * ((stats.attacking?.attacks?.won || 0) + (stats.attacking?.attacks?.stalemate || 0) + (stats.attacking?.attacks?.lost || 0)) +
    25 * (stats.hospital?.reviving?.revives || 0) +
    5 * (stats.items?.found?.dump || 0)
  )
  
  const totalEnergy = Math.max(0, natureEnergy + itemEnergy - expendEnergy)
  return totalEnergy
}

// 模拟健身房锻炼
const simulateGymTraining = (totalEnergy, stats, profile) => {
  let i = 0 // 总属性点
  let s = totalEnergy // 剩余能量
  let r = 0 // 当前健身房索引
  let l = BS_CONSTANTS.W[0] // 当前健身房容量
  
  const now = Math.floor(Date.now() / 1000)
  const startTimestamp = Math.floor(new Date('2022-08-02').getTime() / 1000)
  const G = (now - startTimestamp) / 86400
  const a = (now - (profile.last_action?.timestamp || now)) / 86400
  const H = totalEnergy * (G - a) / (profile.age - a)
  
  while (s > 0 && r < BS_CONSTANTS.L.length) {
    // 确定本次消耗能量
    const e = Math.min(BS_CONSTANTS.W[r], s, l, 1000)
    
    // 获取当前健身房系数
    const U = BS_CONSTANTS.L[r]
    
    // 计算本次属性增长
    let attributeGain = 0
    
    if (s > H && i < 200000000) {
      // 旧公式
      attributeGain = 1.122 * 1.02 * U * e * (((3.48e-9 * Math.log(4750) + 3.1e-7) * i / 4) + 0.32433 - 0.0301431777)
    } else if (s > H) {
      // 属性上限
      const cappedE = s - H
      attributeGain = ((stats.xantaken || 0) <= (stats.lsdtaken || 0) && (stats.xantaken || 0) <= 100) 
        ? (3240 * cappedE) 
        : (2510 * cappedE)
    } else {
      // 新公式
      let q = (i >= 3000000000) ? (i - 2000000000) : (i / 3)
      q = (q < 50000000) ? q : ((q - 50000000) / (8.77635 * Math.log10(q)) + 50000000)
      attributeGain = 5e-6 * U * e * 1.165248 * (q * Math.round(1 + 0.07 * Math.round(Math.log(21), 4), 4) + 8 * Math.pow(5000, 1.05) + 1600 * (1 - Math.pow(5000 / 99999, 2)) + 2000)
    }
    
    // 更新变量
    i += attributeGain
    s -= e
    l -= e
    
    // 切换健身房
    if (l <= 0 && r < BS_CONSTANTS.L.length - 1) {
      r++
      l = BS_CONSTANTS.W[r]
    }
  }
  
  // SE加成
  if (stats.items?.used?.stat_enhancers && stats.items.used.stat_enhancers > 0) {
    const E = stats.items.used.stat_enhancers
    i = 0.5 * i + 0.25 * i * (1 + 0.85 * (Math.pow(1.01, 0.8 * E) - 1)) + 0.25 * i * (1 + 0.85 * (Math.pow(1.01, 0.2 * E) - 1))
  }
  
  return Math.floor(i)
}

// 应用Rank修正
const applyRankCorrection = (totalStats, profile, criminalRecord) => {
  let c = BS_CONSTANTS.Y[profile.rank] || 1
  c--
  
  // 根据等级修正
  for (const threshold of BS_CONSTANTS.J) {
    if (profile.level >= threshold) c--
  }
  
  // 根据犯罪次数修正 - 使用正确的API字段名
  const totalCrimes = criminalRecord?.total || 0
  for (const threshold of BS_CONSTANTS.K) {
    if (totalCrimes >= threshold) c--
  }
  
  // 根据总资产修正 - 使用正确的API字段名
  const networth = profile.networth?.total || profile.networth || 0
  for (const threshold of BS_CONSTANTS.V) {
    if (networth >= threshold) c--
  }
  
  // 确定Rank对应的BS范围
  let lowerBound, upperBound
  if (c <= 0) {
    lowerBound = 0
    upperBound = BS_CONSTANTS.R[0]
  } else if (c >= BS_CONSTANTS.B.length) {
    lowerBound = BS_CONSTANTS.B[BS_CONSTANTS.B.length - 1]
    upperBound = Number.MAX_SAFE_INTEGER
  } else {
    lowerBound = BS_CONSTANTS.B[c - 1]
    upperBound = BS_CONSTANTS.R[c]
  }
  
  // 根据计算结果与范围关系返回最终值
  if (totalStats < lowerBound) {
    return (totalStats + lowerBound) / 2 // 返回中间值
  } else if (totalStats > upperBound) {
    return (upperBound + totalStats) / 2 // 返回中间值
  } else {
    return totalStats
  }
}

// 辅助函数
const getMemberCount = (members) => {
  if (!members) return 0
  if (Array.isArray(members)) return members.length
  return Object.keys(members).length
}

// 格式化活跃时间段
const formatPeakHours = (peakHours) => {
  if (!peakHours || peakHours.length === 0) return '无数据'
  
  // 将连续的时间段合并
  const ranges = []
  let start = peakHours[0]
  let end = peakHours[0]
  
  for (let i = 1; i < peakHours.length; i++) {
    if (peakHours[i] === end + 1) {
      end = peakHours[i]
    } else {
      ranges.push(start === end ? `${start}:00` : `${start}:00-${end}:00`)
      start = peakHours[i]
      end = peakHours[i]
    }
  }
  ranges.push(start === end ? `${start}:00` : `${start}:00-${end}:00`)
  
  return ranges.join(', ')
}

// 获取四个月前的时间戳
const getFourMonthsAgo = () => {
  const now = new Date()
  now.setMonth(now.getMonth() - 4)
  return Math.floor(now.getTime() / 1000)
}

// 更新进度
const updateProgress = (step, total, message) => {
  overallProgress.value = Math.round((step / total) * 100)
  progressText.value = `${step}/${total} - ${message}`
}

const updateDetailedProgress = (key, label, step, total, status = 'active') => {
  const existing = detailedProgress.value.find(item => item.key === key)
  const percentage = total > 0 ? Math.round((step / total) * 100) : 0
  const text = `${step}/${total}`
  
  if (existing) {
    existing.percentage = percentage
    existing.text = text
    existing.status = status
  } else {
    detailedProgress.value.push({
      key,
      label,
      percentage,
      text,
      status
    })
  }
}

// 获取帮派基本信息
const getFactionInfo = async (factionId, requestQueue) => {
  const cacheKey = getCacheKey('faction', factionId)
  let cached = getCachedData(cacheKey)
  
  if (cached) {
    return cached
  }
  
  statusMessage.value = `正在获取帮派 ${factionId} 的基本信息...`
  
  const data = await requestQueue.addRequest(async (apiKey) => {
    return await fetchApi(`/faction/${factionId}`, apiKey)
  })
  
  // 根据实际数据结构提取帮派信息
  const factionInfo = data.basic || data.faction || data
  if (!factionInfo || !factionInfo.name) {
    console.error('帮派数据结构:', data)
    throw new Error(`获取帮派 ${factionId} 信息失败：数据格式不正确`)
  }
  
  setCachedData(cacheKey, factionInfo, factionInfo.name)
  return factionInfo
}

// 获取帮派成员列表
const getFactionMembers = async (factionId, requestQueue) => {
  const cacheKey = getCacheKey('members', factionId)
  let cached = getCachedData(cacheKey)
  
  if (cached) {
    return cached
  }
  
  statusMessage.value = `正在获取帮派 ${factionId} 的成员列表...`
  
  const data = await requestQueue.addRequest(async (apiKey) => {
    return await fetchApi(`/faction/${factionId}/members?striptags=true`, apiKey)
  })
  
  // 根据实际数据结构提取成员信息
  const members = data.members || data
  if (!members || !Array.isArray(members)) {
    console.error('成员数据结构:', data)
    throw new Error(`获取帮派 ${factionId} 成员列表失败：数据格式不正确`)
  }
  
  // 将成员数组转换为以ID为键的对象，方便后续处理
  const membersObj = {}
  members.forEach(member => {
    membersObj[member.id] = member
  })
  
  setCachedData(cacheKey, membersObj)
  return membersObj
}

// 获取成员个人数据
const getMemberPersonalStats = async (memberId, requestQueue, memberIndex, totalMembers, factionId) => {
  const cacheKey = getCacheKey('personalstats', memberId)
  let cached = getCachedData(cacheKey)
  
  if (cached) {
    updateDetailedProgress(`members_${factionId}`, `帮派 ${factionId} 成员数据`, memberIndex, totalMembers)
    return cached
  }
  
  updateDetailedProgress(`members_${factionId}`, `帮派 ${factionId} 成员数据`, memberIndex, totalMembers)
  
  try {
    // 检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    // 同时获取用户基本信息和个人统计
    const [profileData, personalStatsData] = await Promise.all([
      requestQueue.addRequest(async (apiKey) => {
        return await fetchApi(`/user/${memberId}`, apiKey)
      }),
      requestQueue.addRequest(async (apiKey) => {
        return await fetchApi(`/user/${memberId}/personalstats?cat=all`, apiKey)
      })
    ])
    
    // 再次检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    // 合并数据
    const combinedData = {
      profile: profileData.profile || profileData,
      personalstats: personalStatsData.personalstats || personalStatsData,
      criminalrecord: personalStatsData.criminalrecord || (profileData.criminalrecord || {})
    }
    
    if (!combinedData.personalstats) {
      console.warn(`成员 ${memberId} 个人数据为空`)
      return null
    }
    
    setCachedData(cacheKey, combinedData)
    return combinedData
  } catch (error) {
    if (error.message === '请求被取消') {
      throw error
    }
    console.error(`获取成员 ${memberId} 个人数据失败:`, error)
    return null
  }
}

// 获取帮派RW数据
const getFactionRankedWars = async (factionId, requestQueue) => {
  const fourMonthsAgo = getFourMonthsAgo()
  const cacheKey = getCacheKey('rankedwars', factionId, fourMonthsAgo.toString())
  let cached = getCachedData(cacheKey)
  
  if (cached) {
    return cached
  }
  
  statusMessage.value = `正在获取帮派 ${factionId} 的RW数据...`
  
  try {
    // 1. 获取基础RW列表
    const data = await requestQueue.addRequest(async (apiKey) => {
      return await fetchApi(`/faction/${factionId}/rankedwars`, apiKey)
    })
    
    // 提取RW数据
    const allRankedWars = data.rankedwars || data.rankedwarreports || data || []
    console.log(`帮派 ${factionId} 获取到 ${Object.keys(allRankedWars).length} 条RW记录`)
    console.log(`帮派 ${factionId} RW基础数据结构:`, {
      dataKeys: Object.keys(data),
      rankedwarsKeys: data.rankedwars ? Object.keys(data.rankedwars) : [],
      firstRwId: Object.keys(allRankedWars)[0],
      firstRwData: allRankedWars[Object.keys(allRankedWars)[0]]
    })
    
    // 2. 过滤四个月内的RW
    const recentRankedWars = {}
    const currentTime = Math.floor(Date.now() / 1000)
    
    for (const [warKey, war] of Object.entries(allRankedWars)) {
      if (war.start >= fourMonthsAgo) {
        // 使用war.id作为真实的战争ID
        recentRankedWars[war.id] = war
      }
    }
    
    console.log(`帮派 ${factionId} 过滤后剩余 ${Object.keys(recentRankedWars).length} 条最近四个月的RW记录`)
    console.log(`帮派 ${factionId} 真实RW ID示例:`, Object.keys(recentRankedWars).slice(0, 3))
    
    // 3. 高度并发获取每个RW的详细报告
    const detailedRankedWars = []
    const warIds = Object.keys(recentRankedWars) // 这些现在是真实的war.id
    const apiKeys = getValidApiKeys()
    
    updateDetailedProgress(`rw_${factionId}`, `帮派 ${factionId} RW详细报告`, 0, warIds.length, '')
    
    if (warIds.length > 0) {
      console.log(`开始并发获取 ${warIds.length} 个RW详细报告，使用 ${apiKeys.length} 个API密钥`)
      
      let processedCount = 0
      const rwQueue = [...warIds] // 复制队列
      
      // 创建并发工作器，每个API密钥一个
      const workers = apiKeys.map(async (apiKey, workerIndex) => {
        console.log(`RW工作器 ${workerIndex + 1} 开始工作`)
        
        while (rwQueue.length > 0) {
          // 检查是否被取消
          if (abortController.value?.signal.aborted) {
            throw new Error('请求被取消')
          }
          
          // 从队列中取出一个RW
          const warId = rwQueue.shift()
          if (!warId) break
          
          try {
            console.log(`RW工作器 ${workerIndex + 1} 开始获取RW ${warId} 的详细报告`)
            console.log(`API请求URL: /faction/${warId}/rankedwarreport`)
            console.log(`RW ID类型和值:`, { warId, type: typeof warId, isString: typeof warId === 'string' })
            
            const reportData = await fetchApi(`/faction/${warId}/rankedwarreport`, apiKey)
            
            if (abortController.value?.signal.aborted) {
              throw new Error('请求被取消')
            }
            
            console.log(`RW ${warId} 详细报告数据:`, reportData)
            
            if (reportData.rankedwarreport) {
              detailedRankedWars.push({
                id: warId, // 这现在是真实的war.id
                basicInfo: recentRankedWars[warId],
                report: reportData.rankedwarreport
              })
              console.log(`RW工作器 ${workerIndex + 1} 成功获取RW ${warId}`)
            } else if (reportData.war || reportData.factions) {
              // 尝试直接使用数据
              detailedRankedWars.push({
                id: warId, // 这现在是真实的war.id
                basicInfo: recentRankedWars[warId],
                report: reportData
              })
              console.log(`RW工作器 ${workerIndex + 1} 使用直接格式获取RW ${warId}`)
            } else {
              console.warn(`RW ${warId} 报告数据格式异常:`, Object.keys(reportData))
              detailedRankedWars.push({
                id: warId, // 这现在是真实的war.id
                basicInfo: recentRankedWars[warId],
                report: null
              })
            }
            
          } catch (reportError) {
            if (reportError.message === '请求被取消') {
              throw reportError
            }
            console.error(`RW工作器 ${workerIndex + 1} 获取RW ${warId} 详细报告失败:`, reportError)
            detailedRankedWars.push({
              id: warId, // 这现在是真实的war.id
              basicInfo: recentRankedWars[warId],
              report: null
            })
          }
          
          // 更新进度
          processedCount++
          updateDetailedProgress(`rw_${factionId}`, `帮派 ${factionId} RW详细报告`, processedCount, warIds.length, '')
          
          // 等待间隔
          await new Promise(resolve => setTimeout(resolve, 1200))
        }
        
        console.log(`RW工作器 ${workerIndex + 1} 完成工作`)
      })
      
      // 等待所有工作器完成
      await Promise.all(workers)
    }
    
    updateDetailedProgress(`rw_${factionId}`, `帮派 ${factionId} RW详细报告`, warIds.length, warIds.length, 'success')
    
    setCachedData(cacheKey, detailedRankedWars)
    return detailedRankedWars
  } catch (error) {
    console.error(`获取帮派 ${factionId} RW数据失败:`, error)
    return []
  }
}

// 获取帮派Chain数据（基于RW时间范围）
const getFactionChains = async (factionId, requestQueue, rankedWars = []) => {
  const fourMonthsAgo = getFourMonthsAgo()
  const cacheKey = getCacheKey('chains', factionId, fourMonthsAgo.toString())
  let cached = getCachedData(cacheKey)
  
  if (cached) {
    return cached
  }
  
  statusMessage.value = `正在获取帮派 ${factionId} 的Chain数据...`
  
  try {
    // 1. 收集所有RW的时间范围
    const timeRanges = []
    for (const rwData of rankedWars) {
      if (rwData.report) {
        timeRanges.push({
          start: rwData.report.start,
          end: rwData.report.end,
          warId: rwData.id
        })
      } else if (rwData.basicInfo) {
        // 如果没有详细报告，使用基础信息
        timeRanges.push({
          start: rwData.basicInfo.start,
          end: rwData.basicInfo.end || (rwData.basicInfo.start + 24 * 3600), // 假设战争持续24小时
          warId: rwData.id
        })
      }
    }
    
    console.log(`帮派 ${factionId} 需要获取 ${timeRanges.length} 个RW时间段的Chain数据`)
    
    // 2. 获取四个月内的所有Chain基础列表
    const data = await requestQueue.addRequest(async (apiKey) => {
      return await fetchApi(`/faction/${factionId}/chains?from=${fourMonthsAgo}`, apiKey)
    })
    
    const allChains = data.chains || data || []
    console.log(`帮派 ${factionId} 获取到 ${Object.keys(allChains).length} 条Chain记录`)
    
    // 3. 过滤RW时间范围内的Chain
    const rwChains = {}
    for (const [chainKey, chain] of Object.entries(allChains)) {
      // 检查Chain是否在任何RW时间范围内
      for (const timeRange of timeRanges) {
        const chainStart = chain.start
        const chainEnd = chain.end
        
        // 判断Chain时间是否与RW时间重叠
        if ((chainStart >= timeRange.start && chainStart <= timeRange.end) ||
            (chainEnd >= timeRange.start && chainEnd <= timeRange.end) ||
            (chainStart <= timeRange.start && chainEnd >= timeRange.end)) {
          
          // 使用chain.id作为真实的Chain ID
          if (!rwChains[chain.id]) {
            rwChains[chain.id] = {
              ...chain,
              relatedWars: []
            }
          }
          rwChains[chain.id].relatedWars.push(timeRange.warId)
        }
      }
    }
    
    console.log(`帮派 ${factionId} 过滤后剩余 ${Object.keys(rwChains).length} 条RW相关的Chain记录`)
    
    // 4. 高度并发获取每个Chain的详细报告
    const detailedChains = []
    const chainIds = Object.keys(rwChains) // 这些现在是真实的chain.id
    const apiKeys = getValidApiKeys()
    
    updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, 0, chainIds.length, '')
    
    if (chainIds.length > 0) {
      console.log(`开始并发获取 ${chainIds.length} 个Chain详细报告，使用 ${apiKeys.length} 个API密钥`)
      
      let processedCount = 0
      const chainQueue = [...chainIds] // 复制队列
      
      // 创建并发工作器，每个API密钥一个
      const workers = apiKeys.map(async (apiKey, workerIndex) => {
        console.log(`Chain工作器 ${workerIndex + 1} 开始工作`)
        
        while (chainQueue.length > 0) {
          // 检查是否被取消
          if (abortController.value?.signal.aborted) {
            throw new Error('请求被取消')
          }
          
          // 从队列中取出一个Chain
          const chainId = chainQueue.shift()
          if (!chainId) break
          
          try {
            console.log(`Chain工作器 ${workerIndex + 1} 开始获取Chain ${chainId} 的详细报告`)
            
            const reportData = await fetchApi(`/faction/${chainId}/chainreport`, apiKey)
            
            if (abortController.value?.signal.aborted) {
              throw new Error('请求被取消')
            }
            
            if (reportData.chainreport && reportData.chainreport.attackers) {
              detailedChains.push({
                id: chainId, // 这现在是真实的chain.id
                basicInfo: rwChains[chainId],
                report: reportData.chainreport,
                relatedWars: rwChains[chainId].relatedWars
              })
              console.log(`Chain工作器 ${workerIndex + 1} 成功获取Chain ${chainId}，攻击者数量: ${reportData.chainreport.attackers.length}`)
            } else if (reportData.attackers) {
              detailedChains.push({
                id: chainId, // 这现在是真实的chain.id
                basicInfo: rwChains[chainId],
                report: reportData,
                relatedWars: rwChains[chainId].relatedWars
              })
              console.log(`Chain工作器 ${workerIndex + 1} 获取Chain ${chainId}（直接格式），攻击者数量: ${reportData.attackers.length}`)
            } else {
              console.warn(`Chain ${chainId} 报告数据结构异常`)
              detailedChains.push({
                id: chainId, // 这现在是真实的chain.id
                basicInfo: rwChains[chainId],
                report: null,
                relatedWars: rwChains[chainId].relatedWars
              })
            }
            
          } catch (reportError) {
            if (reportError.message === '请求被取消') {
              throw reportError
            }
            console.error(`Chain工作器 ${workerIndex + 1} 获取Chain ${chainId} 详细报告失败:`, reportError)
            detailedChains.push({
              id: chainId, // 这现在是真实的chain.id
              basicInfo: rwChains[chainId],
              report: null,
              relatedWars: rwChains[chainId].relatedWars
            })
          }
          
          // 更新进度
          processedCount++
          updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, processedCount, chainIds.length, '')
          
          // 等待间隔
          await new Promise(resolve => setTimeout(resolve, 1200))
        }
        
        console.log(`Chain工作器 ${workerIndex + 1} 完成工作`)
      })
      
      // 等待所有工作器完成
      await Promise.all(workers)
    }
    
    updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, chainIds.length, chainIds.length, 'success')
    
    setCachedData(cacheKey, detailedChains)
    return detailedChains
  } catch (error) {
    console.error(`获取帮派 ${factionId} Chain数据失败:`, error)
    return []
  }
}

// 分析Chain数据中的枪数和活跃时间
const analyzeChainActivity = (chains) => {
  let totalAttacks = 0
  let hosAttacks = 0
  let revengeAttacks = 0
  const timeZoneHours = new Array(24).fill(0)
  const fourMonthsAgo = getFourMonthsAgo()
  const oneMonthAgo = Math.floor(Date.now() / 1000) - (30 * 24 * 3600)
  
  let recentTotalAttacks = 0 // 最近一个月
  
  console.log(`开始分析整体Chain活跃度，总共 ${chains.length} 个Chain`)
  
  chains.forEach((chainData, chainIndex) => {
    if (chainData.report && chainData.report.attackers) {
      // 使用新的数据结构：chainreport.attackers数组
      chainData.report.attackers.forEach(attacker => {
        if (attacker.attacks) {
          const attacks = attacker.attacks
          totalAttacks += attacks.total || 0
          hosAttacks += attacks.hospitalize || 0
          revengeAttacks += attacks.retaliations || 0
          
          // 检查是否是最近一个月（使用Chain的开始时间作为近似）
          if (chainData.report.start >= oneMonthAgo) {
            recentTotalAttacks += attacks.total || 0
          }
          
          // 时区分析 - 改进算法
          const totalAttackCount = attacks.total || 0
          if (totalAttackCount > 0) {
            const chainStart = new Date(chainData.report.start * 1000)
            const chainEnd = new Date(chainData.report.end * 1000)
            const chainDuration = (chainData.report.end - chainData.report.start) / 3600 // 小时
            
            // 根据Chain持续时间和攻击数量，估算攻击分布
            for (let i = 0; i < totalAttackCount; i++) {
              // 在Chain持续时间内均匀分布攻击时间
              const attackOffset = (chainDuration * i / totalAttackCount) // 攻击在Chain中的相对时间（小时）
              const attackTime = new Date(chainStart.getTime() + attackOffset * 3600 * 1000)
              const beijingHour = (attackTime.getUTCHours() + 8) % 24
              timeZoneHours[beijingHour]++
            }
          }
        }
      })
    }
  })
  
  // 计算活跃时间段
  const peakHours = []
  const maxActivity = Math.max(...timeZoneHours)
  const threshold = maxActivity * 0.7 // 70%以上的活跃度认为是活跃时间段
  
  for (let hour = 0; hour < 24; hour++) {
    if (timeZoneHours[hour] >= threshold && timeZoneHours[hour] > 0) {
      peakHours.push(hour)
    }
  }
  
  const result = {
    totalAttacks,
    recentAttacks: recentTotalAttacks,
    hosPercentage: totalAttacks > 0 ? (hosAttacks / totalAttacks * 100) : 0,
    revengePercentage: totalAttacks > 0 ? (revengeAttacks / totalAttacks * 100) : 0,
    peakHours,
    timeZoneDistribution: timeZoneHours
  }
  
  console.log('整体Chain活跃度分析结果:', result)
  return result
}

// 分析个人成员数据
const analyzeMemberData = (members, personalStats, chains) => {
  const memberAnalysis = []
  
  console.log('开始分析成员数据:', {
    memberCount: Object.keys(members).length,
    personalStatsCount: Object.keys(personalStats).length,
    chainCount: chains.length
  })
  
  Object.entries(members).forEach(([memberId, member]) => {
    const memberData = personalStats[memberId]
    if (!memberData || !memberData.personalstats) {
      console.warn(`成员 ${memberId} (${member.name}) 缺少个人数据`)
      return
    }
    
    console.log(`开始分析成员 ${memberId} (${member.name})`)
    
    // 计算BS预测
    const bsPrediction = calculateBSPrediction(
      memberData.profile || {
        age: member.days_in_faction || 100,
        level: member.level,
        rank: member.rank || 'Average',
        last_action: { timestamp: Math.floor(Date.now() / 1000) - 3600 },
        networth: memberData.personalstats?.networth || 0
      },
      memberData.personalstats,
      memberData.personalstats?.crimes || {}
    )
    
    // 分析该成员在Chain中的活跃度
    const memberChainActivity = analyzeMemberChainActivity(memberId, chains)
    
    // 计算活跃度分数
    const activityScore = calculateActivityScore(memberChainActivity, bsPrediction.bsScore)
    
    const memberInfo = {
      id: memberId,
      name: member.name,
      level: member.level,
      rank: member.rank || 'Unknown',
      estimatedBS: bsPrediction.bs,
      bsScore: bsPrediction.bsScore,
      confidence: bsPrediction.confidence,
      fourMonthAttacks: memberChainActivity.fourMonthAttacks,
      oneMonthAttacks: memberChainActivity.oneMonthAttacks,
      hosPercentage: memberChainActivity.hosPercentage,
      revengePercentage: memberChainActivity.revengePercentage,
      peakHours: memberChainActivity.peakHours,
      activityScore: activityScore
    }
    
    console.log(`成员 ${memberId} 分析完成:`, memberInfo)
    memberAnalysis.push(memberInfo)
  })
  
  console.log(`成员数据分析完成，共分析 ${memberAnalysis.length} 个成员`)
  return memberAnalysis.sort((a, b) => b.activityScore - a.activityScore)
}

// 分析单个成员在Chain中的活跃度
const analyzeMemberChainActivity = (memberId, chains) => {
  let fourMonthAttacks = 0
  let oneMonthAttacks = 0
  let hosAttacks = 0
  let revengeAttacks = 0
  const timeZoneHours = new Array(24).fill(0)
  const oneMonthAgo = Math.floor(Date.now() / 1000) - (30 * 24 * 3600)
  
  console.log(`开始分析成员 ${memberId} 的Chain活跃度，总共 ${chains.length} 个Chain`)
  
  chains.forEach((chainData, chainIndex) => {
    if (chainData.report && chainData.report.attackers) {
      // 在attackers数组中查找该成员
      const memberAttacker = chainData.report.attackers.find(attacker => String(attacker.id) === String(memberId))
      if (memberAttacker && memberAttacker.attacks) {
        const attacks = memberAttacker.attacks
        console.log(`成员 ${memberId} 在Chain ${chainIndex + 1} 中的攻击数据:`, attacks)
        
        const totalAttacks = attacks.total || 0
        fourMonthAttacks += totalAttacks
        hosAttacks += attacks.hospitalize || 0
        revengeAttacks += attacks.retaliations || 0
        
        // 检查Chain是否在最近一个月内
        if (chainData.report.start >= oneMonthAgo) {
          oneMonthAttacks += totalAttacks
        }
        
        // 活跃时间段分析 - 改进算法
        if (totalAttacks > 0) {
          const chainStart = new Date(chainData.report.start * 1000)
          const chainEnd = new Date(chainData.report.end * 1000)
          const chainDuration = (chainData.report.end - chainData.report.start) / 3600 // 小时
          
          // 根据Chain持续时间和攻击数量，估算攻击分布
          for (let i = 0; i < totalAttacks; i++) {
            // 在Chain持续时间内均匀分布攻击时间
            const attackOffset = (chainDuration * i / totalAttacks) // 攻击在Chain中的相对时间（小时）
            const attackTime = new Date(chainStart.getTime() + attackOffset * 3600 * 1000)
            const beijingHour = (attackTime.getUTCHours() + 8) % 24
            timeZoneHours[beijingHour]++
          }
        }
      }
    }
  })
  
  // 计算个人活跃时间段
  const peakHours = []
  if (fourMonthAttacks > 0) {
    const maxActivity = Math.max(...timeZoneHours)
    const threshold = Math.max(1, maxActivity * 0.3) // 降低阈值到30%
    
    for (let hour = 0; hour < 24; hour++) {
      if (timeZoneHours[hour] >= threshold) {
        peakHours.push(hour)
      }
    }
  }
  
  console.log(`成员 ${memberId} 活跃度分析结果:`, {
    fourMonthAttacks,
    oneMonthAttacks,
    hosAttacks,
    revengeAttacks,
    peakHours
  })
  
  return {
    fourMonthAttacks,
    oneMonthAttacks,
    hosPercentage: fourMonthAttacks > 0 ? (hosAttacks / fourMonthAttacks * 100) : 0,
    revengePercentage: fourMonthAttacks > 0 ? (revengeAttacks / fourMonthAttacks * 100) : 0,
    peakHours
  }
}

// 计算活跃度分数（BS分数和开枪数的加权）
const calculateActivityScore = (chainActivity, bsScore) => {
  const attackWeight = 0.3 // 开枪数权重
  const bsWeight = 0.4 // BS分数权重
  const recentActivityWeight = 0.2 // 最近活跃度权重
  const specialAttackWeight = 0.1 // 特殊攻击权重
  
  // 标准化四个月开枪数（假设40枪/四个月为平均水平）
  const normalizedFourMonthAttacks = Math.min(chainActivity.fourMonthAttacks / 40, 3) * 100
  
  // 标准化最近一个月开枪数（假设10枪/月为平均水平）
  const normalizedRecentAttacks = Math.min(chainActivity.oneMonthAttacks / 10, 3) * 100
  
  // 标准化BS分数（假设5000为平均水平）
  const normalizedBS = Math.min(bsScore / 5000, 3) * 100
  
  // 特殊攻击奖励（HOS和复仇攻击的权重）
  const specialAttackBonus = (chainActivity.hosPercentage + chainActivity.revengePercentage) / 2
  
  // 活跃时间段多样性奖励
  const timeRangeBonus = chainActivity.peakHours.length > 0 ? Math.min(chainActivity.peakHours.length / 8 * 20, 20) : 0
  
  const finalScore = (
    attackWeight * normalizedFourMonthAttacks +
    bsWeight * normalizedBS +
    recentActivityWeight * normalizedRecentAttacks +
    specialAttackWeight * specialAttackBonus
  ) + timeRangeBonus
  
  console.log(`活跃度分数计算: 四月攻击=${normalizedFourMonthAttacks}, BS=${normalizedBS}, 最近攻击=${normalizedRecentAttacks}, 特殊攻击=${specialAttackBonus}, 时间多样性=${timeRangeBonus}, 最终分数=${finalScore}`)
  
  return Math.max(0, finalScore) // 确保分数不为负
}

// 主要的帮派实力分析函数
const analyzeFactionStrength = (factionData) => {
  console.log('开始帮派实力分析:', factionData)
  
  if (!factionData.members || !factionData.personalStats || !factionData.chains) {
    console.warn('帮派实力分析：缺少必要数据')
    return null
  }
  
  // 分析整体Chain活跃度
  const overallActivity = analyzeChainActivity(factionData.chains)
  
  // 分析每个成员的数据
  const memberAnalysis = analyzeMemberData(
    factionData.members, 
    factionData.personalStats, 
    factionData.chains
  )
  
  // 计算帮派总实力分数
  const totalActivityScore = memberAnalysis.reduce((sum, member) => sum + member.activityScore, 0)
  const averageActivityScore = memberAnalysis.length > 0 ? totalActivityScore / memberAnalysis.length : 0
  
  // 计算总BS和平均BS
  const totalBS = memberAnalysis.reduce((sum, member) => sum + member.estimatedBS, 0)
  const averageBS = memberAnalysis.length > 0 ? totalBS / memberAnalysis.length : 0
  
  return {
    name: factionData.name,
    memberCount: memberAnalysis.length,
    memberAnalysis,
    overallActivity,
    totalActivityScore,
    averageActivityScore,
    totalBS,
    averageBS,
    averageAttacksPerMonth: memberAnalysis.length > 0 
      ? memberAnalysis.reduce((sum, m) => sum + m.oneMonthAttacks, 0) / memberAnalysis.length 
      : 0,
    averageAttacksFourMonth: memberAnalysis.length > 0 
      ? memberAnalysis.reduce((sum, m) => sum + m.fourMonthAttacks, 0) / memberAnalysis.length 
      : 0
  }
}

// 预测PVP胜率
const predictPVPWinRate = (faction1Analysis, faction2Analysis) => {
  if (!faction1Analysis || !faction2Analysis) {
    return { faction1WinRate: 50, faction2WinRate: 50, analysis: '数据不足，无法预测' }
  }
  
  // 综合实力评分权重
  const bsWeight = 0.6 // BS权重
  const activityWeight = 0.3 // 活跃度权重
  const memberCountWeight = 0.1 // 人数权重
  
  // 计算两帮的综合实力分数
  const faction1Score = (
    (faction1Analysis.averageBS / 10000) * bsWeight +
    (faction1Analysis.averageActivityScore / 100) * activityWeight +
    (faction1Analysis.memberCount / 50) * memberCountWeight
  ) * 100
  
  const faction2Score = (
    (faction2Analysis.averageBS / 10000) * bsWeight +
    (faction2Analysis.averageActivityScore / 100) * activityWeight +
    (faction2Analysis.memberCount / 50) * memberCountWeight
  ) * 100
  
  // 计算胜率（使用逻辑函数避免极端值）
  const scoreDiff = faction1Score - faction2Score
  const faction1WinRate = Math.round(50 + (scoreDiff / (1 + Math.abs(scoreDiff) / 20)) * 20)
  const faction2WinRate = 100 - faction1WinRate
  
  // 生成分析说明
  const analysis = `
    ${faction1Analysis.name}: 平均BS ${Math.round(faction1Analysis.averageBS)}, 活跃度 ${Math.round(faction1Analysis.averageActivityScore)}, ${faction1Analysis.memberCount} 人
    ${faction2Analysis.name}: 平均BS ${Math.round(faction2Analysis.averageBS)}, 活跃度 ${Math.round(faction2Analysis.averageActivityScore)}, ${faction2Analysis.memberCount} 人
    
    综合实力评分: ${Math.round(faction1Score)} vs ${Math.round(faction2Score)}
  `
  
  return {
    faction1WinRate: Math.max(10, Math.min(90, faction1WinRate)), // 限制在10%-90%之间
    faction2WinRate: Math.max(10, Math.min(90, faction2WinRate)),
    analysis: analysis.trim(),
    faction1Score,
    faction2Score
  }
}

// 主要的数据获取函数
const fetchAllData = async () => {
  const apiKeys = getValidApiKeys()
  const requestQueue = new ApiRequestQueue(apiKeys)
  
  abortController.value = new AbortController()
  
  try {
    // 总步骤计算（这里是动态的，因为RW和Chain数量未知）
    let totalSteps = 6 // 基本信息获取
    let currentStep = 0
    
    // 获取帮派基本信息
    updateProgress(++currentStep, totalSteps, '获取帮派基本信息...')
    console.log('开始获取帮派基本信息...')
    
    // 检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    const [faction1Info, faction2Info] = await Promise.all([
      getFactionInfo(form.faction1Id, requestQueue),
      getFactionInfo(form.faction2Id, requestQueue)
    ])
    console.log('帮派基本信息获取完成:', { faction1Info, faction2Info })
    
    // 获取成员列表
    updateProgress(++currentStep, totalSteps, '获取成员列表...')
    console.log('开始获取成员列表...')
    
    // 检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    const [faction1Members, faction2Members] = await Promise.all([
      getFactionMembers(form.faction1Id, requestQueue),
      getFactionMembers(form.faction2Id, requestQueue)
    ])
    console.log('成员列表获取完成:', {
      faction1MemberCount: getMemberCount(faction1Members),
      faction2MemberCount: getMemberCount(faction2Members)
    })
    
    // 获取RW数据
    updateProgress(++currentStep, totalSteps, '获取RW数据...')
    console.log('开始获取RW数据...')
    
    // 检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    const [faction1RankedWars, faction2RankedWars] = await Promise.all([
      getFactionRankedWars(form.faction1Id, requestQueue),
      getFactionRankedWars(form.faction2Id, requestQueue)
    ])
    console.log('RW数据获取完成:', {
      faction1RwCount: faction1RankedWars.length,
      faction2RwCount: faction2RankedWars.length
    })
    
    // 获取Chain数据
    updateProgress(++currentStep, totalSteps, '获取Chain数据...')
    console.log('开始获取Chain数据...')
    
    // 检查是否被取消
    if (abortController.value?.signal.aborted) {
      throw new Error('请求被取消')
    }
    
    const [faction1Chains, faction2Chains] = await Promise.all([
      getFactionChains(form.faction1Id, requestQueue, faction1RankedWars),
      getFactionChains(form.faction2Id, requestQueue, faction2RankedWars)
    ])
    console.log('Chain数据获取完成:', {
      faction1ChainCount: faction1Chains.length,
      faction2ChainCount: faction2Chains.length
    })
    
    // 重新计算总步骤数（包括所有成员的个人数据）
    const totalMembers = getMemberCount(faction1Members) + getMemberCount(faction2Members)
    totalSteps = 6 + totalMembers
    
    // 获取成员个人数据
    updateProgress(++currentStep, totalSteps, '获取成员个人数据...')
    console.log('开始获取成员个人数据...')
    
    const faction1PersonalStats = {}
    const faction2PersonalStats = {}
    
    // 准备所有需要获取的成员
    const allMembers = [
      ...Object.keys(faction1Members).map(id => ({ id, factionId: form.faction1Id, faction: 'faction1' })),
      ...Object.keys(faction2Members).map(id => ({ id, factionId: form.faction2Id, faction: 'faction2' }))
    ]
    
    console.log(`总共需要获取 ${allMembers.length} 个成员的数据，使用 ${apiKeys.length} 个API密钥`)
    
    // 实现真正的并发：每个API密钥同时处理一个成员
    let processedCount = 0
    const memberQueue = [...allMembers] // 复制队列
    
    // 创建并发工作器，每个API密钥一个
    const workers = apiKeys.map(async (apiKey, workerIndex) => {
      console.log(`工作器 ${workerIndex + 1} 开始工作，使用API密钥: ${apiKey.substring(0, 8)}...`)
      
      while (memberQueue.length > 0) {
        // 检查是否被取消
        if (abortController.value?.signal.aborted) {
          throw new Error('请求被取消')
        }
        
        // 从队列中取出一个成员
        const member = memberQueue.shift()
        if (!member) break
        
        try {
          console.log(`工作器 ${workerIndex + 1} 开始获取成员 ${member.id} 的数据`)
          
          // 直接使用API密钥发起请求，不通过队列
          const [profileData, personalStatsData] = await Promise.all([
            fetchApi(`/user/${member.id}`, apiKey),
            fetchApi(`/user/${member.id}/personalstats?cat=all`, apiKey)
          ])
          
          // 检查是否被取消
          if (abortController.value?.signal.aborted) {
            throw new Error('请求被取消')
          }
          
          // 合并数据
          const combinedData = {
            profile: profileData.profile || profileData,
            personalstats: personalStatsData.personalstats || personalStatsData,
            criminalrecord: personalStatsData.criminalrecord || (profileData.criminalrecord || {})
          }
          
          if (combinedData.personalstats) {
            // 存储到对应的帮派数据中
            if (member.faction === 'faction1') {
              faction1PersonalStats[member.id] = combinedData
            } else {
              faction2PersonalStats[member.id] = combinedData
            }
            
            // 缓存数据
            const cacheKey = getCacheKey('personalstats', member.id)
            setCachedData(cacheKey, combinedData)
            
            console.log(`工作器 ${workerIndex + 1} 成功获取成员 ${member.id} 的数据`)
          } else {
            console.warn(`工作器 ${workerIndex + 1} 获取成员 ${member.id} 数据为空`)
          }
          
        } catch (error) {
          if (error.message === '请求被取消') {
            throw error
          }
          console.error(`工作器 ${workerIndex + 1} 获取成员 ${member.id} 数据失败:`, error)
        }
        
        // 更新进度
        processedCount++
        currentStep++
        updateProgress(currentStep, totalSteps, `已获取 ${processedCount}/${allMembers.length} 个成员数据`)
        updateDetailedProgress(`members_all`, `所有成员数据`, processedCount, allMembers.length)
        
        // 每个请求后等待一小段时间，避免触发API限制
        await new Promise(resolve => setTimeout(resolve, 1200)) // 50次/分钟 = 1.2秒间隔
      }
      
      console.log(`工作器 ${workerIndex + 1} 完成工作`)
    })
    
    // 等待所有工作器完成
    await Promise.all(workers)
    
    console.log(`个人数据获取完成，成功获取 ${processedCount} 个成员的数据`)
    
    // 完成数据收集
    updateProgress(totalSteps, totalSteps, '数据获取完成！')
    
    // 进行帮派实力分析
    statusMessage.value = '正在分析帮派实力...'
    console.log('开始进行帮派实力分析...')
    
    const faction1Analysis = analyzeFactionStrength({
      name: faction1Info.name,
      members: faction1Members,
      personalStats: faction1PersonalStats,
      chains: faction1Chains
    })
    
    const faction2Analysis = analyzeFactionStrength({
      name: faction2Info.name,
      members: faction2Members,
      personalStats: faction2PersonalStats,
      chains: faction2Chains
    })
    
    // 预测PVP胜率
    const winRatePrediction = predictPVPWinRate(faction1Analysis, faction2Analysis)
    
    console.log('帮派实力分析完成:', { faction1Analysis, faction2Analysis, winRatePrediction })
    
    // 构建结果对象
    comparisonResult.value = {
      faction1: {
        info: faction1Info,
        name: faction1Info.name,
        members: faction1Members,
        personalStats: faction1PersonalStats,
        rankedWars: faction1RankedWars,
        chains: faction1Chains
      },
      faction2: {
        info: faction2Info,
        name: faction2Info.name,
        members: faction2Members,
        personalStats: faction2PersonalStats,
        rankedWars: faction2RankedWars,
        chains: faction2Chains
      },
      rwDataCount: faction1RankedWars.length + faction2RankedWars.length,
      chainDataCount: faction1Chains.length + faction2Chains.length,
      detailedRwCount: faction1RankedWars.filter(rw => rw.report).length + faction2RankedWars.filter(rw => rw.report).length,
      detailedChainCount: faction1Chains.filter(chain => chain.report).length + faction2Chains.filter(chain => chain.report).length,
      personalStatsCount: Object.values(faction1PersonalStats).filter(stats => stats).length + Object.values(faction2PersonalStats).filter(stats => stats).length,
      // 添加实力分析结果
      faction1Analysis,
      faction2Analysis,
      winRatePrediction
    }
    
    statusMessage.value = '所有数据获取完成！'
    statusType.value = 'success'
    
  } catch (error) {
    if (error.message === '请求被取消') {
      statusMessage.value = '数据获取已取消'
      statusType.value = 'warning'
    } else {
      console.error('数据获取失败:', error)
      statusMessage.value = `数据获取失败: ${error.message}`
      statusType.value = 'error'
    }
  }
}

// 开始对比分析
const startComparison = async () => {
  if (!canStartComparison.value) {
    ElMessage.error('请填入帮派ID和API密钥')
    return
  }
  
  // 验证帮派ID格式
  const faction1Id = form.faction1Id.trim()
  const faction2Id = form.faction2Id.trim()
  
  if (!/^\d+$/.test(faction1Id) || !/^\d+$/.test(faction2Id)) {
    ElMessage.error('帮派ID必须是数字')
    return
  }
  
  if (faction1Id === faction2Id) {
    ElMessage.error('两个帮派ID不能相同')
    return
  }
  
  loading.value = true
  statusMessage.value = '开始获取数据...'
  statusType.value = 'info'
  overallProgress.value = 0
  progressText.value = ''
  detailedProgress.value = []
  comparisonResult.value = null
  
  // 更新API密钥池
  apiKeyPool.value = getValidApiKeys()
  
  console.log(`开始帮派对比分析: ${faction1Id} vs ${faction2Id}`)
  console.log(`使用 ${apiKeyPool.value.length} 个API密钥`)
  
  await fetchAllData()
  
  loading.value = false
}

// 停止分析
const stopComparison = () => {
  console.log('用户请求停止分析')
  
  if (abortController.value) {
    abortController.value.abort()
  }
  
  // 立即停止loading状态
  loading.value = false
  
  // 重置进度相关状态
  overallProgress.value = 0
  progressText.value = ''
  detailedProgress.value = []
  
  // 设置取消状态消息
  statusMessage.value = '分析已取消'
  statusType.value = 'warning'
  
  console.log('分析已停止')
}

// 组件挂载时初始化
onMounted(() => {
  updateCacheInfo()
})
</script>

<style scoped>
.faction-comparison-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.api-config-card {
  border: 1px solid #e4e7ed;
}

.api-help-text {
  margin-top: 5px;
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
  margin-bottom: 8px;
  color: #303133;
}

.progress-text {
  margin-top: 5px;
  font-size: 14px;
  color: #606266;
}

.detailed-progress {
  margin-top: 15px;
}

.progress-detail-item {
  margin-bottom: 10px;
}

.progress-detail-label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 5px;
  color: #606266;
}

.progress-detail-text {
  margin-top: 3px;
  font-size: 12px;
  color: #909399;
}

.cache-info-card {
  border: 1px solid #e4e7ed;
}

.cache-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-card {
  border: 1px solid #e4e7ed;
}

.result-summary {
  font-size: 14px;
  line-height: 1.6;
}

.result-summary ul {
  margin: 10px 0;
  padding-left: 20px;
}

.result-summary li {
  margin: 5px 0;
}

.win-rate-card {
  border: 1px solid #e4e7ed;
}

.win-rate-display {
  padding: 20px;
}

.faction-win-rate {
  text-align: center;
}

.win-percentage {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 10px;
}

.analysis-text {
  margin-top: 20px;
}

.strength-analysis-card {
  border: 1px solid #e4e7ed;
}

.overall-comparison {
  margin-bottom: 20px;
}

.member-analysis {
  margin-top: 20px;
}

.member-count-info {
  margin-bottom: 10px;
  font-size: 14px;
  color: #606266;
}

.peak-hours {
  color: #67c23a;
}

.cache-data-content {
  max-height: 600px;
  overflow-y: auto;
}

.json-content {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
}
</style> 