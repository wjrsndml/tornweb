<template>
  <el-card class="analytics-card">
    <template #header>
      <div class="card-header">
        <h2>OC 收益与权重分析</h2>
        <div class="controls">
           <el-select v-model="selectedOcKey" placeholder="选择 OC" style="width: 240px" @change="handleOcChange">
             <el-option
               v-for="(data, key) in OC_ANALYSIS_DATA"
               :key="key"
               :label="getOcName(key)"
               :value="key"
             />
           </el-select>
           
           <div class="mode-switch">
             <span :class="{ active: mode === 'weight' }">权重模式 (%)</span>
             <el-switch
                v-model="mode"
                active-value="income"
                inactive-value="weight"
                style="margin: 0 8px"
             />
             <span :class="{ active: mode === 'income' }">收益模式 ($)</span>
           </div>
        </div>
      </div>
    </template>

    <div v-if="!selectedOcKey" class="empty-tip">请选择一个 OC 查看分析数据</div>

    <el-table 
      v-else
      :data="tableData" 
      stripe 
      height="calc(100vh - 200px)" 
      style="width: 100%"
      :header-cell-style="{ background: '#1e1e1e', color: '#fff' }"
      :cell-style="{ background: '#181818', color: '#ddd' }"
    >
      <el-table-column 
        prop="rate" 
        label="基础成功率" 
        width="100" 
        fixed 
        align="center"
      >
        <template #default="scope">
            <span style="font-weight: bold; color: #ffd700">{{ scope.row.rate }}%</span>
        </template>
      </el-table-column>

      <!-- Dynamic Role Columns -->
      <el-table-column
        v-for="role in currentRoles"
        :key="role.id"
        :label="role.name"
        min-width="120"
        align="center"
      >
        <template #default="scope">
           <template v-if="mode === 'weight'">
               <span class="val-weight">{{ (scope.row[role.id] * 100).toFixed(2) }}%</span>
           </template>
           <template v-else>
               <span class="val-income">${{ formatMoney(scope.row[role.id]) }}</span>
           </template>
        </template>
      </el-table-column>

      <el-table-column 
        label="总期望收益" 
        min-width="150" 
        fixed="right" 
        align="center"
      >
        <template #default="scope">
            <span class="val-total">${{ formatMoney(scope.row.total_ev) }}</span>
        </template>
      </el-table-column>
    </el-table>

  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { OC_ANALYSIS_DATA } from '../data/oc_analysis_data'
import { OCS } from '../data/oc_config'

const selectedOcKey = ref('')
const mode = ref('weight') // 'weight' or 'income'

// Helper to get printable name
const getOcName = (key) => {
    // Try to find in config first
    const def = OCS.find(o => o.key === key || o.name === key)
    if (def) return def.name
    return key
}

// Get roles definition for current selected OC
const currentRoles = computed(() => {
    if (!selectedOcKey.value) return []
    // We can infer roles from the first data entry (rate=1)
    const ocData = OC_ANALYSIS_DATA[selectedOcKey.value]
    if (!ocData) return []
    const firstRow = ocData["1"]
    if (!firstRow || !firstRow.roles) return []
    return firstRow.roles.map(r => ({ id: r.id, name: r.name }))
})

// Transform dictionary to array for table
const tableData = computed(() => {
    if (!selectedOcKey.value) return []
    const ocData = OC_ANALYSIS_DATA[selectedOcKey.value]
    if (!ocData) return []

    const rows = []
    // range 1 to 100
    for (let i = 1; i <= 100; i++) {
        const rowData = ocData[String(i)] || ocData[i]
        if (!rowData) continue

        const row = {
            rate: i,
            total_ev: rowData.total_ev
        }

        // Fill roles
        rowData.roles.forEach(r => {
            // Store raw values, format in template
            if (mode.value === 'weight') {
                row[r.id] = r.percent // 0.1234
            } else {
                row[r.id] = r.income // 123456.78
            }
        })
        rows.push(row)
    }
    return rows
})

const handleOcChange = () => {
    // maybe reset scroll or something
}

const formatMoney = (val) => {
    if (!Number.isFinite(val)) return '0'
    if (val >= 1000000) {
        return (val / 1000000).toFixed(1) + 'm'
    }
    return Math.round(val).toLocaleString()
}

// Set default
if (Object.keys(OC_ANALYSIS_DATA).length > 0) {
    selectedOcKey.value = Object.keys(OC_ANALYSIS_DATA)[0]
}
</script>

<style scoped>
.analytics-card {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.controls {
    display: flex;
    align-items: center;
    gap: 20px;
}
.mode-switch {
    display: flex;
    align-items: center;
    font-size: 14px;
    color: #888;
}
.mode-switch span.active {
    color: #409eff;
    font-weight: bold;
}
.val-weight {
    color: #4ade80;
}
.val-income {
    color: #fca5a5;
}
.val-total {
    color: #ffd700;
    font-weight: bold;
}
.empty-tip {
    text-align: center;
    color: #888;
    margin-top: 50px;
}

/* Dark table overrides */
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
    background: #232323 !important;
}
:deep(.el-table__row:hover > td) {
    background-color: #333 !important;
}
</style>
