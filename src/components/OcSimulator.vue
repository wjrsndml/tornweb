<template>
  <div class="oc-simulator-container">
    <el-card class="function-card">
      <template #header>
        <div class="card-header flex justify-between items-center">
          <div class="flex items-center gap-4">
             <h2>OC 结局概率模拟器</h2>
             <el-button type="primary" size="small" @click="fetchMyOc" :loading="loading">一键导入当前OC</el-button>
          </div>
          <div class="stats-group">
            <div class="status-box">
                <span class="label">Total Success:</span>
                <span class="value success">{{ totalGoodRate }}</span>
            </div>
            <div class="status-box">
                <span class="label">Exp. Money:</span>
                <span class="value money">${{ formatMoney(expectedMoney) }}</span>
            </div>
            <div class="status-box">
                <span class="label">Exp. Respect:</span>
                <span class="value respect">{{ expectedRespect.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </template>
      
      <div class="controls-section">
        <div class="oc-select">
          <label>选择 OC 任务：</label>
          <el-select v-model="selectedOcIndex" placeholder="Select OC" @change="handleOcChange">
            <el-option
              v-for="(oc, index) in OCS"
              :key="index"
              :label="oc.name"
              :value="index"
            />
          </el-select>
        </div>

        <div class="sliders-grid">
          <div v-for="role in currentRoles" :key="role.id" class="slider-box">
             <div class="slider-header">
               <span class="role-name" :style="{ color: role.color }">{{ role.name }}</span>
               <span class="role-value">{{ (roleRates[role.id] * 100).toFixed(0) }}%</span>
             </div>
             <el-slider 
               v-model="roleRates[role.id]" 
               :min="0" 
               :max="1" 
               :step="0.01" 
               :format-tooltip="(val) => (val * 100).toFixed(0) + '%'"
               @input="updateCalculation"
             />
          </div>
        </div>
      </div>

      <div class="graph-container">
        <div class="legend">
           <span class="legend-item pass">PASS</span>
           <span class="legend-item fail">FAIL</span>
        </div>
        <div class="svg-wrapper">
          <svg id="canvas" width="1700" height="800" viewBox="0 0 1700 800">
              <defs>
                  <marker id="arrow-green" markerWidth="8" markerHeight="8" refX="7" refY="4" orientation="auto"><path d="M0,0 L0,8 L8,4 z" fill="#2ecc71"/></marker>
                  <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="7" refY="4" orientation="auto"><path d="M0,0 L0,8 L8,4 z" fill="#e74c3c"/></marker>
              </defs>
              <g class="links-layer">
                 <template v-for="(link, idx) in graphLinks" :key="'link-'+idx">
                   <path :d="link.d" :class="link.cls" />
                 </template>
              </g>
              <g class="nodes-layer">
                 <template v-for="(node, key) in graphNodes" :key="'node-'+key">
                    <g :transform="`translate(${node.x},${node.y})`">
                       <!-- Start Node -->
                       <template v-if="node.type === 'start'">
                          <circle r="24" fill="#111" stroke="#fff" stroke-width="2"/>
                          <text class="node-label" dy="4">{{ node.label }}</text>
                       </template>
                       <!-- Step Node -->
                       <template v-else-if="node.type === 'step'">
                          <rect x="-30" y="-30" width="60" height="60" :fill="node.color" transform="rotate(45)" stroke="#fff" stroke-width="1.5" class="node-rect"/>
                          <text class="node-label" y="-4">{{ node.labelParts[0] }}</text>
                          <text class="node-label" y="10">{{ node.labelParts[1] || '' }}</text>
                          <text class="prob-tag" y="48">{{ (nodeProbs[key] * 100).toFixed(1) }}%</text>
                       </template>
                       <!-- End Node -->
                       <template v-else-if="node.type === 'end'">
                          <rect x="-50" y="-25" width="100" height="50" rx="6" :fill="node.style === 'good' ? '#064e3b' : '#450a0a'" :stroke="node.style === 'good' ? '#34d399' : '#f87171'" stroke-width="2"/>
                          <text class="node-label" y="-5">{{ node.label }}</text>
                          <text class="node-label" y="10" :fill="node.style === 'good' ? '#34d399' : '#f87171'">{{ (nodeProbs[key] * 100).toFixed(1) }}%</text>
                          <template v-if="node.reward">
                              <text class="node-sub-label money" y="22">${{ formatMoney(node.reward.money) }}</text>
                          </template>
                       </template>
                    </g>
                 </template>
              </g>
          </svg>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { OCS } from '../data/oc_config'

const props = defineProps({
  apiKey: {
    type: String,
    default: ''
  }
})

const loading = ref(false)
const selectedOcIndex = ref(0)
const roleRates = reactive({})
const nodeProbs = reactive({})

const currentOC = computed(() => OCS[selectedOcIndex.value])
const currentRoles = computed(() => currentOC.value.roles)

const fetchMyOc = async () => {
    if (!props.apiKey) {
        ElMessage.warning('请先设置 API Key')
        return
    }

    loading.value = true
    try {
        // 1. Get My ID
        const userResp = await axios.get(`https://api.torn.com/user/?selections=basic&key=${props.apiKey}`)
        const myId = userResp.data.player_id
        if (!myId) throw new Error('无法获取用户ID')

        // 2. Get Faction Crimes
        const crimesResp = await axios.get(`https://api.torn.com/v2/faction/crimes?cat=available,initiated,in_progress&sort=DESC&limit=50`, {
            headers: { Authorization: `ApiKey ${props.apiKey}` }
        })
        
        const crimes = crimesResp.data.crimes || []
        
        // 3. Find crime where I am a participant
        const myCrime = crimes.find(c => {
            if (!c.slots) return false
            return c.slots.some(s => s.user && s.user.id === myId)
        })

        if (!myCrime) {
            ElMessage.info('未找到您当前参与的 OC')
            return
        }

        // 4. Match OC Type
        const ocIndex = OCS.findIndex(def => def.name.toLowerCase().includes(myCrime.name.toLowerCase()))
        if (ocIndex === -1) {
             ElMessage.warning(`找到 OC "${myCrime.name}"，但在模拟器中未定义`)
             return
        }
        selectedOcIndex.value = ocIndex
        
        // 5. Update Rates
        console.log('Found Crime:', myCrime)
        
        const targetRoles = OCS[ocIndex].roles
        const apiSlots = myCrime.slots
        const newRates = { ...roleRates }
        
        // Map slots to roles by order
        if (apiSlots.length > 0) {
            console.log('Slot keys:', Object.keys(apiSlots[0]))
            console.log('First slot data:', apiSlots[0])
        }

        // Map slots to roles by matching name + position_number
        if (apiSlots.length > 0) {
            console.log('Slot keys:', Object.keys(apiSlots[0]))
            console.log('First slot data:', apiSlots[0])
        }

        apiSlots.forEach((slot, idx) => {
            // Construct potential role names in OCS config
            // e.g. "Muscle" + "1" -> "Muscle 1"
            // e.g. "Robber" + "1" -> "Robber 1" (But config says "Robber")
            const pName = slot.position || ''
            const pNum = slot.position_number
            
            const candidate1 = `${pName} ${pNum}` // "Muscle 1"
            const candidate2 = pName             // "Robber"

            // Find matching role in config
            const roleDef = targetRoles.find(r => r.name === candidate1 || r.name === candidate2)
            
            if (roleDef) {
                // Try multiple potential keys for rate
                let val = undefined
                const keys = ['checkpoint_pass_rate', 'success', 'success_rate', 'initial_success', 'effectiveness']
                for (const k of keys) {
                    if (slot[k] !== undefined) {
                        val = slot[k]
                        break
                    }
                }

                if (val !== undefined) {
                    let r = parseFloat(val)
                    if (r > 1) r = r / 100
                    newRates[roleDef.id] = r
                }
            } else {
                console.warn(`Could not match API slot "${candidate1}" or "${candidate2}" to any role.`)
            }
        })
        
        // Apply updates
        Object.assign(roleRates, newRates)
        updateCalculation() 
        ElMessage.success(`已导入 "${myCrime.name}" 数据`)

    } catch (e) {
        console.error(e)
        // Extract error message safely
        const msg = e.response?.data?.error?.error || e.message || '获取失败'
        ElMessage.error(msg)
    } finally {
        loading.value = false
    }
}
const graphNodes = computed(() => {
    const nodes = currentOC.value.nodes
    const res = {}
    for (let k in nodes) {
        res[k] = { ...nodes[k], labelParts: (nodes[k].label || '').split('\n') }
    }
    return res
})

const totalGoodRate = computed(() => {
    let total = 0
    for(let k in nodeProbs) {
        if(currentOC.value.nodes[k]?.style === 'good') {
            total += nodeProbs[k]
        }
    }
    return (total * 100).toFixed(2) + '%'
})

const expectedMoney = computed(() => {
    let ev = 0
    const nodes = currentOC.value.nodes
    for(let k in nodeProbs) {
        const reward = nodes[k]?.reward
        if(reward?.money) {
            ev += nodeProbs[k] * reward.money
        }
    }
    return ev
})

const expectedRespect = computed(() => {
    let ev = 0
    const nodes = currentOC.value.nodes
    for(let k in nodeProbs) {
        const reward = nodes[k]?.reward
        if(reward?.respect) {
            ev += nodeProbs[k] * reward.respect
        }
    }
    return ev
})

function formatMoney(amount) {
    if(!amount) return '0'
    return Math.round(amount).toLocaleString('en-US')
}


// Generate SVG links dynamically
// Generate SVG links dynamically
const graphLinks = computed(() => {
    const links = []
    const nodes = currentOC.value.nodes
    for (let k in nodes) {
        const n = nodes[k]
        
        // Handle Start Node
        if (n.type === 'start' && n.next && nodes[n.next]) {
            const t = nodes[n.next]
            links.push({ d: `M ${n.x} ${n.y} L ${t.x} ${t.y}`, cls: 'line-green' })
        }

        const hasPass = n.pass && nodes[n.pass]
        const hasFail = n.fail && nodes[n.fail]

        if (hasPass && hasFail && n.pass === n.fail) {
            // Overlapping case: Curve them out
            const t = nodes[n.pass]
            const dx = t.x - n.x
            const dy = t.y - n.y
            const dist = Math.sqrt(dx*dx + dy*dy) || 1
            
            // Calculate normal vector for offset (approx 30px)
            const offset = 35
            const nx = (-dy / dist) * offset
            const ny = (dx / dist) * offset
            
            // Midpoint
            const mx = (n.x + t.x) / 2
            const my = (n.y + t.y) / 2
            
            // Control points
            const cp1x = mx + nx
            const cp1y = my + ny
            const cp2x = mx - nx
            const cp2y = my - ny
            
            links.push({ d: `M ${n.x} ${n.y} Q ${cp1x} ${cp1y} ${t.x} ${t.y}`, cls: 'line-green' })
            links.push({ d: `M ${n.x} ${n.y} Q ${cp2x} ${cp2y} ${t.x} ${t.y}`, cls: 'line-red' })
        } else {
            // Normal case
            if (hasPass) {
                const t = nodes[n.pass]
                links.push({ d: `M ${n.x} ${n.y} L ${t.x} ${t.y}`, cls: 'line-green' })
            }
            if (hasFail) {
                const t = nodes[n.fail]
                links.push({ d: `M ${n.x} ${n.y} L ${t.x} ${t.y}`, cls: 'line-red' })
            }
        }
    }
    return links
})

function handleOcChange() {
    // Reset rates to defaults
    for(let r of currentRoles.value) {
        roleRates[r.id] = 0.7
    }
    updateCalculation()
}

function updateCalculation() {
    const oc = currentOC.value
    const probs = {}
    for(let k in oc.nodes) probs[k] = 0
    probs.start = 1.0

    const processList = oc.order || Object.keys(oc.nodes)
    
    processList.forEach(key => {
        const node = oc.nodes[key]
        const pIn = probs[key]
        
        if (pIn <= 0) return 

        if (node.type === 'start') {
            if (node.next) probs[node.next] += pIn
        } 
        else if (node.type === 'step') {
            let passRate = 0
            if (node.roles && node.roles.length > 0) {
                const totalRate = node.roles.reduce((sum, rId) => sum + (roleRates[rId] || 0), 0)
                passRate = totalRate / node.roles.length
            }
            
            const pPass = pIn * passRate
            const pFail = pIn * (1 - passRate)
            
            if (node.pass) probs[node.pass] += pPass
            if (node.fail) probs[node.fail] += pFail
        }
    })

    // Update reactive state
    for(let k in probs) {
        nodeProbs[k] = probs[k]
    }
}

// Init
onMounted(() => {
    handleOcChange()
})
</script>

<style scoped>
.oc-simulator-container {
    padding: 10px;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.status-box {
    background: #1e1e1e;
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid #333;
}
.status-box .label {
    color: #888;
    font-size: 12px;
    text-transform: uppercase;
    margin-right: 8px;
}
.status-box .value {
    color: #fff;
    font-size: 16px;
    font-weight: bold;
}
.status-box .value.success { color: #2ecc71; }
.status-box .value.money { color: #f1c40f; }
.status-box .value.respect { color: #3498db; }

.stats-group {
    display: flex;
    gap: 12px;
}

.controls-section {
    margin-top: 10px;
    margin-bottom: 20px;
}
/* ... */
.node-sub-label {
    font-size: 9px; 
    text-anchor: middle; 
    font-weight: bold;
    fill: #ffd700;
    filter: drop-shadow(0 1px 1px rgba(0,0,0,0.8));
}

.oc-select {
    margin-bottom: 20px;
}

.sliders-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
}

.slider-box {
    background: #1e1e1e;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #333;
}
.slider-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}
.role-name {
    font-size: 12px;
    font-weight: bold;
}
.role-value {
    font-size: 12px;
    color: #fff;
    background: rgba(255,255,255,0.1);
    padding: 0 4px;
    border-radius: 4px;
}

.graph-container {
    background: #181818;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid #333;
    overflow: hidden;
    position: relative;
    margin-top: 20px;
}
.legend {
    position: absolute;
    top: 10px;
    left: 10px;
    display: flex;
    gap: 8px;
    z-index: 10;
}
.legend-item {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
}
.legend-item.pass { color: #4ade80; border-color: rgba(74,222,128,0.3); }
.legend-item.fail { color: #f87171; border-color: rgba(248,113,113,0.3); }

.svg-wrapper {
    overflow-x: auto;
    padding: 10px;
}
/* Replicate the dark theme SVG styles */
.node-label { font-size: 11px; fill: white; font-weight: bold; text-anchor: middle; pointer-events: none; text-shadow: 0 1px 2px rgba(0,0,0,0.8); }
.prob-tag { font-size: 10px; fill: #00ffcc; text-anchor: middle; font-family: 'Consolas', monospace; filter: drop-shadow(0 1px 1px rgba(0,0,0,0.5)); }
.line-green { stroke: #2ecc71; stroke-width: 2.5; fill: none; marker-end: url(#arrow-green); transition: stroke-width 0.2s; }
.line-red { stroke: #e74c3c; stroke-width: 2.5; fill: none; marker-end: url(#arrow-red); transition: stroke-width 0.2s; }
.line-green:hover, .line-red:hover { stroke-width: 4; }

/* Custom Scrollbar */
.svg-wrapper::-webkit-scrollbar { width: 8px; height: 8px; }
.svg-wrapper::-webkit-scrollbar-track { background: #1a1a1a; }
.svg-wrapper::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
.svg-wrapper::-webkit-scrollbar-thumb:hover { background: #555; }
</style>
