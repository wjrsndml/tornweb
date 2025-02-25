<template>
  <div class="container">
    <el-card class="input-card">
      <template #header>
        <div class="card-header">
          <h2>Torn RW 分析器</h2>
        </div>
      </template>
      
      <el-form :model="form" label-width="120px">
        <el-form-item label="API Key">
          <el-input v-model="form.apiKey" placeholder="请输入您的Torn API Key" show-password />
        </el-form-item>
        <el-form-item label="RW War ID">
          <el-input v-model="form.warId" placeholder="请输入RW War ID" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="analyzeWar" :loading="loading">分析</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="warData" class="result-card">
      <template #header>
        <div class="card-header">
          <h3>战争分析结果</h3>
        </div>
      </template>
      
      <div class="war-info">
        <h4>基本信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="战争状态">{{ warData.status }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(warData.start) }}</el-descriptions-item>
        </el-descriptions>

        <div class="faction-details" v-for="faction in warData.factions" :key="faction.id">
          <h4>{{ faction.name }}</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="得分">{{ faction.score }}</el-descriptions-item>
            <el-descriptions-item label="Caches收益明细">
              <div v-if="faction.caches">
                <div v-if="faction.caches.small.quantity > 0">
                  Small Arms Cache: {{ faction.caches.small.quantity }}个 ({{ formatNumber(faction.caches.small.value) }}$)
                </div>
                <div v-if="faction.caches.medium.quantity > 0">
                  Medium Arms Cache: {{ faction.caches.medium.quantity }}个 ({{ formatNumber(faction.caches.medium.value) }}$)
                </div>
                <div v-if="faction.caches.heavy.quantity > 0">
                  Heavy Arms Cache: {{ faction.caches.heavy.quantity }}个 ({{ formatNumber(faction.caches.heavy.value) }}$)
                </div>
                <div v-if="faction.caches.armor.quantity > 0">
                  Armor Cache: {{ faction.caches.armor.quantity }}个 ({{ formatNumber(faction.caches.armor.value) }}$)
                </div>
                <div>总计: {{ formatNumber(faction.cacheValue) }}$</div>
              </div>
              <div v-else>无</div>
            </el-descriptions-item>
            <el-descriptions-item label="Points收益">
              {{ formatNumber(faction.pointsValue) }} $
            </el-descriptions-item>
            <el-descriptions-item label="总收益">
              {{ formatNumber(faction.totalValue) }} $
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <el-card v-if="error" class="error-card">
      <template #header>
        <div class="card-header">
          <h3>错误信息</h3>
        </div>
      </template>
      <p class="error-message">{{ error }}</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const form = reactive({
  apiKey: '',
  warId: ''
})

const loading = ref(false)
const error = ref(null)
const warData = ref(null)

const formatDate = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const formatNumber = (num) => {
  return new Intl.NumberFormat().format(num)
}

const analyzeWar = async () => {
  if (!form.apiKey || !form.warId) {
    error.value = '请填写API Key和War ID'
    return
  }

  loading.value = true
  error.value = null
  warData.value = null

  try {
    // 获取RW信息
    const warResponse = await axios.get(
      `https://api.torn.com/v2/faction/${form.warId}/rankedwarreport?key=${form.apiKey}`
    )

    // 获取物品价格信息
    const itemsResponse = await axios.get(
      `https://api.torn.com/v2/torn/items?cat=Supply%20Pack&sort=ASC&key=${form.apiKey}`
    )

    // 获取points市场价格信息
    const pointsResponse = await axios.get(
      `https://api.torn.com/v2/market?selections=pointsmarket&sort=DESC&key=${form.apiKey}`
    )

    const warInfo = warResponse.data.rankedwarreport
    const itemPrices = itemsResponse.data.items
    
    // 获取最低points价格
    const pointsMarket = pointsResponse.data.pointsmarket
    const lowestPointPrice = Object.values(pointsMarket)
      .sort((a, b) => a.cost - b.cost)[0]?.cost || 45000 // 如果获取失败则默认45k

    const processedData = {
      status: warInfo.status || '进行中',
      start: warInfo.start,
      factions: []
    }

    for (const faction of warInfo.factions) {
      let cacheValue = 0
      const caches = {
        small: { id: 1120, quantity: 0, value: 0 },
        medium: { id: 1121, quantity: 0, value: 0 },
        heavy: { id: 1122, quantity: 0, value: 0 },
        armor: { id: 1118, quantity: 0, value: 0 },
        melee: { id: 1119, quantity: 0, value: 0 }
      }

      if (faction.rewards && faction.rewards.items) {
        for (const item of faction.rewards.items) {
          const itemPrice = Object.values(itemPrices).find(i => i.id === item.id)?.value?.market_price || 0
          if (item.id === caches.small.id) {
            caches.small.quantity = item.quantity
            caches.small.value = itemPrice * item.quantity
          } else if (item.id === caches.medium.id) {
            caches.medium.quantity = item.quantity
            caches.medium.value = itemPrice * item.quantity
          } else if (item.id === caches.heavy.id) {
            caches.heavy.quantity = item.quantity
            caches.heavy.value = itemPrice * item.quantity
          } else if (item.id === caches.armor.id) {
            caches.armor.quantity = item.quantity
            caches.armor.value = itemPrice * item.quantity
          } else if (item.id === caches.melee.id) {
            caches.melee.quantity = item.quantity
            caches.melee.value = itemPrice * item.quantity
          }
        }
        cacheValue = Object.values(caches).reduce((total, cache) => total + cache.value, 0)
      }
      
      const pointsValue = (faction.rewards?.points || 0) * lowestPointPrice

      processedData.factions.push({
        id: faction.id,
        name: faction.name,
        score: faction.score,
        caches: caches,
        cacheValue: cacheValue,
        pointsValue: pointsValue,
        totalValue: cacheValue + pointsValue
      })
    }

    warData.value = processedData
  } catch (e) {
    error.value = e.response?.data?.error || '获取数据失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.input-card,
.result-card,
.error-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.faction-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.error-message {
  color: #f56c6c;
}

h2, h3, h4 {
  margin: 0;
  color: #303133;
}
</style>