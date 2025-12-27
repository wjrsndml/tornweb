<!--
FactionOcStatus.vue
作用：通过 Torn v2 `/faction/crimes?cat=available` 接口获取帮派当前 OC（有组织犯罪）信息，
并统计 difficulty >= 7 的 OC：已上车人数、总坑位（含空缺）、以及按人数档位计算 OC 分数（6/5/4/3人）。
修改记录：
- 2025-12-27：新增组件，支持一键刷新与明细列表展示。
- 2025-12-27：新增目标分数（可编辑）、未来24h分数、差值/补齐计算、按完成时间排序，并完善分值规则与提示文案。
-->
<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>帮派 OC 推荐</h2>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="fetchCrimes" :loading="loading" :disabled="!apiKey">
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <el-alert
      class="notice"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 12px"
    >
      <template #title>
        <span class="notice-title">注意事项</span>
      </template>
      <template #default>
        <div class="notice-body">
          目标分数为能做7级以上oc的总人数再减去一点冗余。6人oc+3.5分，5人oc+3分，4人oc+2.5分，3人oc+2分。
        </div>
      </template>
    </el-alert>

    <el-alert
      v-if="!apiKey"
      title="请先在左侧输入 API Key"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 12px"
    />

    <div v-if="summary" class="summary">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="7级以上OC 数量">{{ summary.ocCount }}</el-descriptions-item>
        <el-descriptions-item label="当前 OC 分数">{{ summary.ocScore.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="已上车人数（difficulty ≥ 7）">{{ summary.filledUsers }}</el-descriptions-item>
        <el-descriptions-item label="总坑位（含空缺）">{{ summary.totalSlots }}</el-descriptions-item>
        <el-descriptions-item label="目标分数">
          <el-input-number
            v-model="targetScore"
            :min="0"
            :precision="0"
            size="small"
            style="width: 180px"
          />
        </el-descriptions-item>
        <el-descriptions-item label="未来24h完成 OC 分数">{{ summary.future24hScore.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="下一个OC完成时间(TCT)">{{ summary.earliestCompletionUtc || '-' }}</el-descriptions-item>
        <el-descriptions-item label="距离下一个OC完成">{{ summary.earliestCompletionIn || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div v-if="summary" class="gap-section">
      <el-divider content-position="center">OC生成计算</el-divider>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="当前所需分数">
          {{ calc1.gapText }}
          <span v-if="calc1.needText">；建议：{{ calc1.needText }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="未来24h所需分数">
          {{ calc2.gapText }}
          <span v-if="calc2.needText">；建议：{{ calc2.needText }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-divider content-position="center">OC详情</el-divider>

    <el-table v-if="filteredCrimes.length" :data="filteredCrimes" stripe style="width: 100%" size="small">
      <el-table-column prop="name" label="名称" min-width="220" />
      <el-table-column prop="difficulty" label="难度" width="80" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="人数(已上车/总坑位)" width="150">
        <template #default="scope">
          {{ scope.row._filled }}/{{ scope.row._slots }}
        </template>
      </el-table-column>
      <el-table-column label="分值" width="80">
        <template #default="scope">
          {{ scope.row._score.toFixed(1) }}
        </template>
      </el-table-column>
      <el-table-column label="完成时间(TCT)" width="170">
        <template #default="scope">
          {{ scope.row._completionAt ? formatUtc(scope.row._completionAt) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="距离完成" width="120">
        <template #default="scope">
          {{ scope.row._completionAt ? formatRemaining(scope.row._completionAt) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="Created at (TCT)" width="170">
        <template #default="scope">
          {{ scope.row.created_at ? formatUtc(scope.row.created_at) : '-' }}
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else description="暂无符合条件的 OC（difficulty ≥ 7）" />

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      style="margin-top: 12px"
    />
  </el-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import axios from 'axios'
import { createRateLimiter } from '../utils/requestRateLimiter'

const props = defineProps({
  apiKey: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const error = ref(null)
const crimes = ref([])
const targetScore = ref(0)
const targetScoreTouched = ref(false)

const apiKey = computed(() => String(props.apiKey || '').trim())
const ensureRate = createRateLimiter(1100)

const formatUtc = (epochSeconds) => {
  const d = new Date(Number(epochSeconds) * 1000)
  return d.toLocaleString('en-GB', { timeZone: 'UTC' })
}

const formatRemaining = (epochSeconds) => {
  const now = Date.now()
  const t = Number(epochSeconds) * 1000
  const diffMs = t - now
  if (!Number.isFinite(diffMs)) return '-'
  if (diffMs <= 0) return '已到'
  const totalSeconds = Math.ceil(diffMs / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  return `${h}h${m}m`
}

const calcScoreBySlots = (slotsCount) => {
  if (slotsCount === 6) return 3.5
  if (slotsCount === 5) return 3
  if (slotsCount === 4) return 2.5
  if (slotsCount === 3) return 2
  return 0
}

const getCompletionAt = (crime) => {
  // 完成时间只认 ready_at：
  // - 当 OC 没人/未成型时，ready_at 可能为 null，此时不应误显示“已到”
  // - 没有 ready_at 的条目在排序中自然放到最后
  const v = Number(crime?.ready_at || 0) || 0
  return Number.isFinite(v) && v > 0 ? v : 0
}

const filteredCrimes = computed(() => {
  const list = (crimes.value || [])
    .filter(c => Number(c?.difficulty || 0) >= 7)
    .map(c => {
      const slots = Array.isArray(c?.slots) ? c.slots : []
      const filled = slots.reduce((sum, s) => sum + (s?.user ? 1 : 0), 0)
      const slotsCount = slots.length
      const score = calcScoreBySlots(slotsCount)
      const completionAt = getCompletionAt(c)
      return { ...c, _slots: slotsCount, _filled: filled, _score: score, _completionAt: completionAt }
    })
    .sort((a, b) => {
      const ta = Number(a?._completionAt || 0) || 0
      const tb = Number(b?._completionAt || 0) || 0
      if (ta === 0 && tb === 0) return 0
      if (ta === 0) return 1
      if (tb === 0) return -1
      return ta - tb
    })
  return list
})

const summary = computed(() => {
  const list = filteredCrimes.value
  if (!list || list.length === 0) return null

  let filledUsers = 0
  let totalSlots = 0
  let ocScore = 0
  let future24hScore = 0

  const nowSec = Math.floor(Date.now() / 1000)
  const endSec = nowSec + 24 * 3600

  for (const c of list) {
    filledUsers += Number(c._filled || 0)
    totalSlots += Number(c._slots || 0)
    ocScore += Number(c._score || 0)
    const completionAt = Number(c._completionAt || 0) || 0
    if (completionAt >= nowSec && completionAt <= endSec) {
      future24hScore += Number(c._score || 0)
    }
  }

  const earliest = list.find(x => Number(x?._completionAt || 0) > 0)
  const earliestAt = earliest ? Number(earliest._completionAt || 0) : 0

  return {
    ocCount: list.length,
    filledUsers,
    totalSlots,
    ocScore,
    future24hScore,
    earliestCompletionUtc: earliestAt ? formatUtc(earliestAt) : '',
    earliestCompletionIn: earliestAt ? formatRemaining(earliestAt) : ''
  }
})

const computeNeedFor6And4 = (gap) => {
  const g = Number(gap)
  if (!Number.isFinite(g) || g <= 0) {
    return { a6: 0, a4: 0, covered6: 0, covered4: 0 }
  }

  // 按用户口径：两种方案分别计算（不做“混搭最优”）
  // - 6人OC所需数量 = gap / 3.5 取整（为保证能补齐差值，这里使用向上取整）
  // - 4人OC所需数量 = gap / 2.5 取整（同上）
  const a6 = Math.ceil(g / 3.5)
  const a4 = Math.ceil(g / 2.5)
  return { a6, a4, covered6: a6 * 3.5, covered4: a4 * 2.5 }
}

const calc1 = computed(() => {
  const s = summary.value
  if (!s) return { gapText: '-', needText: '' }
  const gap = Number(targetScore.value || 0) - Number(s.ocScore || 0)
  if (gap <= 0) return { gapText: `${gap.toFixed(1)}（已达标）`, needText: '' }
  const need = computeNeedFor6And4(gap)
  return {
    gapText: `${gap.toFixed(1)}`,
    needText: `仅做6人OC：× ${need.a6}（约 ${need.covered6.toFixed(1)} 分）；仅做4人OC：× ${need.a4}（约 ${need.covered4.toFixed(1)} 分）`
  }
})

const calc2 = computed(() => {
  const s = summary.value
  if (!s) return { gapText: '-', needText: '' }
  // “未来24h所需分数”按：目标分数 + 未来24h完成分数 - 当前OC分数
  const gap =
    Number(targetScore.value || 0) +
    Number(s.future24hScore || 0) -
    Number(s.ocScore || 0)
  if (gap <= 0) return { gapText: `${gap.toFixed(1)}（已达标）`, needText: '' }
  const need = computeNeedFor6And4(gap)
  return {
    gapText: `${gap.toFixed(1)}`,
    needText: `仅做6人OC：× ${need.a6}（约 ${need.covered6.toFixed(1)} 分）；仅做4人OC：× ${need.a4}（约 ${need.covered4.toFixed(1)} 分）`
  }
})

const fetchCrimesPage = async (url) => {
  await ensureRate()
  const resp = await axios.get(url, {
    headers: {
      accept: 'application/json',
      Authorization: `ApiKey ${apiKey.value}`
    }
  })
  return resp?.data
}

const fetchCrimes = async () => {
  if (!apiKey.value) return

  loading.value = true
  error.value = null
  crimes.value = []

  try {
    // 说明：该 v2 接口使用 Authorization header（与旧版 ?key=... 不同）
    let nextUrl = 'https://api.torn.com/v2/faction/crimes?cat=available&offset=0&sort=DESC'
    const all = []
    let guard = 0

    while (nextUrl) {
      guard++
      if (guard > 50) throw new Error('分页保护阀触发：next 链接过多，已中止。')

      const data = await fetchCrimesPage(nextUrl)
      const batch = Array.isArray(data?.crimes) ? data.crimes : []
      all.push(...batch)

      const next = data?._metadata?.links?.next
      nextUrl = next ? String(next) : ''
      if (!nextUrl) break
    }

    crimes.value = all
  } catch (e) {
    console.error(e)
    error.value = e?.response?.data?.error?.error || e?.message || '获取 OC 数据失败'
  } finally {
    loading.value = false
  }
}

// API Key 变化时自动刷新一次（避免用户每次都手动点）
watch(
  () => apiKey.value,
  (v, oldV) => {
    if (!v) return
    if (v === oldV) return
    fetchCrimes()
  }
)

// summary 更新后，若用户未手动改过目标分数，则默认=已上车人数
watch(
  () => summary.value?.filledUsers,
  (v) => {
    if (!Number.isFinite(Number(v))) return
    if (targetScoreTouched.value) return
    targetScore.value = Number(v)
  }
)

watch(
  () => targetScore.value,
  (v, oldV) => {
    // 用户手动编辑才算 touched；首次由程序赋值时 oldV 可能为 0，这里用启发式避免误判
    if (v === oldV) return
    if (summary.value && Number(oldV) === 0 && Number(v) === Number(summary.value.filledUsers)) return
    targetScoreTouched.value = true
  }
)
</script>

<style scoped>
.desc {
  margin: 0 0 12px;
  color: #606266;
  font-size: 13px;
}

.notice :deep(.el-alert__title) {
  font-weight: 800;
}

.notice-title {
  font-weight: 800;
  font-size: 14px;
}

.notice-body {
  font-weight: 700;
  color: #7a4b00;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.summary {
  margin: 12px 0;
}

.gap-section {
  margin-top: 12px;
}
</style>


