<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>帮派攻击记录抓取</h2>
      </div>
    </template>
    <p>抓取指定时间段内的帮派攻击记录，导出xlsx查看。</p>

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
        <el-table-column prop="direction" label="方向" width="90" />
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
// FactionAttacksGrabber.vue
// 作用：按用户选择的时间范围抓取 Torn 帮派攻击记录并导出 Excel。
// 时间处理约定：
// - Torn API/记录中的 started/ended 时间戳：统一视为 UTC 的 epoch 秒（不做任何时区数值偏移）。
// - 界面/Excel 展示时间统一按 TCT (UTC+0) 格式化。
// - date-picker 输出的是“本地时区下选中时刻”的 epoch 秒；本页面约定用户输入的是 TCT 字面量时间，因此需要把本地 epoch 映射为“同字面量在 UTC 下”的 epoch。
// 抓取策略（attacks）：
// - 使用 `/v2/faction/attacks?limit=100&sort=DESC&to=<currentTo>&key=<key>` 倒序抓取。
// - 若返回条数 == 100，则以本批 started 的“中位数”作为新的 to 继续请求；直到返回条数 < 100，认为已抓全（在当前时间窗内）。
// - 为减少重复/便于区分，分别使用 `filters=incoming` 与 `filters=outgoing` 抓取帮派“收到/发出”的攻击记录，并合并去重。
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

const formatTimeInZone = (timestamp, timeZone, locale) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString(locale, { timeZone })
}

const formatTime = (timestamp) => {
  return formatTimeInZone(timestamp, 'UTC', 'en-GB')
}

// 把 date-picker 产出的 epoch（按本地时区解释的“选中时刻”）转换为：
// “同样字面量时间”在 UTC (TCT) 对应的 epoch 秒
// 公式：utcEpoch = localEpoch - (localOffsetMinutes - 0) * 60
// 其中 offsetMinutes = Date.getTimezoneOffset() = UTC - LocalTZ（单位分钟）
const convertPickerEpochToUtcEpoch = (pickerEpochSeconds) => {
  const localOffsetMinutes = new Date().getTimezoneOffset()
  return pickerEpochSeconds - localOffsetMinutes * 60
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
  const pickerStart = parseInt(form.dateRange[0])
  const pickerEnd = parseInt(form.dateRange[1])

  // 将 date-picker 的“本地字面量时间”映射到 TCT (UTC) 的 epoch
  let startTime = convertPickerEpochToUtcEpoch(pickerStart)
  let endTime = convertPickerEpochToUtcEpoch(pickerEnd)

  // 便于排查：同时打印输入与换算后的 epoch
  console.log(
    `PickerStart: ${pickerStart}, PickerEnd: ${pickerEnd}, Start: ${startTime}, End: ${endTime}, LocalOffsetMinutes: ${new Date().getTimezoneOffset()}`
  )

  try {
    // 合并 incoming/outgoing 并按 id 去重
    const attacksById = new Map()
    const markDirection = (existing, dir) => {
      if (!existing.direction) {
        existing.direction = dir
        return
      }
      if (existing.direction === dir) return
      const parts = new Set(existing.direction.split(',').map(s => s.trim()).filter(Boolean))
      parts.add(dir)
      existing.direction = Array.from(parts).sort().join(',')
    }

    const fetchWithFilter = async (filter) => {
      let currentTo = endTime
      let guard = 0

      while (true) {
        guard++
        if (guard > 5000) {
          throw new Error(`抓取保护阀触发：${filter} 迭代次数过多，可能陷入死循环`)
        }

        // 避免 API 速率限制，每分钟最多60次，即每次间隔至少1秒
        await sleep(1000)

        progress.value = `正在抓取(${filter}) ${formatTime(currentTo)} 之前的记录... (当前合并总数 ${attacksById.size} 条)`

        // attacks 一次最多 100 条，按 DESC 返回 <= to 的数据
        const url = `https://api.torn.com/v2/faction/attacks?filters=${filter}&limit=100&sort=DESC&to=${currentTo}&key=${props.apiKey}`
        const response = await axios.get(url)

        if (!response.data || !response.data.attacks) {
          throw new Error('API 返回格式错误')
        }

        const batch = response.data.attacks
        if (batch.length === 0) break

        for (const attack of batch) {
          // 过滤时间窗
          if (attack.started < startTime) continue
          if (attack.started > endTime) continue

          const existing = attacksById.get(attack.id)
          if (existing) {
            markDirection(existing, filter)
            continue
          }

          attack.direction = filter
          attacksById.set(attack.id, attack)
        }

        // 结束条件：返回条数不足 100，视为已抓全
        if (batch.length < 100) break

        // 以 started 的中位数作为新的 to（batch 已按 started DESC 接近 to 排序）
        const medianIndex = Math.floor(batch.length / 2)
        let newTo = batch[medianIndex]?.started
        if (!newTo || Number.isNaN(newTo)) {
          newTo = batch[batch.length - 1]?.started ? batch[batch.length - 1].started - 1 : currentTo - 1
        }

        // 防止不下降导致死循环
        if (newTo >= currentTo) {
          newTo = currentTo - 1
        }
        currentTo = newTo

        if (currentTo < startTime) break
      }
    }

    // 分别抓取 incoming / outgoing 再合并
    await fetchWithFilter('incoming')
    await fetchWithFilter('outgoing')

    // 写回数组（按 started DESC 排序）
    attacks.value = Array.from(attacksById.values()).sort((a, b) => (b.started || 0) - (a.started || 0))

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

  // 准备数据
  const data = attacks.value.map(a => ({
    'Attack Link': {
      t: 's', 
      v: 'Link', 
      l: { Target: `https://www.torn.com/loader.php?sid=attackLog&ID=${a.code}` }
    },
    'Attack ID': a.id,
    'Code': a.code,
    'Direction': a.direction || '',
    // 真实时间戳：UTC epoch 秒（不要做 +8 的数值偏移）
    'Started Timestamp': a.started,
    'Ended Timestamp': a.ended,
    // 保持向后兼容：保留旧列名 Started/Ended
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
    {wch: 12}, // Direction
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

