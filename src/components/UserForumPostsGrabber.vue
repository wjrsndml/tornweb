<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>个人论坛回帖抓取</h2>
      </div>
    </template>

    <p>
      抓取用户论坛回帖
    </p>

    <el-form :model="form" label-width="140px">
      <el-form-item label="User ID">
        <el-input v-model="form.userId" placeholder="支持粘贴用户URL或纯数字ID" />
      </el-form-item>

      <el-form-item label="striptags">
        <el-switch v-model="form.stripTags" />
        <span class="hint">（开启后回帖内容会去掉 HTML 标签）</span>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="fetchUserProfile" :loading="loadingProfile" :disabled="!canUse">
          抓取用户概要
        </el-button>
        <el-button
          type="primary"
          @click="fetchUserForumPosts"
          :loading="loadingPosts"
          :disabled="!canUse || !profile || !isRangeValid"
        >
          抓取论坛回帖<span v-if="plannedPages">（约 {{ plannedPages }} 次请求）</span>
        </el-button>
        <el-button @click="clearAll" :disabled="loadingProfile || loadingPosts">
          清空
        </el-button>
      </el-form-item>

      <el-form-item v-if="profile" label="回帖范围">
        <div class="range-row">
          <el-input-number v-model="form.offsetStart" :min="0" :step="20" />
          <span class="range-sep">~</span>
          <el-input-number v-model="form.offsetEnd" :min="0" :step="20" />
          <span class="hint" style="margin-left: 10px">
            （单次最多请求20条；profile显示回帖数：{{ totalForumPosts || '未知' }}）
          </span>
        </div>
      </el-form-item>

      <el-form-item v-if="postsProgress.active" label="抓取进度">
        <div class="progress-box">
          <el-progress :percentage="postsProgressPercent" :stroke-width="14" />
          <div class="progress-text">
            已完成 {{ postsProgress.finishedPages }}/{{ postsProgress.plannedPages }} 次请求；已收集
            {{ postsProgress.fetchedCount }}/{{ postsProgress.targetCount }} 条
            <span v-if="postsProgress.stopReason">；停止原因：{{ postsProgress.stopReason }}</span>
          </div>
        </div>
      </el-form-item>
    </el-form>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      style="margin-top: 12px"
    />

    <div v-if="profile" class="result-section">
      <el-divider content-position="center">用户概要</el-divider>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ profile.id }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ profile.name }}</el-descriptions-item>
        <el-descriptions-item label="等级">{{ profile.level }}</el-descriptions-item>
        <el-descriptions-item label="Rank">{{ profile.rank }}</el-descriptions-item>
        <el-descriptions-item label="Forum posts">{{ profile.forum_posts }}</el-descriptions-item>
        <el-descriptions-item label="Karma">{{ profile.karma }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div v-if="forumPosts && forumPosts.length" class="result-section">
      <el-divider content-position="center">
        回帖（{{ lastFetch.offsetStart }}~{{ lastFetch.offsetEnd }}，共 {{ forumPosts.length }} 条）
      </el-divider>

      <div class="posts-toolbar">
        <div class="action-bar" style="margin-top: 0">
          <el-button type="success" @click="exportJson" :disabled="!profile">
            导出 JSON
          </el-button>
          <el-button @click="copyRawJsonToClipboard" :disabled="!profile">
            复制原始 JSON
          </el-button>
          <el-button type="warning" @click="copyAiSummaryPackToClipboard" :disabled="!profile">
            一键复制给 AI 总结（中文，含回帖）
          </el-button>
          <el-button @click="postsListCollapsed = !postsListCollapsed">
            {{ postsListCollapsed ? '展开回帖列表' : '折叠回帖列表' }}
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="postsListCollapsed"
        type="info"
        show-icon
        :closable="false"
        style="margin-top: 10px"
        title="回帖列表已折叠（避免内容过长影响滚动）。你仍可直接导出/复制/AI总结；如需查看回帖，请点击“展开回帖列表”。"
      />

      <el-table v-if="!postsListCollapsed" :data="forumPosts" stripe size="small" style="width: 100%">
        <el-table-column label="时间(TCT)" width="170">
          <template #default="scope">
            {{ formatTime(scope.row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="thread_id" label="Thread ID" width="110" />
        <el-table-column label="赞/踩" width="100">
          <template #default="scope">
            {{ scope.row.likes }}/{{ scope.row.dislikes }}
          </template>
        </el-table-column>
        <el-table-column label="内容">
          <template #default="scope">
            <div class="post-content">{{ scope.row.content }}</div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
// UserForumPostsGrabber.vue
// 作用：抓取 Torn 用户 profile（用于获取 forum_posts 总数）与用户 forumPosts，并提供范围抓取、进度展示、导出/复制与 AI 总结；长回帖默认折叠可展开。
// 重要说明：
// - 论坛改版可能导致分页断裂：一旦检测到重复 post id，或单页返回少于 20 条，则停止抓取并提示原因。
// - API 限速：至少 1s/次请求，避免触发 Torn 的 rate limit。
import { computed, reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { createRateLimiter } from '../utils/requestRateLimiter'

const props = defineProps({
  apiKey: {
    type: String,
    required: true
  }
})

const ensureRateLimit = createRateLimiter(1000)

const form = reactive({
  userId: '',
  stripTags: true,
  offsetStart: 0,
  offsetEnd: 19
})

const loadingProfile = ref(false)
const loadingPosts = ref(false)
const error = ref(null)

const profile = ref(null)
const forumPosts = ref([])

// 回帖量巨大时默认折叠“整块列表”，避免滚动太久才能导出/复制
const AUTO_COLLAPSE_LIST_THRESHOLD = 120
const postsListCollapsed = ref(false)

const postsProgress = reactive({
  active: false,
  start: 0,
  end: 0,
  targetCount: 0,
  pageSize: 20,
  plannedPages: 0,
  finishedPages: 0,
  fetchedCount: 0,
  stopReason: ''
})

const postsProgressPercent = computed(() => {
  if (!postsProgress.active || postsProgress.plannedPages <= 0) return 0
  const p = Math.round((postsProgress.finishedPages / postsProgress.plannedPages) * 100)
  return Math.max(0, Math.min(100, p))
})

const lastFetch = reactive({
  offsetStart: 0,
  offsetEnd: 0,
  stripTags: true,
  pageSize: 20,
  stopped: false,
  stopReason: ''
})

const canUse = computed(() => {
  return Boolean(props.apiKey) && Boolean(String(form.userId || '').trim())
})

const totalForumPosts = computed(() => {
  const n = Number(profile.value?.forum_posts)
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0
})

const clampInt = (val, min, max) => {
  const n = Math.floor(Number(val))
  if (!Number.isFinite(n)) return min
  if (n < min) return min
  if (n > max) return max
  return n
}

const rangeMaxIndex = computed(() => {
  if (totalForumPosts.value > 0) return totalForumPosts.value - 1
  return 0
})

const isRangeValid = computed(() => {
  if (!profile.value) return false
  const max = rangeMaxIndex.value
  const s = clampInt(form.offsetStart, 0, max)
  const e = clampInt(form.offsetEnd, 0, max)
  return s <= e
})

const plannedPages = computed(() => {
  if (!isRangeValid.value) return 0
  const max = rangeMaxIndex.value
  const s = clampInt(form.offsetStart, 0, max)
  const e = clampInt(form.offsetEnd, 0, max)
  const pageSize = 20
  return Math.ceil((e - s + 1) / pageSize)
})

const authHeaders = computed(() => {
  return {
    accept: 'application/json',
    Authorization: `ApiKey ${props.apiKey}`
  }
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(Number(timestamp) * 1000)
  return date.toLocaleString('zh-CN', { timeZone: 'UTC' })
}

const normalizeUserId = () => {
  const t = String(form.userId || '').trim()
  if (!t) return null
  const m = t.match(/(\d+)/g)
  if (!m || !m.length) return null
  return m[m.length - 1]
}

const clearAll = () => {
  error.value = null
  profile.value = null
  forumPosts.value = []
  postsListCollapsed.value = false

  postsProgress.active = false
  postsProgress.start = 0
  postsProgress.end = 0
  postsProgress.targetCount = 0
  postsProgress.pageSize = 20
  postsProgress.plannedPages = 0
  postsProgress.finishedPages = 0
  postsProgress.fetchedCount = 0
  postsProgress.stopReason = ''

  lastFetch.offsetStart = 0
  lastFetch.offsetEnd = 0
  lastFetch.stripTags = true
  lastFetch.pageSize = 20
  lastFetch.stopped = false
  lastFetch.stopReason = ''
}

const fetchUserProfile = async () => {
  if (!canUse.value) return
  error.value = null
  loadingProfile.value = true

  try {
    const userId = normalizeUserId()
    if (!userId) {
      error.value = 'User ID 无效'
      return
    }

    const url = `https://api.torn.com/v2/user/${userId}/profile`
    await ensureRateLimit()
    const res = await axios.get(url, {
      headers: authHeaders.value,
      params: { striptags: form.stripTags ? 'true' : 'false' }
    })

    profile.value = res?.data?.profile || null
    if (!profile.value) {
      error.value = '未获取到 profile 数据'
      return
    }

    if (totalForumPosts.value > 0) {
      form.offsetStart = 0
      form.offsetEnd = Math.min(19, rangeMaxIndex.value)
    } else {
      form.offsetStart = 0
      form.offsetEnd = 19
    }

    ElMessage.success('用户概要抓取成功')
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.error?.error || e.response?.data?.error || e.message || '抓取失败'
  } finally {
    loadingProfile.value = false
  }
}

const fetchUserForumPosts = async () => {
  if (!canUse.value) return
  if (!profile.value) {
    error.value = '请先抓取用户概要'
    return
  }
  if (!isRangeValid.value) {
    error.value = '回帖范围不合法，请检查 offsetStart/offsetEnd'
    return
  }

  error.value = null
  loadingPosts.value = true

  try {
    const userId = normalizeUserId()
    if (!userId) {
      error.value = 'User ID 无效'
      return
    }

    const pageSize = 20
    const max = rangeMaxIndex.value
    const start = clampInt(form.offsetStart, 0, max)
    const end = clampInt(form.offsetEnd, 0, max)

    const baseUrl = `https://api.torn.com/v2/user/${userId}/forumposts`
    // 注意：按你的要求，这里通过 _metadata.links.prev 继续分页抓取
    // （论坛改版后 next/prev 的方向可能与直觉不同，本工具明确使用 prev）
    let prevUrl = baseUrl

    const collected = []
    const seenIds = new Set()

    postsProgress.active = true
    postsProgress.start = start
    postsProgress.end = end
    postsProgress.targetCount = end - start + 1
    postsProgress.pageSize = pageSize
    postsProgress.plannedPages = Math.ceil((end - start + 1) / pageSize)
    postsProgress.finishedPages = 0
    postsProgress.fetchedCount = 0
    postsProgress.stopReason = ''

    let globalIndex = 0
    let stopped = false
    let stopReason = ''

    while (prevUrl && globalIndex <= end) {
      await ensureRateLimit()
      const res = await axios.get(prevUrl, {
        headers: authHeaders.value,
        ...(prevUrl === baseUrl
          ? { params: { striptags: form.stripTags ? 'true' : 'false', limit: pageSize } }
          : {})
      })

      const dataPosts = res?.data?.forumPosts
      if (!Array.isArray(dataPosts)) {
        error.value = '未获取到 forumPosts 数据'
        return
      }
      if (dataPosts.length === 0) {
        stopped = true
        stopReason = '接口返回空数据，已停止抓取'
        break
      }

      for (let i = 0; i < dataPosts.length; i++) {
        const p = dataPosts[i]
        const id = p?.id
        if (id != null) {
          if (seenIds.has(id)) {
            stopped = true
            stopReason = '检测到重复数据（论坛改版导致分页可能断裂），已停止抓取'
            break
          }
          seenIds.add(id)
        }

        const idx = globalIndex
        globalIndex += 1

        if (idx < start) continue
        if (idx > end) break
        collected.push(p)
      }

      postsProgress.fetchedCount = collected.length
      postsProgress.finishedPages += 1

      if (stopped) break

      if (dataPosts.length < pageSize) {
        stopped = true
        stopReason = '单次返回少于 20 条（可能到末尾或论坛改版导致缺失），已停止抓取'
        break
      }

      prevUrl = res?.data?._metadata?.links?.prev || null
      if (!prevUrl && globalIndex <= end) {
        stopped = true
        stopReason = '没有 prev 链接，无法继续抓取（可能到末尾或论坛改版导致缺失）'
        break
      }
    }

    forumPosts.value = collected
    postsListCollapsed.value = forumPosts.value.length >= AUTO_COLLAPSE_LIST_THRESHOLD
    lastFetch.offsetStart = start
    lastFetch.offsetEnd = end
    lastFetch.stripTags = Boolean(form.stripTags)
    lastFetch.pageSize = pageSize
    lastFetch.stopped = Boolean(stopped)
    lastFetch.stopReason = stopReason || ''

    if (stopped && stopReason) {
      postsProgress.stopReason = stopReason
      ElMessage.warning(`回帖抓取结束：${forumPosts.value.length} 条（已提前停止：${stopReason}）`)
    } else {
      ElMessage.success(`回帖抓取成功：${forumPosts.value.length} 条（范围 ${start}~${end}）`)
    }
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.error?.error || e.response?.data?.error || e.message || '抓取失败'
  } finally {
    loadingPosts.value = false
    postsProgress.active = false
  }
}

const buildRawBundle = () => {
  return {
    profile: profile.value,
    forumPosts: forumPosts.value,
    _metadata: {
      fetched_at: new Date().toISOString(),
      forum_posts_fetch: forumPosts.value?.length
        ? {
            offsetStart: lastFetch.offsetStart,
            offsetEnd: lastFetch.offsetEnd,
            pageSize: lastFetch.pageSize,
            striptags: lastFetch.stripTags,
            stopped: lastFetch.stopped,
            stopReason: lastFetch.stopReason
          }
        : null
    }
  }
}

const downloadTextFile = (filename, text) => {
  const blob = new Blob([text], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

const exportJson = () => {
  if (!profile.value) return
  const userId = normalizeUserId() || 'user'
  const filename = `user_forum_posts_${userId}_${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}.json`
  downloadTextFile(filename, JSON.stringify(buildRawBundle(), null, 2))
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    console.error(e)
    error.value = '复制失败：浏览器可能不允许剪贴板写入（请尝试使用 HTTPS 或允许权限）'
  }
}

const copyRawJsonToClipboard = async () => {
  if (!profile.value) return
  await copyToClipboard(JSON.stringify(buildRawBundle(), null, 2))
}

const buildAiBundle = () => {
  const p = profile.value || {}
  const ai = {
    profile: {
      id: p.id,
      name: p.name,
      level: p.level,
      rank: p.rank,
      title: p.title,
      donator_status: p.donator_status,
      gender: p.gender,
      age: p.age,
      signed_up: p.signed_up,
      faction_id: p.faction_id,
      forum_posts: p.forum_posts,
      karma: p.karma
    },
    forumPosts: (forumPosts.value || []).map(fp => ({
      id: fp.id,
      thread_id: fp.thread_id,
      created_time: fp.created_time,
      is_legacy: fp.is_legacy,
      is_topic: fp.is_topic,
      is_edited: fp.is_edited,
      has_quote: fp.has_quote,
      likes: fp.likes,
      dislikes: fp.dislikes,
      content: (fp.content || '').trim()
    })),
    _metadata: {
      fetch: forumPosts.value?.length
        ? {
            offsetStart: lastFetch.offsetStart,
            offsetEnd: lastFetch.offsetEnd,
            pageSize: lastFetch.pageSize,
            striptags: lastFetch.stripTags,
            stopped: lastFetch.stopped,
            stopReason: lastFetch.stopReason
          }
        : null,
      note: '数据来自 Torn API 的用户 forumPosts（可能因论坛改版分页断裂导致抓取不完整）。'
    }
  }

  const prompt =
'# Role Definition\n' +
'你是一位拥有10年经验的《Torn City》（撕裂之城）资深玩家，同时也是一位精通文本分析的心理侧写专家。你熟悉这款游戏的所有机制、复杂的地下经济、帮派政治（Faction Politics）以及论坛独特的亚文化（包括喷子文化、诈骗套路和黑话）。\n' +
'\n' +
'# Task\n' +
'我将提供一名玩家在 Torn City 官方论坛发布的英文帖子记录（Post History）。请你深入分析这些文本，用**中文**为这名玩家生成一份详细的“人物侧写报告”。\n' +
'\n' +
'# Analysis Guidelines (分析指南)\n' +
'在分析时，请务必遵循以下原则：\n' +
'1.  **语境识别**：Torn 的论坛（特别是 General Discussion）充满了反讽（Sarcasm）和诱饵（Bait）。不要把所有的“威胁”或“愚蠢言论”当真，这通常是钓鱼行为。\n' +
'2.  **黑话理解**：请准确理解游戏术语。例如：\n' +
'    * "Mug" 是游戏机制（抢劫），不代表现实恶意。\n' +
'    * "RW" 指 Ranked War（排位战）。\n' +
'    * "Scammer" 指骗子，需特别警惕交易相关的发言。\n' +
'    * "Buy-mug" 指交易后立刻抢劫对方的行为。\n'  +
'# Output Format (输出格式)\n' +
'请大致按照以下结构输出中文报告，但不要完全按照这个结构输出，根据实际收到的信息自行发挥补充你觉得重要的内容：\n' +
'\n' +
'## 1. 玩家类型 (Archetype)\n' +
'* **核心标签**：(资深大佬 / 萌新小白 / 论坛喷子(Troll) / 奸商 / 帮派管理 / 乞丐 / 骗子嫌疑人 / 吃瓜群众等等，如果以上都不符合，请自行写出其他合适的标签)\n' +
'* **总结**：(概括为什么给他是这个标签)\n' +
'\n' +
'## 2. 性格与行为特征 (Personality & Behavior)\n' +
'* **攻击性 (Aggression)**：(高/中/低) - 他是否喜欢挑起争端？\n' +
'* **可信度 (Trustworthiness)**：(高/存疑/极低) - 他的交易贴或言论是否诚实？\n' +
'* **游戏理解 (Knowledge)**：(精通/一般/无知) - 他是否懂游戏机制（如健身房算法、战争策略）？\n' +
'* **社区形象**：他是受人尊敬，还是人人喊打？\n' +
'\n' +
'## 3. 阵营与倾向\n' +
'* **帮派立场**：通过发言判断，他是否效忠于某些大型联盟（如 Monarch, Natural Selection, PT 等）？还是他是独立玩家/雇佣兵？\n' +
'* **政治态度**：他是否表现出反对某个阵营的情绪，或者是某些大佬的追随者？\n' +
'\n' +
'## 4. 潜在风险提示 (Red Flags)\n' +
'* (如果没有风险请写“无明显风险”)\n' +
'* [ ] **诈骗风险**：是否有“低价出售”、“高利贷”等可疑言论？\n' +
'* [ ] **乞讨行为**：是否经常索要免费物品？\n' +
'* [ ] **违规嫌疑**：是否谈论过 RMT (现实货币交易) 或多开账号 (Multi)？\n'

  return { prompt, data: ai }
}

const copyAiSummaryPackToClipboard = async () => {
  if (!profile.value) return
  const pack = buildAiBundle()
  const text = pack.prompt + JSON.stringify(pack.data, null, 2)
  await copyToClipboard(text)
}
</script>

<style scoped>
.hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.range-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.range-sep {
  color: #606266;
}

.result-section {
  margin-top: 12px;
}

.action-bar {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.post-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.progress-box {
  width: 100%;
}

.progress-text {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}
</style>


