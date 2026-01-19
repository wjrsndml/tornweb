<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <el-aside class="sidebar" width="280px">
      <div class="sidebar-header">
        <h1>Torn RW 工具箱</h1>
      </div>
      
      <!-- API Key 输入 -->
      <div class="api-key-section">
        <el-form label-position="top">
          <el-form-item label="API Key">
            <el-input 
              v-model="globalApiKey" 
              placeholder="请输入您的Torn API Key" 
              show-password 
              size="small"
            />
          </el-form-item>
          <div class="api-key-actions">
            <el-switch v-model="rememberApiKey" />
            <span class="api-key-hint">记住 API Key（仅保存在本地浏览器）</span>
            <el-button size="small" @click="clearRememberedApiKey">清除已记住</el-button>
          </div>
        </el-form>
      </div>

      <!-- 导航菜单 -->
      <el-menu 
        :default-active="activeMenu" 
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="split">
          <el-icon><Box /></el-icon>
          <span>RW 分箱器</span>
        </el-menu-item>
        <el-menu-item index="attacks">
          <el-icon><Operation /></el-icon>
          <span>RW 丢分分析</span>
        </el-menu-item>
        <el-menu-item index="chains">
          <el-icon><Link /></el-icon>
          <span>Chain 查看器</span>
        </el-menu-item>
        <el-menu-item index="comparison">
          <el-icon><DataAnalysis /></el-icon>
          <span>帮派实力对比</span>
        </el-menu-item>
        <el-menu-item index="tempweapons">
          <el-icon><Operation /></el-icon>
          <span>临时武器统计</span>
        </el-menu-item>
        <el-menu-item index="oc">
          <el-icon><Operation /></el-icon>
          <span>帮派 OC 推荐</span>
        </el-menu-item>
        <el-menu-item index="grabber">
          <el-icon><Download /></el-icon>
          <span>攻击记录抓取</span>
        </el-menu-item>
        <el-menu-item index="forum">
          <el-icon><Document /></el-icon>
          <span>论坛帖子抓取</span>
        </el-menu-item>
        <el-menu-item index="userforum">
          <el-icon><User /></el-icon>
          <span>个人论坛回帖抓取</span>
        </el-menu-item>
        <el-menu-item index="oc_simulator">
          <el-icon><DataLine /></el-icon>
          <span>OC 模拟器</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区域 -->
    <el-main class="main-content">
      <!-- RW 分箱器 -->
      <div v-if="activeMenu === 'split'" class="content-section">
        <el-card class="function-card">
          <template #header>
            <div class="card-header">
              <h2>Torn RW 分箱器</h2>
            </div>
          </template>
          <p>给假赛计算按比例分箱子的最小现金方案</p>
          <el-form :model="form" label-width="120px">
            <el-form-item label="RW War ID">
              <el-input v-model="form.warId" placeholder="请输入RW War ID" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="analyzeWar" :loading="loading" :disabled="!globalApiKey">
                分析
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 分析结果 -->
          <div v-if="warData" class="war-results">
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

            <!-- 奖励划分 -->
            <div v-if="warData.factions.length === 2" class="reward-split">
              <h4>奖励划分</h4>
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
            </div>
          </div>

          <!-- 错误信息 -->
          <el-alert 
            v-if="error" 
            :title="error" 
            type="error" 
            show-icon
            style="margin-top: 20px"
          />
        </el-card>
      </div>

      <!-- RW 丢分分析 -->
      <div v-if="activeMenu === 'attacks'" class="content-section">
        <el-card class="function-card">
          <template #header>
            <div class="card-header">
              <h2>RW丢分分析</h2>
            </div>
          </template>
          <p>根据目前的住院情况，计算RW双方各自无缝被刷会丢多少分。（注：这里只能计算你自己帮派正在进行的RW！）</p>
          
          <el-form>
            <el-form-item>
              <el-button type="primary" @click="fetchAttackData" :loading="attacksLoading" :disabled="!globalApiKey">
                获取当前战争数据
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="attacksData">
            <el-alert 
              title="数据获取成功" 
              type="success" 
              :closable="false" 
              style="margin-bottom: 20px"
            >
              <template #default>
                <p>我方帮派: {{ attacksData.ourFaction.name }}</p>
                <p>对方帮派: {{ attacksData.opponentFaction.name }}</p>
                <p>战争开始时间: {{ formatDate(attacksData.startTimestamp) }}</p>
                <p>攻击记录数: {{ attacksData.attacksCount }}</p>
              </template>
            </el-alert>
            
            <el-divider content-position="center">预测计算</el-divider>
            
            <el-form :model="hoursForm" label-width="180px">
              <el-form-item label="预测多少小时后">
                <el-input-number v-model="hoursForm.hours" :min="0" :precision="1" :step="0.5" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="calculateAttackPotential">计算预测</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div v-if="attacksLoading && !attacksData">
            <el-progress 
              :percentage="100" 
              status="active" 
              :indeterminate="true" 
              :duration="3" 
              :stroke-width="15"
              style="margin: 20px 0"
            />
            <p class="load-message">{{ attacksError || '正在获取数据，请耐心等待...' }}</p>
          </div>

          <div v-if="attacksResult" class="attacks-result">
            <el-divider content-position="center">预测结果</el-divider>
            
            <el-descriptions title="我方帮派" :column="1" border>
              <el-descriptions-item label="总丢分">{{ attacksResult.ourFactionTotalLoss.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="成员详情">
                <el-table :data="attacksResult.ourMembers" stripe style="width: 100%">
                  <el-table-column prop="name" label="成员" width="150" />
                  <el-table-column prop="status" label="状态" width="100" />
                  <el-table-column prop="attackCount" label="可被攻击次数" width="130" />
                  <el-table-column prop="avgRespect" label="平均丢分" width="130" />
                  <el-table-column prop="totalLoss" label="总丢分" width="100" />
                </el-table>
              </el-descriptions-item>
            </el-descriptions>
            
            <el-descriptions style="margin-top: 20px" title="对方帮派" :column="1" border>
              <el-descriptions-item label="总丢分">{{ attacksResult.opponentFactionTotalLoss.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="成员详情">
                <el-table :data="attacksResult.opponentMembers" stripe style="width: 100%">
                  <el-table-column prop="name" label="成员" width="150" />
                  <el-table-column prop="status" label="状态" width="100" />
                  <el-table-column prop="attackCount" label="可被攻击次数" width="130" />
                  <el-table-column prop="avgRespect" label="平均丢分" width="130" />
                  <el-table-column prop="totalLoss" label="总丢分" width="100" />
                </el-table>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <el-alert 
            v-if="attacksError" 
            :title="attacksError" 
            type="error" 
            show-icon
            style="margin-top: 20px"
          />
        </el-card>
      </div>

      <!-- Chain 查看器 -->
      <div v-if="activeMenu === 'chains'" class="content-section">
        <ChainAnalyzer :api-key="globalApiKey" />
      </div>
      
      <!-- 帮派实力对比 -->
      <div v-if="activeMenu === 'comparison'" class="content-section">
        <FactionComparison />
      </div>

      <!-- 临时武器统计 -->
      <div v-if="activeMenu === 'tempweapons'" class="content-section">
        <TempWeaponStats :api-key="globalApiKey" />
      </div>

      <!-- 帮派 OC 状态 -->
      <div v-if="activeMenu === 'oc'" class="content-section">
        <FactionOcStatus :api-key="globalApiKey" />
      </div>

      <!-- 攻击记录抓取 -->
      <div v-if="activeMenu === 'grabber'" class="content-section">
        <FactionAttacksGrabber :api-key="globalApiKey" />
      </div>

      <!-- 论坛帖子抓取 -->
      <div v-if="activeMenu === 'forum'" class="content-section">
        <ForumThreadGrabber :api-key="globalApiKey" />
      </div>

      <!-- 个人论坛回帖抓取 -->
      <div v-if="activeMenu === 'userforum'" class="content-section">
        <UserForumPostsGrabber :api-key="globalApiKey" />
      </div>

      <!-- OC 模拟器 -->
      <div v-if="activeMenu === 'oc_simulator'" class="content-section">
        <OcSimulator :api-key="globalApiKey" />
      </div>
    </el-main>
  </div>
</template>

<script setup>
// App.vue
// 作用：应用主入口与侧边栏导航；提供全局 API Key 输入，并将 API Key 传递给各功能组件；并在刷新/重开后恢复上一次使用的功能页。
// 修改记录：
// - 2025-12-27: 增加“记住 API Key（localStorage）”与一键清除功能。
// - 2025-12-27: 增加“帮派 OC 推荐”功能入口。
// - 2025-12-27: 增加“页面记忆”功能：刷新/重开后自动恢复上一次选择的菜单。
import { ref, reactive, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import ChainAnalyzer from './components/ChainAnalyzer.vue'
import FactionComparison from './components/FactionComparison.vue'
import TempWeaponStats from './components/TempWeaponStats.vue'
import FactionOcStatus from './components/FactionOcStatus.vue'
import FactionAttacksGrabber from './components/FactionAttacksGrabber.vue'
import ForumThreadGrabber from './components/ForumThreadGrabber.vue'
import UserForumPostsGrabber from './components/UserForumPostsGrabber.vue'
import OcSimulator from './components/OcSimulator.vue'
import { Box, Operation, Link, DataAnalysis, Download, Document, User, DataLine } from '@element-plus/icons-vue'
import {
  clearStoredApiKey,
  getRememberApiKeyEnabled,
  getStoredApiKey,
  setRememberApiKeyEnabled,
  setStoredApiKey
} from './utils/apiKeyStorage'
import { getStoredActiveMenu, setStoredActiveMenu } from './utils/pageStateStorage'

// 全局状态
const globalApiKey = ref('')
const rememberApiKey = ref(true)
const ALLOWED_MENUS = new Set([
  'split',
  'attacks',
  'chains',
  'comparison',
  'tempweapons',
  'oc',
  'grabber',
  'forum',
  'userforum',
  'oc_simulator'
])

const normalizeActiveMenu = (menu) => {
  const v = String(menu || '').trim()
  return ALLOWED_MENUS.has(v) ? v : 'split'
}

// 页面记忆：初始化时就从 localStorage 恢复，避免先闪到默认页再切回
const activeMenu = ref(normalizeActiveMenu(getStoredActiveMenu('split')))

onMounted(() => {
  rememberApiKey.value = getRememberApiKeyEnabled(true)
  if (rememberApiKey.value) {
    const saved = getStoredApiKey()
    if (saved) globalApiKey.value = saved
  }
})

// 页面记忆：切换菜单时持久化
watch(activeMenu, (v) => {
  setStoredActiveMenu(normalizeActiveMenu(v))
})

watch(globalApiKey, (v) => {
  if (!rememberApiKey.value) return
  setStoredApiKey(v)
})

watch(rememberApiKey, (v) => {
  setRememberApiKeyEnabled(Boolean(v))
  if (!v) {
    clearStoredApiKey()
    globalApiKey.value = ''
  } else {
    setStoredApiKey(globalApiKey.value)
  }
})

const clearRememberedApiKey = () => {
  clearStoredApiKey()
  globalApiKey.value = ''
}

// 原有的状态变量
const form = reactive({
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
  points: 0
})

// 攻击分析相关变量
const hoursForm = reactive({
  hours: 1
})

const attacksLoading = ref(false)
const attacksError = ref(null)
const attacksData = ref(null)
const attacksResult = ref(null)

// 菜单选择处理
const handleMenuSelect = (index) => {
  activeMenu.value = normalizeActiveMenu(index)
  // 清除之前的错误信息
  error.value = null
  attacksError.value = null
}

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
    
    // 更新points价值 - 修复：直接使用faction.pointsCount而非尝试访问faction.rewards
    const pointsValue = (faction.pointsCount || 0) * priceSettings.points;
    
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

  // 计算帮派目标金额
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

  // fromTotal 为转出帮派初始的 caches 总价值
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

    // 如果剩余 diff 小于所有可转移 cache 中最小的单价，则再转移一件会"过补"，此时直接用现金结算
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
  if (!globalApiKey.value || !form.warId) {
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
      `https://api.torn.com/v2/faction/${form.warId}/rankedwarreport?key=${globalApiKey.value}`
    )
    // 获取物品价格信息
    const itemsResponse = await axios.get(
      `https://api.torn.com/v2/torn/items?cat=Supply%20Pack&sort=ASC&key=${globalApiKey.value}`
    )
    // 获取points市场价格信息
    const pointsResponse = await axios.get(
      `https://api.torn.com/v2/market?selections=pointsmarket&sort=DESC&key=${globalApiKey.value}`
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
      
      // 保存points数量，用于后续价格重新计算
      const pointsCount = faction.rewards?.points || 0
      const pointsValue = pointsCount * lowestPointPrice
    
      processedData.factions.push({
        id: faction.id,
        name: faction.name,
        score: faction.score,
        caches: caches,
        cacheValue: cacheValue,
        pointsValue: pointsValue,
        pointsCount: pointsCount, // 新增：保存points数量
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

// 获取战争攻击数据
const fetchAttackData = async () => {
  if (!globalApiKey.value) {
    attacksError.value = '请填写API Key'
    return
  }
  
  attacksLoading.value = true
  attacksError.value = null
  attacksData.value = null
  attacksResult.value = null
  
  try {
    // 1. 获取用户信息，确定用户当前帮派
    const userResponse = await axios.get(
      `https://api.torn.com/v2/user?key=${globalApiKey.value}`
    )
    
    const userData = userResponse.data.profile
    const userFactionId = userData.faction_id
    
    if (!userFactionId) {
      attacksError.value = '您当前没有加入帮派'
      return
    }
    
    // 2. 获取最新的ranked war
    const rankedWarsResponse = await axios.get(
      `https://api.torn.com/v2/faction/${userFactionId}/rankedwars?key=${globalApiKey.value}`
    )
    
    const rankedWarsData = rankedWarsResponse.data
    
    if (!rankedWarsData || !rankedWarsData.rankedwars) {
      attacksError.value = '未找到ranked wars数据'
      return
    }
    
    // 按开始时间排序，获取最新的ranked war
    const rankedWars = Object.values(rankedWarsData.rankedwars).sort((a, b) => b.start - a.start)
    
    if (!rankedWars.length) {
      attacksError.value = '未找到任何ranked war记录'
      return
    }
    
    const latestRankedWar = rankedWars[0]
    
    // 检查最新的ranked war是否正在进行中
    if (latestRankedWar.winner !== null) {
      attacksError.value = '当前没有正在进行的ranked war'
      return
    }
    
    const startTimestamp = latestRankedWar.start
    const factionIds = [latestRankedWar.factions[0].id, latestRankedWar.factions[1].id]
    const opponentFactionId = factionIds[0] !== userFactionId ? factionIds[0] : factionIds[1]
    
    // 3. 获取双方帮派成员
    const ourFactionResponse = await axios.get(
      `https://api.torn.com/v2/faction/${userFactionId}/members?key=${globalApiKey.value}`
    )
    
    const opponentFactionResponse = await axios.get(
      `https://api.torn.com/v2/faction/${opponentFactionId}/members?key=${globalApiKey.value}`
    )
    
    const ourFactionMembers = ourFactionResponse.data.members
    const opponentFactionMembers = opponentFactionResponse.data.members
    
    // 4. 分页获取所有攻击记录
    const allAttacks = []
    let currentTimestamp = startTimestamp
    let hasMore = true
    
    while (hasMore) {
      try {
        // 为避免API限流，每次请求间隔1秒
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 进度提示
        attacksLoading.value = true
        attacksError.value = `正在获取从 ${formatDate(currentTimestamp)} 开始的攻击记录...`
        
        const attacksResponse = await axios.get(
          `https://api.torn.com/v2/faction/attacksfull?from=${currentTimestamp}&sort=ASC&key=${globalApiKey.value}`
        )
        
        const attacks = Object.values(attacksResponse.data.attacks || {})
        
        if (attacks.length === 0) {
          hasMore = false
          break
        }
        
        allAttacks.push(...attacks)
        
        // 获取最后一条记录的时间戳作为下一次查询的起始时间
        const lastAttackTimestamp = Math.max(...attacks.map(attack => parseInt(attack.started)))
        
        // 如果最后一条记录的时间戳没有变化，说明没有更多数据了
        if (lastAttackTimestamp <= currentTimestamp) {
          hasMore = false
        } else {
          currentTimestamp = lastAttackTimestamp
        }
        
        // 更新进度提示
        attacksError.value = `已获取 ${allAttacks.length} 条攻击记录...`
      } catch (e) {
        attacksError.value = e.response?.data?.error?.error || '获取攻击记录失败'
        break
      }
    }
    
    // 5. 存储数据
    attacksData.value = {
      startTimestamp,
      ourFaction: {
        id: userFactionId,
        name: latestRankedWar.factions.find(f => f.id === userFactionId)?.name || '我方帮派'
      },
      opponentFaction: {
        id: opponentFactionId,
        name: latestRankedWar.factions.find(f => f.id === opponentFactionId)?.name || '对方帮派'
      },
      ourMembers: ourFactionMembers,
      opponentMembers: opponentFactionMembers,
      attacks: allAttacks,
      attacksCount: allAttacks.length
    }
    
    attacksError.value = null
  } catch (e) {
    attacksError.value = e.response?.data?.error?.error || '获取数据失败'
  } finally {
    attacksLoading.value = false
  }
}

// 计算攻击潜力
const calculateAttackPotential = () => {
  if (!attacksData.value) return
  
  const { 
    ourFaction, 
    opponentFaction, 
    ourMembers, 
    opponentMembers, 
    attacks, 
    startTimestamp 
  } = attacksData.value
  
  // 计算目标时间戳
  const currentTimestamp = Math.floor(Date.now() / 1000)
  const hoursInSeconds = hoursForm.hours * 3600
  const checkTimestamp = currentTimestamp + hoursInSeconds
  
  // 计算每个成员的被攻击次数和平均丢分
  const ourMembersResult = []
  const opponentMembersResult = []
  let ourFactionTotalLoss = 0
  let opponentFactionTotalLoss = 0
  
  // 处理我方成员
  for (const [iter, member] of Object.entries(ourMembers)) {
    const memberId = member.id
    const status = member.status?.state || 'Unknown'
    const untilTimestamp = member.status?.until
    
    const attackCount = calculateMemberAttackPotential(status, untilTimestamp, checkTimestamp)
    const avgRespect = calculateAverageRespect(attacks, memberId, opponentFaction.id)
    const totalLoss = attackCount * avgRespect
    
    ourFactionTotalLoss += totalLoss
    
    ourMembersResult.push({
      id: memberId,
      name: member.name,
      status,
      attackCount,
      avgRespect: avgRespect.toFixed(2),
      totalLoss: totalLoss.toFixed(2)
    })
  }
  
  // 处理对方成员
  for (const [iter, member] of Object.entries(opponentMembers)) {
    const memberId = member.id
    const status = member.status?.state || 'Unknown'
    const untilTimestamp = member.status?.until
    
    const attackCount = calculateMemberAttackPotential(status, untilTimestamp, checkTimestamp)
    const avgRespect = calculateAverageRespect(attacks, memberId, ourFaction.id)
    const totalLoss = attackCount * avgRespect
    
    opponentFactionTotalLoss += totalLoss
    
    opponentMembersResult.push({
      id: memberId,
      name: member.name,
      status,
      attackCount,
      avgRespect: avgRespect.toFixed(2),
      totalLoss: totalLoss.toFixed(2)
    })
  }
  
  // 结果排序 - 按总丢分降序
  ourMembersResult.sort((a, b) => parseFloat(b.totalLoss) - parseFloat(a.totalLoss))
  opponentMembersResult.sort((a, b) => parseFloat(b.totalLoss) - parseFloat(a.totalLoss))
  
  // 保存结果
  attacksResult.value = {
    ourFactionTotalLoss,
    opponentFactionTotalLoss,
    ourMembers: ourMembersResult,
    opponentMembers: opponentMembersResult
  }
}

// 计算成员可被攻击的次数
const calculateMemberAttackPotential = (status, untilTimestamp, checkTimestamp) => {
  if (status !== "Okay" && status !== "Hospital") {
    return 0
  }
  
  // 如果是医院状态，且出院时间大于当前时间，则无法被攻击
  if (status === "Hospital" && untilTimestamp && untilTimestamp > checkTimestamp) {
    return 0
  }
  
  // 每20分钟可被攻击一次
  const attackInterval = 20 * 60  // 20分钟转换为秒
  
  if (status === "Hospital") {
    // 如果是医院状态，计算从出院时间到检查时间的攻击次数
    return Math.floor((checkTimestamp - untilTimestamp) / attackInterval)
  } else {
    // 如果是正常状态，使用从当前时间到检查时间的间隔
    const currentTime = Math.floor(Date.now() / 1000)
    return Math.floor((checkTimestamp - currentTime) / attackInterval)
  }
}

// 计算成员的平均respect损失
const calculateAverageRespect = (attacks, memberId, opponentFactionId) => {
  const respects = []
  console.log(`计算用户ID ${memberId} 的平均丢分，对方帮派ID: ${opponentFactionId}`)
  
  for (const attack of attacks) {
    const respectGain = parseFloat(attack.respect_gain || 0)
    
    // 排除异常值
    if (respectGain === 0 || respectGain > 20) {
      continue
    }
    
    const attacker = attack.attacker
    const defender = attack.defender
    
    // 检查攻击记录中的防守方ID是否匹配当前成员ID
    if (defender && String(defender.id) === String(memberId)) {
      // 检查攻击方是否来自对方帮派
      if (attacker && String(attacker.faction_id) === String(opponentFactionId)) {
        console.log(`找到匹配的攻击记录: ${attack.code}, 丢分: ${respectGain}`)
        respects.push(respectGain)
      }
    }
  }
  
  console.log(`用户ID ${memberId} 找到 ${respects.length} 条攻击记录`)
  
  // 如果没有数据，返回默认值10
  if (respects.length === 0) {
    console.log(`用户ID ${memberId} 没有匹配的攻击记录，返回默认值10`)
    return 10.0
  }
  
  const avgRespect = respects.reduce((sum, val) => sum + val, 0) / respects.length
  console.log(`用户ID ${memberId} 的平均丢分: ${avgRespect.toFixed(2)}`)
  return avgRespect
}
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.sidebar {
  background-color: #fff;
  padding: 20px;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  border-right: 1px solid #e4e7ed;
}

.sidebar-header {
  margin-bottom: 30px;
  text-align: center;
}

.sidebar-header h1 {
  color: #409eff;
  margin: 0;
  font-size: 20px;
}

.api-key-section {
  margin-bottom: 30px;
  padding: 15px;
  background-color: #f9f9fb;
  border-radius: 8px;
  border: 1px solid #e9e9eb;
}

.api-key-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.api-key-hint {
  color: #909399;
  font-size: 12px;
}

.sidebar-menu {
  width: 100%;
  border: none;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-section {
  max-width: 1200px;
  margin: 0 auto;
}

.function-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.war-results {
  margin-top: 20px;
}

.war-info {
  margin-bottom: 20px;
}

.price-settings {
  margin: 20px 0;
  padding: 20px;
  background-color: #f9f9fb;
  border-radius: 8px;
}

.price-settings .el-input-number {
  width: 100%;
}

.faction-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.reward-split {
  margin-top: 20px;
  padding: 20px;
  background-color: #f9f9fb;
  border-radius: 8px;
  border-top: 1px solid #eee;
}

.split-result {
  margin-top: 15px;
  padding: 15px;
  background-color: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.transfer-item {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.error-message {
  color: #f56c6c;
}

.load-message {
  text-align: center;
  color: #909399;
  margin: 10px 0;
}

.attacks-result {
  margin-top: 20px;
}

h2, h3, h4 {
  margin: 0;
  color: #303133;
}
</style>
