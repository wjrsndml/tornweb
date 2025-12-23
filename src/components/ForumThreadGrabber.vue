<template>
  <el-card class="function-card">
    <template #header>
      <div class="card-header">
        <h2>论坛帖子抓取</h2>
      </div>
    </template>

    <p>抓取指定论坛帖子信息，支持导出 JSON、复制原始 JSON、以及一键复制给AI总结内容。</p>

    <el-form :model="form" label-width="140px">
      <el-form-item label="Thread ID">
        <el-input v-model="form.threadId" />
      </el-form-item>

      <el-form-item label="striptags">
        <el-switch v-model="form.stripTags" />
        <span class="hint">（开启后回帖内容会去掉 HTML 标签）</span>
      </el-form-item>

      <el-form-item v-if="thread" label="回帖范围">
        <div class="range-row">
          <el-input-number v-model="form.offsetStart" :min="0" :step="20" />
          <span class="range-sep">~</span>
          <el-input-number v-model="form.offsetEnd" :min="0" :step="20" />
          <span class="hint" style="margin-left: 10px">
            （单次最多请求20条；当前总回帖数：{{ totalPosts || '未知' }}）
          </span>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="fetchThread" :loading="loadingThread" :disabled="!canUse">
          抓取帖子概要
        </el-button>
        <el-button
          type="primary"
          @click="fetchPosts"
          :loading="loadingPosts"
          :disabled="!canUse || !thread || !isRangeValid"
        >
          抓取回帖<span v-if="plannedPages">（约 {{ plannedPages }} 次请求）</span>
        </el-button>
        <el-button @click="clearAll" :disabled="loadingThread || loadingPosts">
          清空
        </el-button>
      </el-form-item>

      <el-form-item v-if="postsProgress.active" label="抓取进度">
        <div class="progress-box">
          <el-progress :percentage="postsProgressPercent" :stroke-width="14" />
          <div class="progress-text">
            已完成 {{ postsProgress.finishedPages }}/{{ postsProgress.plannedPages }} 次请求；已收集
            {{ postsProgress.fetchedCount }}/{{ postsProgress.targetCount }} 条；当前 offset={{ postsProgress.currentOffset }}
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

    <div v-if="thread" class="result-section">
      <el-divider content-position="center">帖子概要</el-divider>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ thread.title }}</el-descriptions-item>
        <el-descriptions-item label="Forum ID">{{ thread.forum_id }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ thread.author?.username }}</el-descriptions-item>
        <el-descriptions-item label="最后回复者">{{ thread.last_poster?.username }}</el-descriptions-item>
        <el-descriptions-item label="回帖数">{{ thread.posts }}</el-descriptions-item>
        <el-descriptions-item label="浏览">{{ thread.views }}</el-descriptions-item>
        <el-descriptions-item label="评分">{{ thread.rating }}</el-descriptions-item>
        <el-descriptions-item label="锁定/置顶">
          {{ thread.is_locked ? '锁定' : '未锁定' }} / {{ thread.is_sticky ? '置顶' : '未置顶' }}
        </el-descriptions-item>
        <el-descriptions-item label="首帖时间(TCT)">{{ formatTime(thread.first_post_time) }}</el-descriptions-item>
        <el-descriptions-item label="最后回复时间(TCT)">{{ formatTime(thread.last_post_time) }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="thread.poll" class="poll-section">
        <el-divider content-position="left">投票</el-divider>
        <div class="poll-question">{{ thread.poll.question }}</div>
        <el-table :data="thread.poll.answers || []" stripe size="small" style="width: 100%">
          <el-table-column prop="answer" label="选项" />
          <el-table-column prop="votes" label="票数" width="120" />
        </el-table>
      </div>

      <el-tabs style="margin-top: 12px">
        <el-tab-pane label="content">
          <pre class="content-pre">{{ thread.content }}</pre>
        </el-tab-pane>
        <el-tab-pane label="content_raw">
          <pre class="content-pre">{{ thread.content_raw }}</pre>
        </el-tab-pane>
      </el-tabs>

      <div class="action-bar">
        <el-button type="success" @click="exportJson" :disabled="!thread">
          导出 JSON
        </el-button>
        <el-button @click="copyRawJsonToClipboard" :disabled="!thread">
          复制原始 JSON
        </el-button>
        <el-button type="warning" @click="copyAiSummaryPackToClipboard" :disabled="!thread">
          一键复制给 AI 总结
        </el-button>
      </div>
    </div>

    <div v-if="posts && posts.length" class="result-section">
      <el-divider content-position="center">
        回帖（{{ lastFetch.offsetStart }}~{{ lastFetch.offsetEnd }}，共 {{ posts.length }} 条）
      </el-divider>

      <el-table :data="posts" stripe size="small" style="width: 100%">
        <el-table-column label="时间(TCT)" width="170">
          <template #default="scope">
            {{ formatTime(scope.row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="作者" width="140">
          <template #default="scope">
            {{ scope.row.author?.username }}
          </template>
        </el-table-column>
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

      <div class="action-bar">
        <el-button type="success" @click="exportJson" :disabled="!thread">
          导出 JSON（含回帖）
        </el-button>
        <el-button @click="copyRawJsonToClipboard" :disabled="!thread">
          复制原始 JSON（含回帖）
        </el-button>
        <el-button type="warning" @click="copyAiSummaryPackToClipboard" :disabled="!thread">
          一键复制给 AI 总结（中文，含回帖）
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
// ForumThreadGrabber.vue
// 作用：抓取 Torn 论坛 Thread 及其回帖（posts），并提供导出/复制/AI总结用的精简复制；抓取回帖时显示分页抓取进度。
// 交互流程约定：
// - 用户先输入 Thread ID 抓取“帖子概要”（包含回帖总数 posts）。
// - 再根据回帖总数输入要抓取的回帖范围（offsetStart ~ offsetEnd）。
// - posts 接口单次最多返回 20 条，因此范围抓取会自动按 offset+=20 分页拉取。
import { computed, reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  apiKey: {
    type: String,
    required: true
  }
})

const form = reactive({
  threadId: '',
  stripTags: true,
  offsetStart: 0,
  offsetEnd: 19
})

const loadingThread = ref(false)
const loadingPosts = ref(false)
const error = ref(null)

const thread = ref(null)
const posts = ref([])

const postsProgress = reactive({
  active: false,
  start: 0,
  end: 0,
  targetCount: 0,
  pageSize: 20,
  plannedPages: 0,
  finishedPages: 0,
  currentOffset: 0,
  fetchedCount: 0
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
  pageSize: 20
})

const canUse = computed(() => {
  return Boolean(props.apiKey) && Boolean(String(form.threadId || '').trim())
})

const totalPosts = computed(() => {
  // Torn 返回的 thread.posts 通常是回帖数/总帖数；这里仅用作范围上限提示
  const n = Number(thread.value?.posts)
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
  // 假设 offset 从 0 开始，最大索引为 totalPosts-1；若未知则给个保守值
  if (totalPosts.value > 0) return totalPosts.value - 1
  return 0
})

const isRangeValid = computed(() => {
  if (!thread.value) return false
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
  // TCT = UTC+0
  return date.toLocaleString('zh-CN', { timeZone: 'UTC' })
}

const normalizeThreadId = () => {
  const t = String(form.threadId || '').trim()
  if (!t) return null
  // 允许用户粘贴 URL 或纯数字
  const m = t.match(/(\d+)/g)
  if (!m || !m.length) return null
  return m[m.length - 1]
}

const clearAll = () => {
  error.value = null
  thread.value = null
  posts.value = []

  postsProgress.active = false
  postsProgress.start = 0
  postsProgress.end = 0
  postsProgress.targetCount = 0
  postsProgress.pageSize = 20
  postsProgress.plannedPages = 0
  postsProgress.finishedPages = 0
  postsProgress.currentOffset = 0
  postsProgress.fetchedCount = 0

  lastFetch.offsetStart = 0
  lastFetch.offsetEnd = 0
  lastFetch.stripTags = true
  lastFetch.pageSize = 20
}

const fetchThread = async () => {
  if (!canUse.value) return
  error.value = null
  loadingThread.value = true

  try {
    const threadId = normalizeThreadId()
    if (!threadId) {
      error.value = 'Thread ID 无效'
      return
    }

    const url = `https://api.torn.com/v2/forum/${threadId}/thread`
    const res = await axios.get(url, { headers: authHeaders.value })
    thread.value = res?.data?.thread || null
    if (!thread.value) {
      error.value = '未获取到 thread 数据'
      return
    }
    // 初始化回帖范围：默认抓前 20 条（0~19），但不超过上限
    if (totalPosts.value > 0) {
      form.offsetStart = 0
      form.offsetEnd = Math.min(19, rangeMaxIndex.value)
    } else {
      form.offsetStart = 0
      form.offsetEnd = 19
    }
    ElMessage.success('帖子概要抓取成功')
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.error?.error || e.response?.data?.error || e.message || '抓取失败'
  } finally {
    loadingThread.value = false
  }
}

const fetchPosts = async () => {
  if (!canUse.value) return
  if (!thread.value) {
    error.value = '请先抓取帖子概要'
    return
  }
  if (!isRangeValid.value) {
    error.value = '回帖范围不合法，请检查 offsetStart/offsetEnd'
    return
  }
  error.value = null
  loadingPosts.value = true

  try {
    const threadId = normalizeThreadId()
    if (!threadId) {
      error.value = 'Thread ID 无效'
      return
    }

    const url = `https://api.torn.com/v2/forum/${threadId}/posts`
    const pageSize = 20

    const max = rangeMaxIndex.value
    const start = clampInt(form.offsetStart, 0, max)
    const end = clampInt(form.offsetEnd, 0, max)

    const collected = []
    const seen = new Set()

    postsProgress.active = true
    postsProgress.start = start
    postsProgress.end = end
    postsProgress.targetCount = end - start + 1
    postsProgress.pageSize = pageSize
    postsProgress.plannedPages = Math.ceil((end - start + 1) / pageSize)
    postsProgress.finishedPages = 0
    postsProgress.currentOffset = start
    postsProgress.fetchedCount = 0

    // 按 20 条分页：offset=0/20/40...
    for (let offset = start; offset <= end; offset += pageSize) {
      postsProgress.currentOffset = offset
      const res = await axios.get(url, {
        headers: authHeaders.value,
        params: {
          striptags: form.stripTags ? 'true' : 'false',
          offset
        }
      })

      const dataPosts = res?.data?.posts
      if (!Array.isArray(dataPosts)) {
        error.value = '未获取到 posts 数据'
        return
      }
      if (dataPosts.length === 0) break

      for (let i = 0; i < dataPosts.length; i++) {
        const idx = offset + i
        if (idx < start) continue
        if (idx > end) continue
        const p = dataPosts[i]
        const key = p?.id ?? `${idx}-${p?.created_time ?? ''}-${p?.author?.username ?? ''}`
        if (seen.has(key)) continue
        seen.add(key)
        collected.push(p)
      }

      postsProgress.fetchedCount = collected.length
      postsProgress.finishedPages += 1

      // 如果最后一页不足 20，通常意味着到末尾了
      if (dataPosts.length < pageSize) break
    }

    posts.value = collected
    lastFetch.offsetStart = start
    lastFetch.offsetEnd = end
    lastFetch.stripTags = Boolean(form.stripTags)
    lastFetch.pageSize = pageSize

    ElMessage.success(`回帖抓取成功：${posts.value.length} 条（范围 ${start}~${end}）`)
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
    thread: thread.value,
    posts: posts.value,
    _metadata: {
      fetched_at: new Date().toISOString(),
      posts_fetch: posts.value?.length
        ? {
            offsetStart: lastFetch.offsetStart,
            offsetEnd: lastFetch.offsetEnd,
            pageSize: lastFetch.pageSize,
            striptags: lastFetch.stripTags
          }
        : null
    }
  }
}

const buildAiBundle = () => {
  const t = thread.value || {}
  const ai = {
    thread: {
      title: t.title,
      forum_id: t.forum_id,
      posts: t.posts,
      rating: t.rating,
      views: t.views,
      author: { username: t.author?.username },
      last_poster: { username: t.last_poster?.username },
      first_post_time: t.first_post_time,
      last_post_time: t.last_post_time,
      has_poll: t.has_poll,
      is_locked: t.is_locked,
      is_sticky: t.is_sticky,
      // 优先给 raw，便于 AI 看上下文；如果 raw 为空就用 content
      content: (t.content_raw || t.content || '').trim(),
      poll: t.poll
        ? {
            question: t.poll.question,
            answers_count: t.poll.answers_count,
            answers: (t.poll.answers || []).map(a => ({ answer: a.answer, votes: a.votes }))
          }
        : null
    },
    posts: (posts.value || []).map(p => ({
      author: { username: p.author?.username },
      created_time: p.created_time,
      is_edited: p.is_edited,
      has_quote: p.has_quote,
      quoted_post_id: p.quoted_post_id || null,
      likes: p.likes,
      dislikes: p.dislikes,
      content: (p.content || '').trim()
    })),
    _metadata: {
      posts_fetch: posts.value?.length
        ? {
            offsetStart: lastFetch.offsetStart,
            offsetEnd: lastFetch.offsetEnd,
            pageSize: lastFetch.pageSize,
            striptags: lastFetch.stripTags
          }
        : null,
      note: '已去掉大部分与内容无关的 id/karma 等字段，适合复制给 AI 做中文总结。'
    }
  }

  const prompt =
    '你是中文内容分析助手。请基于下面提供的【论坛帖】与【回帖】数据，输出：\n' +
    '1) 先给一句话摘要\n' +
    '2) 再给 5-10 条要点（用项目符号）\n' +
    '3) 归纳主要观点分歧/共识与关键证据\n' +
    '4) 如果有投票，解释投票问题、各选项票数与可能含义\n' +
    '5) 列出最有价值的 3-5 条回帖（说明原因）\n' +
    '6) 最后给一个“适合转发”的中文短总结（<=120字）\n' +
    '注意：不要编造不存在的信息，引用时请标注是“首帖”还是“回帖”。\n\n'

  return {
    prompt,
    data: ai
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
  if (!thread.value) return
  const bundle = buildRawBundle()
  const threadId = normalizeThreadId() || 'thread'
  const filename = `forum_thread_${threadId}_${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}.json`
  downloadTextFile(filename, JSON.stringify(bundle, null, 2))
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
  if (!thread.value) return
  await copyToClipboard(JSON.stringify(buildRawBundle(), null, 2))
}

const copyAiSummaryPackToClipboard = async () => {
  if (!thread.value) return
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

.progress-box {
  width: 100%;
}

.progress-text {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
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

.content-pre {
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
  max-height: 320px;
  overflow: auto;
}

.post-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.poll-section {
  margin-top: 10px;
}

.poll-question {
  font-weight: 600;
  margin-bottom: 8px;
}
</style>


