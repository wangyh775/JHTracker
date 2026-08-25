<template>
  <div class="space-y-4 max-w-[1600px] mx-auto">
    <!-- Top Toolbar: Search, Filters, Stats & Actions -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索公司 / 岗位名称..." 
            class="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 outline-none w-60 focus:border-blue-500 transition"
          />
          <span class="absolute left-2.5 top-2 text-slate-500 text-xs">🔍</span>
        </div>

        <select v-model="filterTrack" class="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 outline-none">
          <option value="">全部简历版本</option>
          <option value="自动化版">⚡ 自动化版</option>
          <option value="机械版">🔧 机械版</option>
          <option value="机电综合版">🤖 机电综合版</option>
        </select>

        <select v-model="filterChannel" class="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 outline-none">
          <option value="">全部投递渠道</option>
          <option value="官网直投">官网直投</option>
          <option value="BOSS直聘">BOSS直聘</option>
          <option value="猎聘">猎聘</option>
          <option value="内推">校友/员工内推</option>
          <option value="邮箱直投">HR邮箱直投</option>
        </select>
      </div>

      <div class="flex items-center gap-2.5">
        <button 
          @click="showAddModal = true"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm cursor-pointer"
        >
          <span>+</span> 新增岗位记录
        </button>
        <button 
          @click="loadApplications"
          class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs transition cursor-pointer"
          title="刷新列表"
        >
          🔄
        </button>
      </div>
    </div>

    <!-- Full-Featured 8-Stage Horizontal Kanban Lanes -->
    <div class="flex gap-3.5 overflow-x-auto pb-4 pt-1 items-start min-h-[calc(100vh-220px)]">
      <div 
        v-for="lane in lanes" 
        :key="lane.status"
        class="w-72 shrink-0 bg-slate-900/50 border border-slate-800/80 rounded-xl p-3 flex flex-col max-h-[calc(100vh-240px)]"
      >
        <!-- Lane Header -->
        <div class="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-800/80">
          <div class="flex items-center gap-1.5">
            <span :class="['w-2 h-2 rounded-full', lane.color]"></span>
            <span class="font-bold text-xs text-slate-200">{{ lane.title }}</span>
          </div>
          <span class="text-[11px] px-2 py-0.2 rounded-full bg-slate-800 text-slate-400 font-mono font-bold">
            {{ getLaneApps(lane.status).length }}
          </span>
        </div>

        <!-- Lane Card List -->
        <div class="flex-1 overflow-y-auto space-y-2.5 pr-1">
          <div 
            v-for="app in getLaneApps(lane.status)" 
            :key="app.id"
            @click="openDetail(app)"
            class="p-3.5 bg-slate-900/90 rounded-lg border border-slate-800 hover:border-blue-500/50 transition cursor-pointer shadow-sm group space-y-2.5 relative"
          >
            <!-- Card Header: Company & Match Score -->
            <div class="flex items-start justify-between gap-1">
              <span class="font-bold text-sm text-slate-100 group-hover:text-blue-400 transition truncate">
                {{ app.company?.name || '未知企业' }}
              </span>
              <span 
                v-if="app.match_score" 
                :class="[
                  'text-[10px] px-1.5 py-0.5 rounded font-mono font-bold shrink-0',
                  app.match_score >= 90 ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' :
                  app.match_score >= 80 ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' :
                  'bg-slate-800 text-slate-400'
                ]"
              >
                {{ app.match_score }}分
              </span>
            </div>

            <!-- Position Title -->
            <div class="text-xs font-medium text-slate-200 line-clamp-1">
              {{ app.position }}
            </div>

            <!-- Agent Scoring Reason (if any) -->
            <div v-if="app.scoring_reason" class="p-2 bg-slate-950/70 rounded border border-slate-800/80 text-[11px] text-slate-400 line-clamp-2">
              💡 {{ app.scoring_reason }}
            </div>

            <!-- Card Tags & Metadata -->
            <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
              <span v-if="app.resume_version" :class="[
                'px-1.5 py-0.5 rounded border',
                app.resume_version.includes('自动化') ? 'bg-amber-400/10 text-amber-400 border-amber-400/20' :
                app.resume_version.includes('机械') ? 'bg-blue-400/10 text-blue-400 border-blue-400/20' :
                'bg-purple-400/10 text-purple-400 border-purple-400/20'
              ]">
                {{ app.resume_version }}
              </span>
              <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                📍 {{ app.company?.city || '全国' }}
              </span>
              <span v-if="app.apply_date" class="text-slate-500 font-mono ml-auto">
                {{ app.apply_date.substring(5, 10) }}
              </span>
            </div>

            <!-- Quick Action Bar (Bottom of card) -->
            <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2" @click.stop>
              <!-- State Transition Dropdown -->
              <select 
                :value="app.status" 
                @change="onQuickStatusChange(app.id, ($event.target as HTMLSelectElement).value)"
                class="bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-[11px] text-slate-300 outline-none max-w-[120px]"
              >
                <option v-for="l in lanes" :key="l.status" :value="l.status">{{ l.title }}</option>
              </select>

              <!-- External Job URL Button -->
              <a 
                v-if="app.job?.job_url || app.company?.careers_url" 
                :href="app.job?.job_url || app.company?.careers_url" 
                target="_blank" 
                class="text-[11px] text-blue-400 hover:text-blue-300 px-2 py-1 rounded bg-blue-500/10 hover:bg-blue-500/20 transition"
              >
                JD ↗
              </a>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="!getLaneApps(lane.status).length" class="text-center py-10 text-slate-600 text-xs border border-dashed border-slate-800/60 rounded-lg">
            暂无记录
          </div>
        </div>
      </div>
    </div>

    <!-- Application Detail & Edit Modal Drawer -->
    <div 
      v-if="selectedApp" 
      class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex justify-end animate-in fade-in duration-150"
      @click.self="selectedApp = null"
    >
      <div class="w-[500px] bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto space-y-5 shadow-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 class="font-bold text-base text-slate-100">{{ selectedApp.company?.name }}</h3>
            <p class="text-xs text-blue-400">{{ selectedApp.position }}</p>
          </div>
          <button @click="selectedApp = null" class="text-slate-400 hover:text-slate-200 text-xs px-2.5 py-1 bg-slate-800 rounded">✕ 关闭</button>
        </div>

        <!-- Form Edit Controls -->
        <div class="space-y-3.5 text-xs">
          <div>
            <label class="block text-slate-400 mb-1">当前推进状态</label>
            <select v-model="selectedApp.status" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none">
              <option v-for="l in lanes" :key="l.status" :value="l.status">{{ l.title }}</option>
            </select>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">匹配简历版本</label>
            <select v-model="selectedApp.resume_version" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none">
              <option value="自动化版">⚡ 自动化版 (STM32/RK3588/MPC/EKF)</option>
              <option value="机械版">🔧 机械版 (SolidWorks/Fluent/CFD/腔体)</option>
              <option value="机电综合版">🤖 机电综合版 (整机+算法+竞赛国一)</option>
            </select>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">投递渠道</label>
            <input v-model="selectedApp.channel" type="text" placeholder="如：官网直投 / 牛客内推 / BOSS直聘" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>

          <div>
            <label class="block text-slate-400 mb-1">投递/面试备忘笔记</label>
            <textarea v-model="selectedApp.notes" rows="4" placeholder="记录面试官问题、HR 沟通细节、薪资情况..." class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none"></textarea>
          </div>

          <div class="pt-4 flex items-center justify-between border-t border-slate-800">
            <button @click="deleteApp(selectedApp.id)" class="px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition cursor-pointer">
              删除此记录
            </button>
            <button @click="saveAppDetail" class="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold transition cursor-pointer">
              保存更改
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Add Modal -->
    <div 
      v-if="showAddModal" 
      class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showAddModal = false"
    >
      <div class="w-[450px] bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-2xl text-xs">
        <div class="flex items-center justify-between pb-2 border-b border-slate-800">
          <h3 class="font-bold text-sm text-slate-100">新增投递与岗位记录</h3>
          <button @click="showAddModal = false" class="text-slate-400 hover:text-slate-200">✕</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-slate-400 mb-1">企业名称 *</label>
            <input v-model="newForm.company_name" type="text" placeholder="如：汇川技术 / 拓竹科技" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>
          <div>
            <label class="block text-slate-400 mb-1">岗位名称 *</label>
            <input v-model="newForm.position" type="text" placeholder="如：运动控制算法工程师" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>
          <div>
            <label class="block text-slate-400 mb-1">目标城市</label>
            <input v-model="newForm.city" type="text" placeholder="如：苏州 / 深圳 / 青岛" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>
          <div>
            <label class="block text-slate-400 mb-1">简历版本</label>
            <select v-model="newForm.resume_version" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none">
              <option value="自动化版">⚡ 自动化版</option>
              <option value="机械版">🔧 机械版</option>
              <option value="机电综合版">🤖 机电综合版</option>
            </select>
          </div>
        </div>

        <div class="pt-3 flex justify-end gap-2 border-t border-slate-800">
          <button @click="showAddModal = false" class="px-3 py-1.5 rounded bg-slate-800 text-slate-300">取消</button>
          <button @click="submitNewApp" class="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold">创建记录</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const applications = ref<any[]>([])
const searchQuery = ref('')
const filterTrack = ref('')
const filterChannel = ref('')
const selectedApp = ref<any>(null)
const showAddModal = ref(false)

const newForm = ref({
  company_name: '',
  position: '',
  city: '苏州',
  resume_version: '自动化版'
})

// 8 大标准生命周期泳道
const lanes = [
  { status: '待投递', title: '待投递 (To Apply)', color: 'bg-blue-500' },
  { status: '待提交', title: '待提交草稿 (Drafts)', color: 'bg-cyan-500' },
  { status: '已投递', title: '已投递 (Applied)', color: 'bg-indigo-500' },
  { status: '简历筛选', title: '简历筛选 (Screening)', color: 'bg-sky-500' },
  { status: '笔试', title: '笔试测评 (Test)', color: 'bg-amber-500' },
  { status: '一面', title: '技术一面 (1st Round)', color: 'bg-orange-500' },
  { status: '二面', title: '技术二面/主管 (2nd Round)', color: 'bg-rose-500' },
  { status: 'Offer', title: '录用意向 (Offer)', color: 'bg-emerald-500' },
]

const loadApplications = async () => {
  try {
    const res = await fetch('/api/v1/applications')
    if (res.ok) {
      applications.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch applications', e)
  }
}

onMounted(() => {
  loadApplications()
})

const getLaneApps = (status: string) => {
  return applications.value.filter(app => {
    const matchesStatus = app.status === status
    const matchesSearch = !searchQuery.value || 
      (app.position && app.position.toLowerCase().includes(searchQuery.value.toLowerCase())) ||
      (app.company?.name && app.company.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
    const matchesTrack = !filterTrack.value || app.resume_version === filterTrack.value
    const matchesChannel = !filterChannel.value || app.channel === filterChannel.value

    return matchesStatus && matchesSearch && matchesTrack && matchesChannel
  })
}

const onQuickStatusChange = async (appId: number, newStatus: string) => {
  try {
    const res = await fetch(`/api/v1/applications/${appId}/status?status=${encodeURIComponent(newStatus)}`, {
      method: 'PATCH'
    })
    if (res.ok) {
      await loadApplications()
    }
  } catch (e) {
    console.error('Failed to change status', e)
  }
}

const openDetail = (app: any) => {
  selectedApp.value = { ...app }
}

const saveAppDetail = async () => {
  if (!selectedApp.value) return
  await onQuickStatusChange(selectedApp.value.id, selectedApp.value.status)
  selectedApp.value = null
}

const deleteApp = async (appId: number) => {
  if (!confirm('确定删除此投递记录？')) return
  try {
    const res = await fetch(`/api/v1/applications/${appId}`, { method: 'DELETE' })
    if (res.ok) {
      selectedApp.value = null
      await loadApplications()
    }
  } catch (e) {
    console.error('Failed to delete', e)
  }
}

const submitNewApp = async () => {
  if (!newForm.value.company_name || !newForm.value.position) return
  try {
    // 1. 创建公司
    const cRes = await fetch('/api/v1/companies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newForm.value.company_name, city: newForm.value.city })
    })
    const comp = await cRes.json()

    // 2. 创建投递
    await fetch('/api/v1/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_id: comp.id,
        position: newForm.value.position,
        resume_version: newForm.value.resume_version,
        status: '待投递'
      })
    })

    showAddModal.value = false
    newForm.value = { company_name: '', position: '', city: '苏州', resume_version: '自动化版' }
    await loadApplications()
  } catch (e) {
    console.error('Failed to create app', e)
  }
}
</script>
