<template>
  <div class="space-y-4 max-w-[1600px] mx-auto">
    <!-- Top Header Bar -->
    <div class="flex flex-wrap items-center justify-between gap-4 bg-slate-900/70 p-4 rounded-xl border border-slate-800 shadow-sm">
      <div>
        <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <span>🎯</span> 待投递机会库 (4轨智能分发)
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">多渠道高匹配机会聚合 • 自动化 4 轨简历推荐 • 差异化自荐打招呼语一键复制</p>
      </div>

      <!-- Stats Bar -->
      <div class="flex items-center gap-2">
        <div class="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
          🔵 控制算法: {{ countByTrack('控制算法') }}
        </div>
        <div class="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold">
          🟣 自动化嵌入式: {{ countByTrack('自动化与嵌入式') }}
        </div>
        <div class="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          🟢 机电电气: {{ countByTrack('机电一体化与电气') }}
        </div>
        <div class="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold">
          🟠 机械仿真: {{ countByTrack('机械结构与仿真') }}
        </div>
      </div>
    </div>

    <!-- Filters & Quick Actions -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-900/50 p-3 rounded-xl border border-slate-800/80">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Search Input -->
        <div class="relative">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索待投企业 / 岗位..." 
            class="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 outline-none w-60 focus:border-blue-500 transition"
          />
          <span class="absolute left-2.5 top-2 text-slate-500 text-xs">🔍</span>
        </div>

        <!-- 4-Track Filter -->
        <select v-model="selectedTrack" class="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 outline-none">
          <option value="">全部 4 轨方向</option>
          <option value="控制算法">🔵 控制算法</option>
          <option value="自动化与嵌入式">🟣 自动化与嵌入式</option>
          <option value="机电一体化与电气">🟢 机电一体化与电气</option>
          <option value="机械结构与仿真">🟠 机械结构与仿真</option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <button 
          @click="loadToApplyList" 
          class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs transition cursor-pointer"
        >
          🔄 刷新机会池
        </button>
      </div>
    </div>

    <!-- Opportunity Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="item in filteredOpportunities" 
        :key="item.id"
        class="bg-slate-900/70 border border-slate-800 hover:border-blue-500/40 rounded-xl p-4.5 space-y-3.5 transition flex flex-col justify-between shadow-sm"
      >
        <!-- Card Header: Company & Match Score -->
        <div class="space-y-1.5">
          <div class="flex items-start justify-between gap-2">
            <div>
              <h3 class="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                <span>{{ item.company_name }}</span>
                <span v-if="item.city" class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-normal">
                  📍 {{ item.city }}
                </span>
              </h3>
              <div class="text-xs font-semibold text-blue-400 mt-0.5">{{ item.position }}</div>
            </div>

            <div class="text-right shrink-0">
              <span 
                :class="['text-xs px-2 py-0.5 rounded font-mono font-bold inline-block', item.match_score >= 85 ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30']"
              >
                {{ item.match_score || 85 }}分
              </span>
            </div>
          </div>

          <!-- Track Badge & Recommended Resume -->
          <div class="flex flex-wrap items-center gap-1.5 pt-1">
            <span :class="['px-2 py-0.5 rounded text-[10px] font-semibold border', getTrackBadgeClass(item.recommended_track)]">
              {{ item.recommended_track }}
            </span>
            <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
              📄 {{ item.recommended_resume }}
            </span>
          </div>

          <!-- Match Reasoning -->
          <p class="text-[11px] text-slate-400 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
            💡 {{ item.match_reason || '与个人硕士课题及控制/嵌入式/机械项目背景高度契合。' }}
          </p>
        </div>

        <!-- Dynamic Greeting Script Section -->
        <div class="space-y-1.5 bg-slate-950/80 p-3 rounded-lg border border-slate-800/90 text-xs">
          <div class="flex items-center justify-between text-slate-400">
            <span class="font-bold text-[11px] text-slate-300">💬 自荐打招呼语 / 优势陈述:</span>
            <button 
              @click="copyText(item.greeting_script)"
              class="text-[10px] text-blue-400 hover:text-blue-300 transition font-medium cursor-pointer"
            >
              📋 复制话术
            </button>
          </div>
          <p class="text-slate-300 text-[11px] leading-relaxed line-clamp-3 select-all">
            {{ item.greeting_script || '您好，关注到贵司该岗位需求，我硕士就读于大连交大机械工程，主攻运动控制算法与嵌入式机电开发，具备完整的实机工程项目经验，期待与您进一步交流！' }}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-2 pt-2 border-t border-slate-800/80">
          <a 
            v-if="item.portal_url" 
            :href="item.portal_url" 
            target="_blank"
            class="flex-1 py-1.5 rounded-lg text-center text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            打开招聘官网 ↗
          </a>
          <button 
            @click="triggerPrefill(item)"
            :disabled="item.is_prefilling"
            class="flex-1 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-sm transition cursor-pointer disabled:opacity-50"
          >
            <span v-if="item.is_prefilling" class="animate-spin mr-1">⟳</span>
            <span v-else>⚡</span>
            预填并核对
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredOpportunities.length === 0" class="col-span-full py-16 text-center text-slate-500">
        <div class="text-3xl mb-2">🔭</div>
        <div class="text-sm">暂无符合条件的待投递机会</div>
        <p class="text-xs text-slate-600 mt-1">系统将定期通过招聘渠道或企业名录自动扫描并更新</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

interface Opportunity {
  id: number
  company_name: string
  position: string
  city?: string
  match_score: number
  match_reason?: string
  recommended_track: string
  recommended_resume: string
  greeting_script?: string
  portal_url?: string
  is_prefilling?: boolean
}

const router = useRouter()
const opportunities = ref<Opportunity[]>([])
const searchQuery = ref('')
const selectedTrack = ref('')

const filteredOpportunities = computed(() => {
  return opportunities.value.filter(item => {
    if (selectedTrack.value && item.recommended_track !== selectedTrack.value) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      if (!item.company_name.toLowerCase().includes(q) && !item.position.toLowerCase().includes(q)) {
        return false
      }
    }
    return true
  })
})

function countByTrack(track: string) {
  return opportunities.value.filter(o => o.recommended_track === track).length
}

async function loadToApplyList() {
  try {
    const res = await fetch('/api/to-apply')
    const data = await res.json()
    if (data.code === 200 && Array.isArray(data.data)) {
      opportunities.value = data.data
    }
  } catch (err) {
    console.error('Failed to load opportunities:', err)
  }
}

async function triggerPrefill(item: Opportunity) {
  item.is_prefilling = true
  try {
    const res = await fetch(`/api/to-apply/${item.id}/prefill`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track: item.recommended_track })
    })
    const data = await res.json()
    if (data.code === 200 && data.data?.submission_id) {
      router.push(`/submissions/${data.data.submission_id}`)
    } else {
      router.push('/submissions')
    }
  } catch (err) {
    console.error('Prefill failed:', err)
    router.push('/submissions')
  } finally {
    item.is_prefilling = false
  }
}

function copyText(text?: string) {
  if (!text) return
  navigator.clipboard.writeText(text)
  alert('已复制自荐打招呼语到剪贴板！')
}

function getTrackBadgeClass(track?: string) {
  if (!track) return 'bg-slate-800 text-slate-400 border-slate-700'
  if (track.includes('控制算法')) return 'bg-blue-500/15 text-blue-400 border-blue-500/30'
  if (track.includes('自动化') || track.includes('嵌入式')) return 'bg-purple-500/15 text-purple-400 border-purple-500/30'
  if (track.includes('机电') || track.includes('电气')) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
  if (track.includes('机械') || track.includes('仿真')) return 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  return 'bg-slate-800 text-slate-300 border-slate-700'
}

onMounted(() => {
  loadToApplyList()
})
</script>
