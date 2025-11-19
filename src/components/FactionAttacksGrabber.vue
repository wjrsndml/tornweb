<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>帮派攻击记录抓取</h2>
      </div>
    </template>
    <p>抓取指定时间段内的帮派攻击记录，导出xlsx查看（保存的攻击记录时间为北京时间）。</p>

    <el-form :model="form" label-width="120px">
      <el-form-item label="时间范围">
        <el-date-picker
          v-model="form.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="X"
          :default-time="defaultTime"
        />
      </el-form-item>
      <el-form-item label="时间模式">
        <el-radio-group v-model="form.timeMode">
          <el-radio label="TCT">TCT (UTC+0)</el-radio>
          <el-radio label="BJ">北京时间 (UTC+8)</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="详细模式">
        <el-checkbox v-model="form.fetchDetails">抓取详细攻击记录 (速度较慢)</el-checkbox>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="startFetching" :loading="loading" :disabled="!canFetch">
          开始抓取
        </el-button>
        <el-button type="success" @click="exportXlsx" :disabled="attacks.length === 0 || loading">
          导出 Excel ({{ attacks.length }}条)
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 进度显示 -->
    <div v-if="loading || progress" class="progress-section">
      <el-progress 
        v-if="loading"
        :percentage="fetchingDetails ? detailedProgress : 100" 
        :status="fetchingDetails ? '' : 'active'" 
        :indeterminate="!fetchingDetails" 
        :duration="3" 
      />
      <p class="status-text">{{ progress }}</p>
      <p v-if="fetchingDetails" class="eta-text">预计剩余时间: {{ eta }}</p>
    </div>

    <!-- 结果预览 (只显示前10条) -->
    <div v-if="attacks.length > 0" class="result-preview">
      <h3>结果预览 (共 {{ attacks.length }} 条)</h3>
      <el-table :data="attacks.slice(0, 10)" stripe style="width: 100%" size="small">
        <el-table-column prop="started" label="开始时间" width="160">
          <template #default="scope">
            {{ formatTime(scope.row.started) }}
          </template>
        </el-table-column>
        <el-table-column prop="attacker.name" label="攻击者" width="150" />
        <el-table-column prop="defender.name" label="防守者" width="150" />
        <el-table-column prop="result" label="结果" width="100" />
        <el-table-column prop="respect_gain" label="Respect" width="80" />
        <el-table-column prop="chain" label="Chain" width="80" />
      </el-table>
      <p v-if="attacks.length > 10" class="more-text">... 还有 {{ attacks.length - 10 }} 条记录，请导出查看完整数据</p>
    </div>

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
import * as XLSX from 'xlsx'

const props = defineProps({
  apiKey: {
    type: String,
    required: true
  }
})

const form = reactive({
  dateRange: [], // [startTimestamp, endTimestamp] in seconds (string or number)
  timeMode: 'TCT',
  fetchDetails: false
})

const defaultTime = [
  new Date(2000, 1, 1, 0, 0, 0),
  new Date(2000, 1, 1, 23, 59, 59),
]

const loading = ref(false)
const fetchingDetails = ref(false)
const detailedProgress = ref(0)
const detailedTotal = ref(0)
const detailedCurrent = ref(0)
const eta = ref('')
const progress = ref('')
const error = ref(null)
const attacks = ref([])
const visitedIds = new Set()

const canFetch = computed(() => {
  return props.apiKey && form.dateRange && form.dateRange.length === 2
})

const formatTime = (timestamp) => {
  const date = new Date(timestamp * 1000)
  if (form.timeMode === 'TCT') {
    return date.toLocaleString('en-GB', { timeZone: 'UTC' })
  } else {
    return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
  }
}

// 计算北京时间（UTC+8）的时间戳
const getBeijingTimestamp = (timestamp) => {
  // 传入的时间戳是 UTC 的秒数
  // 如果需要转换为北京时间的时间戳（比如显示在 Excel 的 Timestamp 列），
  // 通常我们直接保留原始 UTC 时间戳，因为 Excel 或其他工具会根据用户时区处理。
  // 但如果用户希望看到的是北京时间对应的数值（即 +8 小时后的秒数），可以加上 8*3600。
  // 不过标准做法是存储 UTC 时间戳，显示时格式化。
  // 这里为了满足“存的时间也是11:00到15:00”的需求（看起来像是时区偏移被应用到了时间戳上或者请求参数上）
  // 如果是请求参数问题：
  // Element Plus 的 date-picker 返回的时间戳是基于浏览器本地时区的。
  // 如果用户在 UTC+8 环境下选择了 19:00，得到的 timestamp 就是 19:00 UTC+8 对应的 UTC 时间戳（即 11:00 UTC）。
  // API 期望的是 UTC 时间戳，所以 date-picker 的行为是正确的（传给 API 11:00 UTC）。
  // 但是，如果用户选择了 TCT 模式，意味着他输入的 19:00 是 TCT (UTC+0) 的 19:00。
  // 而 date-picker 如果运行在 UTC+8 环境，会认为用户输入的是 UTC+8 的 19:00。
  
  return timestamp
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const formatDuration = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h}小时 ${m}分 ${s}秒`
}

const startFetching = async () => {
  if (!canFetch.value) return
  
  loading.value = true
  error.value = null
  progress.value = '准备开始...'
  attacks.value = []
  visitedIds.clear()
  fetchingDetails.value = false
  detailedProgress.value = 0
  eta.value = ''

  // Element Plus date picker value-format="X" returns seconds as string/number
  // Ensure they are integers
  let startTime = parseInt(form.dateRange[0])
  let endTime = parseInt(form.dateRange[1])

  // 通用时区处理逻辑：
  // 1. 获取本地时区偏移（分钟），例如 UTC+8 返回 -480，UTC+0 返回 0
  const offsetMinutes = new Date().getTimezoneOffset()
  
  // 2. 第一步：将 date-picker 返回的"本地时间戳"还原为"用户输入字面量对应的 UTC 时间戳"
  // 也就是假设用户输入的是 TCT (UTC+0) 时间
  // 公式：时间戳 - (UTC - Local) = 时间戳 + (Local - UTC)
  // 例如：在 UTC+8 输入 19:00。
  // date-picker 得到 UTC 11:00。
  // offsetMinutes 是 -480 (-8小时)。
  // 11:00 - (-8:00) = 19:00。正确。
  startTime -= offsetMinutes * 60
  endTime -= offsetMinutes * 60

  // 3. 第二步：如果用户选择的是北京时间，则需要再减去 8 小时
  // 因为北京时间 19:00 等于 TCT 11:00
  if (form.timeMode === 'BJ') {
    startTime -= 8 * 3600
    endTime -= 8 * 3600
  }

  console.log(`Start: ${startTime}, End: ${endTime}, Mode: ${form.timeMode}, LocalOffset: ${offsetMinutes}`)

  // 策略：参考 fangfang.py，使用时间窗口滑动。
  // 但由于 API 支持 sort=DESC，我们从 endTime 开始往回抓取直到 startTime。
  // 这样可以确保获取到最新的数据。
  
  let currentTo = endTime
  let hasMore = true
  let totalFetched = 0
  let consecutiveEmptyBatches = 0

  try {
    while (hasMore) {
      // 避免 API 速率限制，每分钟最多60次，即每次间隔至少1秒
      await sleep(1000) 

      progress.value = `正在抓取 ${formatTime(currentTo)} 之前的记录... (已获取 ${totalFetched} 条)`

      // 构造请求
      // 注意：V2 API 的 to 参数通常表示 "直到这个时间点"。
      // 如果我们用 sort=DESC，返回的是 <= to 的记录。
      const url = `https://api.torn.com/v2/faction/attacks?limit=100&sort=DESC&to=${currentTo}&key=${props.apiKey}`
      
      const response = await axios.get(url)
      
      if (!response.data || !response.data.attacks) {
        throw new Error('API 返回格式错误')
      }

      const batch = response.data.attacks
      
      if (batch.length === 0) {
        hasMore = false
        break
      }

      let newItemsInBatch = 0
      let minTimestampInBatch = currentTo

      for (const attack of batch) {
        // 过滤掉时间范围之外的 (早于 startTime)
        if (attack.started < startTime) {
          hasMore = false // 已经超出了开始时间，不需要再往后翻了
          continue 
        }

        // 记录本批次最小时间戳，用于下一次翻页
        if (attack.started < minTimestampInBatch) {
          minTimestampInBatch = attack.started
        }

        // 去重
        if (!visitedIds.has(attack.id)) {
          visitedIds.add(attack.id)
          attacks.value.push(attack)
          newItemsInBatch++
        }
      }

      totalFetched = attacks.value.length

      // 更新 currentTo
      // 如果本批次所有数据的 timestamp 都 >= currentTo (且我们已经处理过它们)，
      // 且没有更早的数据，我们需要强制把 currentTo 往前推一点，防止死循环。
      // 但通常 sort=DESC 会返回更早的数据。
      // 如果 minTimestampInBatch == currentTo 且 batch 满了，说明这一秒有很多数据。
      // 我们下一次请求 to=minTimestampInBatch，API 会返回 <= 这个时间的数据。
      // 由于我们有 visitedIds 去重，所以重复获取没关系。
      
      // 如果本批次没有新增数据（全是重复的），且我们还没超出时间范围
      if (newItemsInBatch === 0) {
        consecutiveEmptyBatches++
        // 强制往前推1秒，避免死循环
        currentTo = minTimestampInBatch - 1
      } else {
        consecutiveEmptyBatches = 0
        currentTo = minTimestampInBatch
      }

      // 安全阀：如果连续多次没有新数据，或者 currentTo 已经小于 startTime
      if (consecutiveEmptyBatches > 5 || currentTo < startTime) {
        hasMore = false
      }
    }

    progress.value = `抓取完成！共找到 ${attacks.value.length} 条记录。`

    if (form.fetchDetails && attacks.value.length > 0) {
      await fetchDetailedLogs()
    }

  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.error?.error || e.message || '抓取失败'
    progress.value = '发生错误'
  } finally {
    loading.value = false
    fetchingDetails.value = false
  }
}

const fetchDetailedLogs = async () => {
  fetchingDetails.value = true
  detailedTotal.value = attacks.value.length
  detailedCurrent.value = 0
  progress.value = '正在抓取详细攻击记录...'
  
  for (let i = 0; i < attacks.value.length; i++) {
    const attack = attacks.value[i]
    let retryCount = 0
    const maxRetries = 3
    let success = false
    
    while (!success && retryCount <= maxRetries) {
      try {
        // 避免 API 速率限制，每分钟最多60次
        await sleep(1100) 
        
        const url = `https://api.torn.com/v2/torn/attacklog?log=${attack.code}&offset=0&striptags=true&key=${props.apiKey}`
        const response = await axios.get(url)
        
        if (response.data && response.data.attacklog) {
          attack.details = response.data.attacklog
          success = true
        } else {
          // 某些情况下 API 可能返回成功但没有数据，视作成功或根据业务需求处理
          // 这里假设没有 attacklog 字段也是一种数据返回
          attack.details = { error: 'No data returned from API' }
          success = true
        }
      } catch (e) {
        const errorMessage = e.response?.data?.error?.error || e.message || 'Unknown error'
        console.error(`Failed to fetch details for ${attack.code} (Attempt ${retryCount + 1}/${maxRetries + 1}):`, errorMessage)
        
        if (retryCount < maxRetries) {
          const waitTime = 5000
          progress.value = `请求失败: ${errorMessage}。正在等待 ${waitTime/1000} 秒后重试 (${retryCount + 1}/${maxRetries})...`
          await sleep(waitTime)
          retryCount++
        } else {
          attack.details = { error: `Failed after ${maxRetries} retries: ${errorMessage}` }
          // 最终失败，让外层循环继续
          break
        }
      }
    }
    
    detailedCurrent.value++
    detailedProgress.value = Math.floor((detailedCurrent.value / detailedTotal.value) * 100)
    
    // Calculate ETA
    const remaining = detailedTotal.value - detailedCurrent.value
    const secondsLeft = remaining * 1.1
    eta.value = formatDuration(secondsLeft)
    progress.value = `正在抓取详细记录 (${detailedCurrent.value}/${detailedTotal.value})`
  }
}

const exportXlsx = () => {
  if (attacks.value.length === 0) return

  // 计算北京时间（UTC+8）的时间戳
  const getBeijingTimestamp = (timestamp) => {
    // 将 UTC 时间戳转换为北京时间对应的数值（即 +8 小时）
    return timestamp + 8 * 3600
  }

  // 准备数据
  const data = attacks.value.map(a => ({
    'Attack Link': {
      t: 's', 
      v: 'Link', 
      l: { Target: `https://www.torn.com/loader.php?sid=attackLog&ID=${a.code}` }
    },
    'Attack ID': a.id,
    'Code': a.code,
    'Started Timestamp': getBeijingTimestamp(a.started),
    'Ended Timestamp': getBeijingTimestamp(a.ended),
    'Started': formatTime(a.started),
    'Ended': formatTime(a.ended),
    'Result': a.result,
    'Attacker ID': a.attacker?.id || '',
    'Attacker Name': a.attacker?.name || '',
    'Attacker Faction': a.attacker?.faction?.name || '',
    'Defender ID': a.defender?.id || '',
    'Defender Name': a.defender?.name || '',
    'Defender Faction': a.defender?.faction?.name || '',
    'Respect Gain': a.respect_gain,
    'Chain': a.chain,
    'Fair Fight': a.modifiers?.fair_fight || '',
    'War': a.modifiers?.war || '',
    'Detailed Log': a.details ? JSON.stringify(a.details) : ''
  }))

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  
  // 设置列宽
  const wscols = [
    {wch: 10}, // Attack Link
    {wch: 12}, // Attack ID
    {wch: 35}, // Code
    {wch: 15}, // Started Timestamp
    {wch: 15}, // Ended Timestamp
    {wch: 20}, // Started
    {wch: 20}, // Ended
    {wch: 10}, // Result
    {wch: 10}, // Attacker ID
    {wch: 20}, // Attacker Name
    {wch: 25}, // Attacker Faction
    {wch: 10}, // Defender ID
    {wch: 20}, // Defender Name
    {wch: 25}, // Defender Faction
    {wch: 10}, // Respect
    {wch: 8},  // Chain
    {wch: 10}, // Fair Fight
    {wch: 8},  // War
    {wch: 50}  // Detailed Log
  ]
  ws['!cols'] = wscols

  XLSX.utils.book_append_sheet(wb, ws, 'Attacks')

  // 导出文件
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  XLSX.writeFile(wb, `faction_attacks_${timestamp}.xlsx`)
}
</script>

<style scoped>
.progress-section {
  margin: 20px 0;
}
.status-text {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}
.result-preview {
  margin-top: 20px;
}
.more-text {
  text-align: center;
  color: #909399;
  margin-top: 10px;
  font-size: 13px;
}
</style>

