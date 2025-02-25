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

    <el-card v-if="warData && warData.factions.length === 2" class="reward-split-card">
      <template #header>
        <div class="card-header">
          <h3>奖励划分</h3>
        </div>
      </template>
      
      <el-form :model="splitForm" label-width="120px">
        <el-form-item :label="warData.factions[0].name + ' 比例'">
          <el-input-number 
            v-model="splitForm.faction1Ratio" 
            :min="0" 
            :max="100" 
            @change="handleRatioChange(0)"
          />
        </el-form-item>
        <el-form-item :label="warData.factions[1].name + ' 比例'">
          <el-input-number 
            v-model="splitForm.faction2Ratio" 
            :min="0" 
            :max="100" 
            @change="handleRatioChange(1)"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="calculateSplit" :disabled="!isValidRatio">划分奖励</el-button>
        </el-form-item>
      </el-form>

      <div v-if="splitResult" class="split-result">
        <h4>划分结果</h4>
        <div v-if="splitResult.transfers.length > 0">
          <div v-for="(transfer, index) in splitResult.transfers" :key="index" class="transfer-item">
            <p>{{ transfer.from }} 需要转移给 {{ transfer.to }}:</p>
            <template v-if="transfer.caches">
              <div v-for="cache in transfer.caches" :key="cache.type">
                {{ cache.name }}: {{ cache.quantity }}个
              </div>
            </template>
            <div v-if="transfer.cash > 0">现金: {{ formatNumber(transfer.cash) }}$</div>
          </div>
        </div>
        <div v-else>
          <p>当前奖励分配已经符合目标比例，无需转移</p>
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
import { ref, reactive, computed } from 'vue'
import axios from 'axios'

const form = reactive({
  apiKey: '',
  warId: ''
})

const splitForm = reactive({
  faction1Ratio: 50,
  faction2Ratio: 50
})

const loading = ref(false)
const error = ref(null)
const warData = ref(null)
const splitResult = ref(null)

const isValidRatio = computed(() => {
  return splitForm.faction1Ratio + splitForm.faction2Ratio === 100
})

const formatDate = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const formatNumber = (num) => {
  return new Intl.NumberFormat().format(num)
}

const handleRatioChange = (factionIndex) => {
  if (factionIndex === 0) {
    splitForm.faction2Ratio = 100 - splitForm.faction1Ratio
  } else {
    splitForm.faction1Ratio = 100 - splitForm.faction2Ratio
  }
}

const calculateSplit = () => {
  if (!warData.value || warData.value.factions.length !== 2) return

  const faction1 = warData.value.factions[0]
  const faction2 = warData.value.factions[1]
  const totalValue = faction1.totalValue + faction2.totalValue

  // 计算目标金额
  const targetValue1 = totalValue * (splitForm.faction1Ratio / 100)
  const targetValue2 = totalValue * (splitForm.faction2Ratio / 100)

  // 计算当前比例
  const currentRatio1 = (faction1.totalValue / totalValue) * 100

  splitResult.value = {
    transfers: []
  }

  // 如果当前比例已经符合目标比例，无需转移
  if (Math.abs(currentRatio1 - splitForm.faction1Ratio) < 0.1) return

  // 确定需要转移的方向
  const [fromFaction, toFaction, transferAmount] = currentRatio1 > splitForm.faction1Ratio
    ? [faction1, faction2, faction1.totalValue - targetValue1]
    : [faction2, faction1, faction2.totalValue - targetValue2]

  const transfer = {
    from: fromFaction.name,
    to: toFaction.name,
    caches: [],
    cash: 0
  }

  let remainingAmount = transferAmount

  // 优先使用缓存转移
  const cacheTypes = [
    { type: 'heavy', name: 'Heavy Arms Cache' },
    { type: 'medium', name: 'Medium Arms Cache' },
    { type: 'small', name: 'Small Arms Cache' },
    { type: 'armor', name: 'Armor Cache' },
    { type: 'melee', name: 'Melee Cache' }
  ]

  for (const cacheType of cacheTypes) {
    const cache = fromFaction.caches[cacheType.type]
    if (cache.quantity > 0 && remainingAmount > 0) {
      const cacheValue = cache.value / cache.quantity
      const maxCaches = Math.min(
        cache.quantity,
        Math.floor(remainingAmount / cacheValue)
      )

      if (maxCaches > 0) {
        transfer.caches.push({
          type: cacheType.type,
          name: cacheType.name,
          quantity: maxCaches
        })
        remainingAmount -= maxCaches * cacheValue
      }
    }
  }

  // 剩余金额用现金补齐
  if (remainingAmount > 0) {
    transfer.cash = Math.ceil(remainingAmount)
  }

  splitResult.value.transfers.push(transfer)
}

const analyzeWar = async () => {
  if (!form.apiKey || !form.warId) {
    error.value = '请填写API Key和War ID'
    return
  }

  loading.value = true
  error.value = null
  warData.value = null
  splitResult.value = null

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
.error-card,
.reward-split-card {
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