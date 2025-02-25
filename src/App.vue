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
        
        <div class="price-settings">
          <h4>价格设置</h4>
          <el-form :model="priceSettings" label-width="180px">
            <el-form-item label="Small Arms Cache 价格">
              <el-input-number v-model="priceSettings.small" :min="0" @change="recalculateValues" />
            </el-form-item>
            <el-form-item label="Medium Arms Cache 价格">
              <el-input-number v-model="priceSettings.medium" :min="0" @change="recalculateValues" />
            </el-form-item>
            <el-form-item label="Heavy Arms Cache 价格">
              <el-input-number v-model="priceSettings.heavy" :min="0" @change="recalculateValues" />
            </el-form-item>
            <el-form-item label="Armor Cache 价格">
              <el-input-number v-model="priceSettings.armor" :min="0" @change="recalculateValues" />
            </el-form-item>
            <el-form-item label="Melee Cache 价格">
              <el-input-number v-model="priceSettings.melee" :min="0" @change="recalculateValues" />
            </el-form-item>
            <el-form-item label="Points 价格">
              <el-input-number v-model="priceSettings.points" :min="0" @change="recalculateValues" />
            </el-form-item>
          </el-form>
        </div>
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
                <div v-if="faction.caches.melee.quantity > 0">
                  Melee Cache: {{ faction.caches.melee.quantity }}个 ({{ formatNumber(faction.caches.melee.value) }}$)
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
const priceSettings = reactive({
  small: 0,
  medium: 0,
  heavy: 0,
  armor: 0,
  melee: 0,
  points: 0 // Will be updated in analyzeWar
})

const recalculateValues = () => {
  if (!warData.value) return;

  for (const faction of warData.value.factions) {
    let cacheValue = 0;
    
    // 重新计算每种cache的价值
    if (faction.caches) {
      faction.caches.small.value = faction.caches.small.quantity * priceSettings.small;
      faction.caches.medium.value = faction.caches.medium.quantity * priceSettings.medium;
      faction.caches.heavy.value = faction.caches.heavy.quantity * priceSettings.heavy;
      faction.caches.armor.value = faction.caches.armor.quantity * priceSettings.armor;
      faction.caches.melee.value = faction.caches.melee.quantity * priceSettings.melee;
      
      // 更新总cache价值
      cacheValue = Object.values(faction.caches).reduce((total, cache) => total + cache.value, 0);
    }
    
    // 更新points价值
    const pointsValue = (faction.rewards?.points || 0) * priceSettings.points;
    
    // 更新faction的价值数据
    faction.cacheValue = cacheValue;
    faction.pointsValue = pointsValue;
    faction.totalValue = cacheValue + pointsValue;
  }
}
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
  if (!warData.value || warData.value.factions.length !== 2) return;

  const faction1 = warData.value.factions[0];
  const faction2 = warData.value.factions[1];
  const totalValue = faction1.totalValue + faction2.totalValue;

  // 计算各派系目标金额
  const targetValue1 = totalValue * (splitForm.faction1Ratio / 100);
  const targetValue2 = totalValue * (splitForm.faction2Ratio / 100);

  // 当前 faction1 的比例
  const currentRatio1 = (faction1.totalValue / totalValue) * 100;

  splitResult.value = { transfers: [] };

  // 如果当前比例已经符合目标比例，则无需转移
  if (Math.abs(currentRatio1 - splitForm.faction1Ratio) < 0.1) return;

  // 确定转移方向：当 faction1 的价值超过目标时，从 faction1 转给 faction2，反之亦然
  let fromFaction, toFaction, targetValue;
  if (currentRatio1 > splitForm.faction1Ratio) {
    fromFaction = faction1;
    toFaction = faction2;
    targetValue = targetValue1; // fromFaction 需要降低到 targetValue
  } else {
    fromFaction = faction2;
    toFaction = faction1;
    targetValue = targetValue2;
  }

  // 定义 caches 顺序及名称（这里顺序可以根据需要调整）
  const cacheTypes = [
    { type: 'heavy', name: 'Heavy Arms Cache' },
    { type: 'medium', name: 'Medium Arms Cache' },
    { type: 'small', name: 'Small Arms Cache' },
    { type: 'armor', name: 'Armor Cache' },
    { type: 'melee', name: 'Melee Cache' }
  ];

  // 构建 caches 数组，每项包含：type、name、可转移数量（available）和单价（unitValue）
  // 假设 fromFaction.caches 对应的格式为：{ heavy: { quantity, value }, ... }
  const caches = cacheTypes.map(cacheType => {
    const data = fromFaction.caches[cacheType.type];
    // 计算单个 cache 的价值（假设 data.value 是该类型 cache 的总价值）
    const unitValue = data.quantity > 0 ? (data.value / data.quantity) : 0;
    return {
      type: cacheType.type,
      name: cacheType.name,
      available: data.quantity,
      unitValue: unitValue
    };
  });

  // fromTotal 为转出派系初始的 caches 总价值
  const fromTotal = fromFaction.totalValue;
  const n = caches.length;

  // memo 用于保存状态搜索结果，key 为状态数组（用逗号连接）的字符串
  const memo = new Map();

  /**
   * dp(state)
   * @param {number[]} state - 长度为 n 的数组，表示每种 cache 已转移的数量
   * @returns {object} { cash, state } 其中 cash 为剩余需要用现金补偿的金额
   */
  const dp = (state) => {
    const stateKey = state.join(',');
    if (memo.has(stateKey)) return memo.get(stateKey);

    // 计算已转移 caches 的总价值
    let transferredValue = 0;
    for (let i = 0; i < n; i++) {
      transferredValue += state[i] * caches[i].unitValue;
    }
    // 当前 fromFaction 剩余价值
    const currentValue = fromTotal - transferredValue;
    // diff 为超出目标值的部分
    const diff = currentValue - targetValue;

    // 如果已经达到或低于目标（误差范围内），则现金补偿为 0
    if (diff <= 1e-6) {
      const res = { cash: 0, state: state };
      memo.set(stateKey, res);
      return res;
    }

    // 找出还有剩余可转移的 cache 类型
    let availableIndices = [];
    for (let i = 0; i < n; i++) {
      if (state[i] < caches[i].available) {
        availableIndices.push(i);
      }
    }
    // 若无可转移 cache，则只能用现金补齐剩余差额
    if (availableIndices.length === 0) {
      const res = { cash: diff, state: state };
      memo.set(stateKey, res);
      return res;
    }

    // 如果剩余 diff 小于所有可转移 cache 中最小的单价，则再转移一件会“过补”，此时直接用现金结算
    let minAvailable = Infinity;
    for (const i of availableIndices) {
      if (caches[i].unitValue < minAvailable) {
        minAvailable = caches[i].unitValue;
      }
    }
    if (diff < minAvailable) {
      const res = { cash: diff, state: state };
      memo.set(stateKey, res);
      return res;
    }

    // 尝试对每个可转移类型增加一件 cache，然后递归求解，选取现金补偿最小的方案
    let best = { cash: Infinity, state: null };
    for (const i of availableIndices) {
      if (diff >= caches[i].unitValue) {
        let newState = state.slice();
        newState[i] += 1;
        const candidate = dp(newState);
        if (candidate.cash < best.cash) {
          best = { cash: candidate.cash, state: candidate.state };
        }
      }
    }
    memo.set(stateKey, best);
    return best;
  };

  // 初始状态：各类型 cache 均未转移
  const initState = Array(n).fill(0);
  const optimal = dp(initState);

  // 构造转移结果对象
  const transfer = {
    from: fromFaction.name,
    to: toFaction.name,
    caches: [],
    cash: 0
  };

  // 若某种 cache 有转移，则加入结果中
  for (let i = 0; i < n; i++) {
    if (optimal.state[i] > 0) {
      transfer.caches.push({
        type: caches[i].type,
        name: caches[i].name,
        quantity: optimal.state[i]
      });
    }
  }
  // dp 返回的 cash 为补差金额，按需要取整（这里用 Math.ceil，可根据业务需求调整）
  transfer.cash = Math.ceil(optimal.cash);

  splitResult.value.transfers.push(transfer);
};


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
    
    // 设置默认价格
    priceSettings.small = Object.values(itemPrices).find(i => i.id === 1120)?.value?.market_price || 0
    priceSettings.medium = Object.values(itemPrices).find(i => i.id === 1121)?.value?.market_price || 0
    priceSettings.heavy = Object.values(itemPrices).find(i => i.id === 1122)?.value?.market_price || 0
    priceSettings.armor = Object.values(itemPrices).find(i => i.id === 1118)?.value?.market_price || 0
    priceSettings.melee = Object.values(itemPrices).find(i => i.id === 1119)?.value?.market_price || 0

    // 获取最低points价格
    const pointsMarket = pointsResponse.data.pointsmarket
    const lowestPointPrice = Object.values(pointsMarket)
      .sort((a, b) => a.cost - b.cost)[0]?.cost || 45000 // 如果获取失败则默认45k

    // 设置 points 默认价格
    priceSettings.points = lowestPointPrice;

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

.price-settings .el-input-number {
  width: 100%; /* Increase width by 100% (double the default) */
}

.error-message {
  color: #f56c6c;
}

h2, h3, h4 {
  margin: 0;
  color: #303133;
}
</style>
