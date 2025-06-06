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
          <el-button size="small" @click="clearCache">清空缓存</el-button>
        </div>
      </template>
      <el-table :data="cacheInfo" size="small">
        <el-table-column prop="type" label="数据类型" width="150" />
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="lastUpdated" label="最后更新时间" width="180" />
        <el-table-column prop="dataSize" label="数据大小" width="120" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="removeCacheItem(row.key)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
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
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = 'https://api.torn.com/v2'
const RATE_LIMIT_PER_MINUTE = 50
const RATE_LIMIT_INTERVAL = 60000 // 1分钟

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

// 辅助函数
const getMemberCount = (members) => {
  if (!members) return 0
  if (Array.isArray(members)) return members.length
  return Object.keys(members).length
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
    const data = await requestQueue.addRequest(async (apiKey) => {
      return await fetchApi(`/user/${memberId}/personalstats?cat=all`, apiKey)
    })
    
    // 根据实际数据结构提取个人统计信息
    const personalStats = data.personalstats || data
    if (!personalStats) {
      console.warn(`成员 ${memberId} 个人数据为空`)
      return null
    }
    
    setCachedData(cacheKey, personalStats)
    return personalStats
  } catch (error) {
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
      return await fetchApi(`/faction/${factionId}/rankedwars?limit=100`, apiKey)
    })
    
    // 提取RW数据
    const allRankedWars = data.rankedwars || data.rankedwarreports || data || []
    console.log(`帮派 ${factionId} 获取到 ${Object.keys(allRankedWars).length} 条RW记录`)
    
    // 2. 过滤四个月内的RW
    const recentRankedWars = {}
    const currentTime = Math.floor(Date.now() / 1000)
    
    for (const [warId, war] of Object.entries(allRankedWars)) {
      if (war.start >= fourMonthsAgo) {
        recentRankedWars[warId] = war
      }
    }
    
    console.log(`帮派 ${factionId} 过滤后剩余 ${Object.keys(recentRankedWars).length} 条最近四个月的RW记录`)
    
    // 3. 获取每个RW的详细报告
    const detailedRankedWars = []
    const warIds = Object.keys(recentRankedWars)
    
    updateDetailedProgress(`rw_${factionId}`, `帮派 ${factionId} RW详细报告`, 0, warIds.length, '')
    
    for (let i = 0; i < warIds.length; i++) {
      const warId = warIds[i]
      statusMessage.value = `正在获取帮派 ${factionId} 的RW详细报告 ${i + 1}/${warIds.length}...`
      updateDetailedProgress(`rw_${factionId}`, `帮派 ${factionId} RW详细报告`, i + 1, warIds.length, '')
      
      try {
        const reportData = await requestQueue.addRequest(async (apiKey) => {
          return await fetchApi(`/faction/${warId}/rankedwarreport`, apiKey)
        })
        
        if (reportData.rankedwarreport) {
          detailedRankedWars.push({
            id: warId,
            basicInfo: recentRankedWars[warId],
            report: reportData.rankedwarreport
          })
        }
      } catch (reportError) {
        console.error(`获取RW ${warId} 详细报告失败:`, reportError)
        // 如果详细报告获取失败，仍然保存基础信息
        detailedRankedWars.push({
          id: warId,
          basicInfo: recentRankedWars[warId],
          report: null
        })
      }
      
      // 添加延迟避免触发API频率限制
      if (i < warIds.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
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
      return await fetchApi(`/faction/${factionId}/chains?from=${fourMonthsAgo}&limit=100`, apiKey)
    })
    
    const allChains = data.chains || data || []
    console.log(`帮派 ${factionId} 获取到 ${Object.keys(allChains).length} 条Chain记录`)
    
    // 3. 过滤RW时间范围内的Chain
    const rwChains = {}
    for (const [chainId, chain] of Object.entries(allChains)) {
      // 检查Chain是否在任何RW时间范围内
      for (const timeRange of timeRanges) {
        const chainStart = chain.start
        const chainEnd = chain.end
        
        // 判断Chain时间是否与RW时间重叠
        if ((chainStart >= timeRange.start && chainStart <= timeRange.end) ||
            (chainEnd >= timeRange.start && chainEnd <= timeRange.end) ||
            (chainStart <= timeRange.start && chainEnd >= timeRange.end)) {
          
          if (!rwChains[chainId]) {
            rwChains[chainId] = {
              ...chain,
              relatedWars: []
            }
          }
          rwChains[chainId].relatedWars.push(timeRange.warId)
        }
      }
    }
    
    console.log(`帮派 ${factionId} 过滤后剩余 ${Object.keys(rwChains).length} 条RW相关的Chain记录`)
    
    // 4. 获取每个Chain的详细报告
    const detailedChains = []
    const chainIds = Object.keys(rwChains)
    
    updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, 0, chainIds.length, '')
    
    for (let i = 0; i < chainIds.length; i++) {
      const chainId = chainIds[i]
      statusMessage.value = `正在获取帮派 ${factionId} 的Chain详细报告 ${i + 1}/${chainIds.length}...`
      updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, i + 1, chainIds.length, '')
      
      try {
        const reportData = await requestQueue.addRequest(async (apiKey) => {
          return await fetchApi(`/faction/${chainId}/chainreport`, apiKey)
        })
        
        if (reportData.chainreport) {
          detailedChains.push({
            id: chainId,
            basicInfo: rwChains[chainId],
            report: reportData.chainreport,
            relatedWars: rwChains[chainId].relatedWars
          })
        }
      } catch (reportError) {
        console.error(`获取Chain ${chainId} 详细报告失败:`, reportError)
        // 如果详细报告获取失败，仍然保存基础信息
        detailedChains.push({
          id: chainId,
          basicInfo: rwChains[chainId],
          report: null,
          relatedWars: rwChains[chainId].relatedWars
        })
      }
      
      // 添加延迟避免触发API频率限制
      if (i < chainIds.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
    
    updateDetailedProgress(`chains_${factionId}`, `帮派 ${factionId} Chain详细报告`, chainIds.length, chainIds.length, 'success')
    
    setCachedData(cacheKey, detailedChains)
    return detailedChains
  } catch (error) {
    console.error(`获取帮派 ${factionId} Chain数据失败:`, error)
    return []
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
    const [faction1Info, faction2Info] = await Promise.all([
      getFactionInfo(form.faction1Id, requestQueue),
      getFactionInfo(form.faction2Id, requestQueue)
    ])
    console.log('帮派基本信息获取完成:', { faction1Info, faction2Info })
    
    // 获取成员列表
    updateProgress(++currentStep, totalSteps, '获取成员列表...')
    console.log('开始获取成员列表...')
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
    
    // 并行获取所有成员的个人数据
    const memberPromises = []
    
    // 帮派1成员数据
    Object.keys(faction1Members).forEach((memberId, index) => {
      memberPromises.push(
        getMemberPersonalStats(memberId, requestQueue, index + 1, getMemberCount(faction1Members), form.faction1Id)
          .then(stats => {
            faction1PersonalStats[memberId] = stats
            currentStep++
            updateProgress(currentStep, totalSteps, `获取成员 ${memberId} 个人数据...`)
          })
      )
    })
    
    // 帮派2成员数据
    Object.keys(faction2Members).forEach((memberId, index) => {
      memberPromises.push(
        getMemberPersonalStats(memberId, requestQueue, index + 1, getMemberCount(faction2Members), form.faction2Id)
          .then(stats => {
            faction2PersonalStats[memberId] = stats
            currentStep++
            updateProgress(currentStep, totalSteps, `获取成员 ${memberId} 个人数据...`)
          })
      )
    })
    
    await Promise.all(memberPromises)
    
    // 完成数据收集
    updateProgress(totalSteps, totalSteps, '数据获取完成！')
    
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
      personalStatsCount: Object.values(faction1PersonalStats).filter(stats => stats).length + Object.values(faction2PersonalStats).filter(stats => stats).length
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
  if (abortController.value) {
    abortController.value.abort()
  }
  loading.value = false
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
</style> 