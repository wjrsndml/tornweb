<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>Chain 历史搜索器</h2>
      </div>
    </template>
    <p>输入帮派 ID 和 Chain 长度，从最新的 Chain 往回翻页查找最近若干年内所有长度大于等于该数值的 Chain，并给出报告链接。</p>

    <el-form :model="form" label-width="140px">
      <el-form-item label="帮派 ID">
        <el-input
          v-model="form.factionId"
          placeholder="请输入帮派 ID，例如: 9361"
          style="max-width: 300px"
        />
      </el-form-item>
      <el-form-item label="Chain 长度 ≥">
        <el-input-number
          v-model="form.minHits"
          :min="1"
          :step="1000"
          step-strictly
          style="max-width: 300px"
        />
      </el-form-item>
      <el-form-item label="回溯年数">
        <el-input-number
          v-model="form.years"
          :min="1"
          :max="10"
          :step="1"
          step-strictly
          style="max-width: 300px"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="startSearch"
          :loading="loading"
        >
          开始搜索
        </el-button>
        <el-button @click="stopSearch" :disabled="!loading">停止</el-button>
      </el-form-item>
    </el-form>

    <!-- 进度显示 -->
    <div v-if="loading || progressText" class="progress-section">
      <el-progress
        v-if="loading"
        :percentage="100"
        status="active"
        :indeterminate="true"
        :duration="3"
        :stroke-width="15"
      />
      <p class="status-text">{{ progressText }}</p>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchDone" class="result-section">
      <el-alert :type="results.length > 0 ? 'success' : 'info'" :closable="false">
        <template #title>
          <template v-if="factionName">{{ factionName }} (ID: {{ form.factionId }}) — </template>
          最近 {{ form.years }} 年内共找到 <b>{{ results.length }}</b> 条长度 ≥ {{ form.minHits }} 的 Chain
          （已扫描 {{ scannedCount }} 条 Chain 记录）
        </template>
      </el-alert>

      <div v-if="results.length > 0" class="result-actions">
        <el-button type="success" size="small" @click="copyAllLinks">复制全部链接</el-button>
        <el-button type="primary" size="small" @click="exportXlsx">导出 Excel</el-button>
      </div>

      <el-table v-if="results.length > 0" :data="results" stripe style="width: 100%" size="small">
        <el-table-column label="#" width="60">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>
        <el-table-column label="Chain ID" width="140">
          <template #default="{ row }">
            <el-link
              type="primary"
              :href="chainReportUrl(row.id)"
              target="_blank"
              :underline="false"
            >
              {{ row.id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="chain" label="Hits" width="100" sortable />
        <el-table-column label="Respect" width="120" sortable :sort-method="(a, b) => a.respect - b.respect">
          <template #default="{ row }">{{ row.respect.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="开始时间 (TCT)" width="180">
          <template #default="{ row }">{{ formatTimestamp(row.start) }}</template>
        </el-table-column>
        <el-table-column label="结束时间 (TCT)" width="180">
          <template #default="{ row }">{{ formatTimestamp(row.end) }}</template>
        </el-table-column>
        <el-table-column label="持续时间" min-width="130">
          <template #default="{ row }">{{ formatDuration(row.end - row.start) }}</template>
        </el-table-column>
        <el-table-column label="报告链接" min-width="220">
          <template #default="{ row }">
            <el-link
              type="primary"
              :href="chainReportUrl(row.id)"
              target="_blank"
              :underline="false"
              style="font-size: 13px;"
            >
              <el-icon style="margin-right: 5px;"><Link /></el-icon>
              查看完整 Chain 报告
            </el-link>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      style="margin-top: 20px"
    />

    <el-alert
      title="注意事项"
      type="warning"
      :closable="false"
      style="margin-top: 20px"
    >
      <template #default>
        <p>从最新的 Chain 开始往回翻页，直到 Chain 结束时间早于回溯范围为止，因此活跃帮派可能需要抓取较多页（每秒 1 次请求），请耐心等待。可随时点击“停止”结束搜索，已找到的结果会保留。</p>
      </template>
    </el-alert>
  </el-card>
</template>

<script setup>
// ChainHistorySearcher.vue
// 作用：输入帮派 ID 与 Chain 长度阈值，从最新 Chain 倒序翻页回溯指定年数，
//       找出所有长度 >= 阈值的 Chain 并输出 Torn 报告链接。
// 抓取策略：
// - 使用 `/v2/faction/{id}/chains?limit=100&sort=DESC&to=<ts>`（新版摘要接口，单条含 {id, chain, respect, start, end}）。
// - 实测该接口 `_metadata.links.next` 恒为 null，无法用它翻页；正确做法是不断把 `to` 时间戳前移：
//   每页结束后取本页最早的 end，令 to = 该值 - 1，继续抓更早的一页。
// - 注意：`to` 实际按 chain 的开始时间过滤，翻页时会重复返回上一页的边界 chain，因此按 chain id 去重；
//   同时保证 to 每轮严格递减，防止同秒结束的 chain 造成死循环。
// - 停止条件：本页所有 Chain 的 end 均早于回溯下限 / 返回为空 / 触发页数保护阀 / 用户手动停止。
import { ref, reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { createRateLimiter } from '../utils/requestRateLimiter'

const props = defineProps({
  apiKey: {
    type: String,
    default: ''
  }
})

const API_BASE_URL = 'https://api.torn.com/v2'
// 翻页保护阀：单次搜索最多抓取的页数（每页 100 条）
const MAX_PAGES = 1000

const form = reactive({
  factionId: '',
  minHits: 10000,
  years: 5
})

const loading = ref(false)
const stopRequested = ref(false)
const progressText = ref('')
const errorMessage = ref('')
const searchDone = ref(false)
const results = ref([])
const scannedCount = ref(0)
const factionName = ref('')

const rateLimiter = createRateLimiter(1000)

const chainReportUrl = (chainId) => `https://www.torn.com/war.php?step=chainreport&chainID=${chainId}`

const fetchApi = async (endpoint) => {
  let url = `${API_BASE_URL}${endpoint}`
  url += url.includes('?') ? `&key=${props.apiKey}` : `?key=${props.apiKey}`

  const response = await axios.get(url)
  if (response.data && response.data.error) {
    throw new Error(`Torn API 错误: ${response.data.error.error} (代码: ${response.data.error.code})`)
  }
  return response.data
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A'
  return new Date(timestamp * 1000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
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

  const parts = []
  if (d > 0) parts.push(d + '天')
  if (h > 0) parts.push(h + '小时')
  if (m > 0) parts.push(m + '分钟')
  if (s > 0 || parts.length === 0) parts.push(s + '秒')
  return parts.join(' ')
}

const stopSearch = () => {
  if (!loading.value) return
  stopRequested.value = true
  progressText.value = '正在停止，已找到的结果会保留...'
}

const startSearch = async () => {
  const factionId = String(form.factionId).trim()
  if (!factionId || !/^\d+$/.test(factionId)) {
    errorMessage.value = '请输入有效的帮派 ID（纯数字）'
    return
  }
  if (!props.apiKey) {
    errorMessage.value = '请先在侧边栏输入 API Key'
    return
  }
  if (!form.minHits || form.minHits < 1) {
    errorMessage.value = '请输入有效的 Chain 长度阈值'
    return
  }

  loading.value = true
  stopRequested.value = false
  errorMessage.value = ''
  searchDone.value = false
  results.value = []
  scannedCount.value = 0
  factionName.value = ''

  const cutoff = Math.floor(Date.now() / 1000) - form.years * 365 * 24 * 3600

  try {
    // 帮派名（失败不阻塞主流程）
    try {
      await rateLimiter()
      progressText.value = '正在获取帮派信息...'
      const factionData = await fetchApi(`/faction/${factionId}`)
      const info = factionData.basic || factionData
      factionName.value = info?.name || ''
    } catch (e) {
      console.warn('获取帮派信息失败，继续搜索 Chain:', e)
    }

    // 从当前时间开始，通过不断把 to 时间戳前移来向更早的 Chain 翻页
    let currentTo = Math.floor(Date.now() / 1000)
    const seenIds = new Set()
    let page = 0

    while (true) {
      if (stopRequested.value) break
      page++
      if (page > MAX_PAGES) {
        progressText.value = `已达单次搜索页数上限（${MAX_PAGES} 页 / ${MAX_PAGES * 100} 条），提前结束。`
        break
      }

      await rateLimiter()
      progressText.value = `正在抓取第 ${page} 页 Chain 列表...（已扫描 ${scannedCount.value} 条，命中 ${results.value.length} 条，当前回溯到 ${formatTimestamp(currentTo)}）`

      const data = await fetchApi(`/faction/${factionId}/chains?limit=100&sort=DESC&to=${currentTo}`)
      const chains = data.chains || []
      if (chains.length === 0) break

      let allOlderThanCutoff = true
      let oldestEnd = null
      for (const chain of chains) {
        if (chain.end >= cutoff) allOlderThanCutoff = false
        // to 按开始时间过滤，边界处会重复返回上一页的 chain，按 id 去重
        if (seenIds.has(chain.id)) continue
        seenIds.add(chain.id)
        scannedCount.value++
        if (oldestEnd === null || chain.end < oldestEnd) oldestEnd = chain.end
        if (chain.end >= cutoff && chain.chain >= form.minHits) {
          results.value.push(chain)
        }
      }

      // 本页全部早于回溯下限，更早的 Chain 无需再看
      if (allOlderThanCutoff) break
      if (oldestEnd === null) break

      // 把 to 前移到本页最早结束时间的前一秒；若未能前进则强制减 1 秒防止死循环
      const nextTo = oldestEnd - 1
      currentTo = nextTo < currentTo ? nextTo : currentTo - 1
    }

    results.value.sort((a, b) => b.end - a.end)
    searchDone.value = true
    progressText.value = stopRequested.value
      ? `搜索已手动停止：已扫描 ${scannedCount.value} 条 Chain，找到 ${results.value.length} 条长度 ≥ ${form.minHits} 的 Chain。`
      : `搜索完成：已扫描 ${scannedCount.value} 条 Chain，找到 ${results.value.length} 条长度 ≥ ${form.minHits} 的 Chain。`
  } catch (e) {
    console.error('Chain 历史搜索失败:', e)
    errorMessage.value = e.response?.data?.error?.error || e.message || '搜索失败'
    if (results.value.length > 0) {
      results.value.sort((a, b) => b.end - a.end)
      searchDone.value = true
    }
  } finally {
    loading.value = false
  }
}

const copyAllLinks = async () => {
  const text = results.value.map((chain) => chainReportUrl(chain.id)).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`已复制 ${results.value.length} 条 Chain 链接`)
  } catch (e) {
    // clipboard API 不可用时的降级方案
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(`已复制 ${results.value.length} 条 Chain 链接`)
  }
}

const exportXlsx = () => {
  if (results.value.length === 0) return

  const data = results.value.map((chain, index) => ({
    '序号': index + 1,
    'Chain 链接': {
      t: 's',
      v: `Chain ${chain.id}`,
      l: { Target: chainReportUrl(chain.id) }
    },
    'Chain ID': chain.id,
    'Hits': chain.chain,
    'Respect': chain.respect,
    '开始时间 (TCT)': formatTimestamp(chain.start),
    '结束时间 (TCT)': formatTimestamp(chain.end),
    '开始时间戳': chain.start,
    '结束时间戳': chain.end
  }))

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(data)
  ws['!cols'] = [
    { wch: 6 },
    { wch: 16 },
    { wch: 12 },
    { wch: 10 },
    { wch: 12 },
    { wch: 20 },
    { wch: 20 },
    { wch: 14 },
    { wch: 14 }
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'Chains')

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  XLSX.writeFile(wb, `faction_chains_${form.factionId}_${timestamp}.xlsx`)
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

.result-section {
  margin-top: 20px;
}

.result-actions {
  margin: 15px 0;
  display: flex;
  gap: 10px;
}
</style>
