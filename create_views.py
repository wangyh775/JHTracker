import os

os.makedirs('frontend/src/views', exist_ok=True)

to_apply_vue = """<template>
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
"""

submissions_vue = """<template>
  <div class="space-y-4 max-w-[1600px] mx-auto">
    <!-- Top Header Bar -->
    <div class="flex flex-wrap items-center justify-between gap-4 bg-slate-900/70 p-4 rounded-xl border border-slate-800 shadow-sm">
      <div>
        <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <span>🛡️</span> 网申预填核对站 (Zero-Submit 审计台)
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">安全围栏机制：自动化脚本仅预填表单，逐项核验后由求职者在真实招聘页手动提交并回写状态</p>
      </div>

      <div class="flex items-center gap-2.5">
        <button 
          @click="loadSubmissions" 
          class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs transition cursor-pointer"
        >
          🔄 刷新列表
        </button>
      </div>
    </div>

    <!-- Submissions Table List -->
    <div class="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/80 text-slate-400 font-medium select-none">
            <th class="py-3 px-4">企业 / 岗位名称</th>
            <th class="py-3 px-3">投递通道 URL</th>
            <th class="py-3 px-3">预填状态</th>
            <th class="py-3 px-3">预填字段数</th>
            <th class="py-3 px-3">创建时间</th>
            <th class="py-3 px-4 text-right">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/60 text-slate-200">
          <tr 
            v-for="sub in submissions" 
            :key="sub.id"
            class="hover:bg-slate-800/40 transition group"
          >
            <!-- Company & Position -->
            <td class="py-3.5 px-4">
              <div class="font-bold text-slate-100 group-hover:text-blue-400 transition">
                {{ sub.company_name || '未命名企业' }}
              </div>
              <div class="text-[11px] text-slate-400 mt-0.5">
                {{ sub.position || '未指定岗位' }}
              </div>
            </td>

            <!-- Portal URL -->
            <td class="py-3.5 px-3 max-w-xs truncate font-mono text-slate-400">
              <a v-if="sub.portal_url" :href="sub.portal_url" target="_blank" class="text-blue-400/80 hover:underline">
                {{ sub.portal_url }}
              </a>
              <span v-else class="text-slate-600">无链接</span>
            </td>

            <!-- Status Badge -->
            <td class="py-3.5 px-3">
              <span :class="['px-2 py-0.5 rounded text-[11px] font-bold border', getSubmissionStatusClass(sub.status)]">
                {{ getSubmissionStatusLabel(sub.status) }}
              </span>
            </td>

            <!-- Field Count -->
            <td class="py-3.5 px-3 font-mono text-slate-300">
              {{ getFieldCount(sub.fields_json) }} 项已提取
            </td>

            <!-- Created At -->
            <td class="py-3.5 px-3 text-slate-400 font-mono">
              {{ sub.created_at?.substring(0, 16) || '刚刚' }}
            </td>

            <!-- Actions -->
            <td class="py-3.5 px-4 text-right whitespace-nowrap">
              <div class="flex items-center justify-end gap-2">
                <router-link 
                  :to=\"`/submissions/${sub.id}`\" 
                  class="px-3 py-1.5 rounded-lg bg-blue-600/15 text-blue-400 hover:bg-blue-600 hover:text-white transition text-xs font-semibold cursor-pointer"
                >
                  逐项核对 ➔
                </router-link>
              </div>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="submissions.length === 0">
            <td colspan="6" class="py-16 text-center text-slate-500">
              <div class="text-3xl mb-2">🛡️</div>
              <div class="text-sm">暂无待核对的网申预填记录</div>
              <p class="text-xs text-slate-600 mt-1">在“待投递机会库”或顶部点击“一键预填当前网申”即可生成预填核对任务</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Submission {
  id: number
  application_id?: number
  company_name?: string
  position?: string
  portal_url?: string
  status: string
  fields_json?: Record<string, any>
  created_at?: string
}

const submissions = ref<Submission[]>([])

async function loadSubmissions() {
  try {
    const res = await fetch('/api/submissions')
    const data = await res.json()
    if (data.code === 200 && Array.isArray(data.data)) {
      submissions.value = data.data
    }
  } catch (err) {
    console.error('Failed to load submissions:', err)
  }
}

function getFieldCount(fields?: Record<string, any>) {
  if (!fields) return 0
  return Object.keys(fields).length
}

function getSubmissionStatusClass(status: string) {
  switch (status) {
    case 'prefilled':
    case 'pending_review': return 'bg-amber-500/15 text-amber-400 border-amber-500/30'
    case 'submitted':
    case 'confirmed': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
    case 'rejected': return 'bg-rose-500/15 text-rose-400 border-rose-500/30'
    default: return 'bg-slate-800 text-slate-400 border-slate-700'
  }
}

function getSubmissionStatusLabel(status: string) {
  switch (status) {
    case 'prefilled':
    case 'pending_review': return '⚡ 待人工核验'
    case 'submitted':
    case 'confirmed': return '✅ 人工已确认提交'
    case 'rejected': return '❌ 已作废'
    default: return status
  }
}

onMounted(() => {
  loadSubmissions()
})
</script>
"""

submission_detail_vue = """<template>
  <div class="space-y-4 max-w-[1200px] mx-auto">
    <!-- Header Navigation Bar -->
    <div class="flex items-center justify-between bg-slate-900/70 p-4 rounded-xl border border-slate-800">
      <div class="flex items-center gap-3">
        <router-link to="/submissions" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
          ← 返回核对列表
        </router-link>
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            <span>🛡️</span> 网申表单预填核验 - {{ submission?.company_name || '目标企业' }}
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">岗位：{{ submission?.position || '控制算法 / 自动化工程师' }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span :class="['px-2.5 py-1 rounded text-xs font-bold border', getSubmissionStatusClass(submission?.status || 'pending_review')]">
          {{ getSubmissionStatusLabel(submission?.status || 'pending_review') }}
        </span>
      </div>
    </div>

    <!-- Main Audit Form Card -->
    <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6 shadow-sm">
      <!-- Portal Link & Reminder Banner -->
      <div class="bg-blue-950/40 border border-blue-500/20 rounded-xl p-4 flex items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="text-xs font-bold text-blue-300 flex items-center gap-1.5">
            <span>ℹ️</span> 安全合规提示 (Zero-Submit 铁律)
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            自动化程序已根据你的简历库预填以下各字段。请逐项核对准确性，确认无误后点击下方按钮进入招聘官网真实页面完成最终“提交申请”。
          </p>
        </div>

        <a 
          v-if="submission?.portal_url" 
          :href="submission.portal_url" 
          target="_blank"
          class="shrink-0 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow transition"
        >
          打开网申页面 ↗
        </a>
      </div>

      <!-- Key Value Field Auditor -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-slate-200 border-b border-slate-800 pb-2">
          📝 预填字段核验明细
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div 
            v-for="(val, key) in parsedFields" 
            :key="key"
            class="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 space-y-1"
          >
            <div class="flex items-center justify-between text-slate-400">
              <span class="font-bold text-slate-300">{{ key }}</span>
              <button 
                @click="copyText(String(val))"
                class="text-[10px] text-blue-400 hover:text-blue-300 cursor-pointer"
              >
                复制
              </button>
            </div>
            <div class="text-slate-200 font-mono bg-slate-900/80 p-2 rounded border border-slate-800 break-all select-all">
              {{ val }}
            </div>
          </div>
        </div>

        <div v-if="Object.keys(parsedFields).length === 0" class="py-8 text-center text-slate-500 text-xs">
          暂无结构化字段，请直接参照个人资料侧边栏进行手动填报。
        </div>
      </div>

      <!-- Action Confirmation Area -->
      <div class="pt-6 border-t border-slate-800 flex items-center justify-between">
        <div class="text-xs text-slate-400">
          确认在招聘官网手动点击提交后，点击右侧按钮将状态回写为“已投递”。
        </div>

        <div class="flex items-center gap-3">
          <button 
            @click="confirmManualSubmission" 
            class="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/20 transition cursor-pointer"
          >
            ✅ 我已在招聘官网手动提交完成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface SubmissionDetail {
  id: number
  application_id?: number
  company_name?: string
  position?: string
  portal_url?: string
  status: string
  fields_json?: Record<string, any>
  created_at?: string
}

const route = useRoute()
const router = useRouter()
const submission = ref<SubmissionDetail | null>(null)

const parsedFields = computed(() => {
  return submission.value?.fields_json || {}
})

async function loadDetail() {
  const id = route.params.id
  try {
    const res = await fetch(`/api/submissions/${id}`)
    const data = await res.json()
    if (data.code === 200) {
      submission.value = data.data
    }
  } catch (err) {
    console.error('Failed to load detail:', err)
  }
}

async function confirmManualSubmission() {
  if (!confirm('确认已经在真实招聘系统中完成了提交操作吗？')) return
  const id = route.params.id
  try {
    const res = await fetch(`/api/submissions/${id}/confirm`, {
      method: 'POST'
    })
    const data = await res.json()
    if (data.code === 200) {
      alert('已成功回写为“已投递”状态！')
      router.push('/applications')
    }
  } catch (err) {
    console.error('Confirm failed:', err)
  }
}

function copyText(val: string) {
  navigator.clipboard.writeText(val)
  alert('已复制到剪贴板！')
}

function getSubmissionStatusClass(status: string) {
  switch (status) {
    case 'prefilled':
    case 'pending_review': return 'bg-amber-500/15 text-amber-400 border-amber-500/30'
    case 'submitted':
    case 'confirmed': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
    default: return 'bg-slate-800 text-slate-400 border-slate-700'
  }
}

function getSubmissionStatusLabel(status: string) {
  switch (status) {
    case 'prefilled':
    case 'pending_review': return '⚡ 待人工核验'
    case 'submitted':
    case 'confirmed': return '✅ 已确认投递'
    default: return status
  }
}

onMounted(() => {
  loadDetail()
})
</script>
"""

with open('frontend/src/views/ToApplyView.vue', 'w', encoding='utf-8') as f:
    f.write(to_apply_vue)
print('ToApplyView.vue generated.')

with open('frontend/src/views/SubmissionsView.vue', 'w', encoding='utf-8') as f:
    f.write(submissions_vue)
print('SubmissionsView.vue generated.')

with open('frontend/src/views/SubmissionDetailView.vue', 'w', encoding='utf-8') as f:
    f.write(submission_detail_vue)
print('SubmissionDetailView.vue generated.')
