<template>
  <div class="space-y-6">
    <!-- 头部栏 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          投递全生命周期总览
          <span class="text-xs px-2.5 py-0.5 rounded-full font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
            {{ totalItems }} 记录
          </span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">支持活跃/归档隔离、4轨工程分类筛选、极速批量变更与看板模式切换</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- 视图切换 -->
        <div class="bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 flex items-center gap-1">
          <button 
            @click="viewMode = 'table'" 
            :class="viewMode === 'table' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
          >
            <List class="w-3.5 h-3.5" />
            表格工作台
          </button>
          <button 
            @click="viewMode = 'kanban'" 
            :class="viewMode === 'kanban' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
          >
            <KanbanIcon class="w-3.5 h-3.5" />
            敏捷看板
          </button>
        </div>
        <button 
          @click="openCreateModal"
          class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition flex items-center gap-1.5 shadow-lg shadow-blue-500/20"
        >
          <Plus class="w-4 h-4" />
          新增投递
        </button>
      </div>
    </div>

    <!-- 过滤器与统计栏 -->
    <div class="bg-slate-800/50 backdrop-blur border border-slate-700/60 rounded-2xl p-4 space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- 活跃 / 归档 选项卡 -->
        <div class="flex items-center gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-700/40">
          <button
            @click="setTab('active')"
            :class="activeTab === 'active' ? 'bg-slate-700/80 text-white shadow' : 'text-slate-400 hover:text-slate-200'"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2"
          >
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            活跃进行中
          </button>
          <button
            @click="setTab('archived')"
            :class="activeTab === 'archived' ? 'bg-slate-700/80 text-white shadow' : 'text-slate-400 hover:text-slate-200'"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2"
          >
            <Archive class="w-3.5 h-3.5 text-slate-400" />
            历史归档库
          </button>
        </div>

        <!-- 4轨工程筛选器 -->
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            @click="setTrack('')"
            :class="selectedTrack === '' ? 'bg-slate-700 text-white' : 'bg-slate-800/60 text-slate-400 hover:bg-slate-700/50'"
            class="px-2.5 py-1 rounded-lg text-xs border border-slate-700/40 transition"
          >
            全部轨道
          </button>
          <button
            v-for="(info, key) in trackMap"
            :key="key"
            @click="setTrack(key)"
            :class="selectedTrack === key ? `${info.bg} ${info.text} border-current shadow-sm` : 'bg-slate-800/60 text-slate-400 hover:bg-slate-700/50 border-slate-700/40'"
            class="px-2.5 py-1 rounded-lg text-xs border transition flex items-center gap-1"
          >
            <span>{{ info.badge }}</span>
            <span>{{ info.short }}</span>
          </button>
        </div>

        <!-- 状态筛选与搜索 -->
        <div class="flex items-center gap-3 w-full md:w-auto">
          <div class="relative flex-1 md:w-56">
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索公司 / 岗位..." 
              class="w-full bg-slate-900/80 border border-slate-700/60 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              @input="onSearch"
            />
          </div>
          <select 
            v-model="selectedStatus" 
            @change="fetchApplications"
            class="bg-slate-900/80 border border-slate-700/60 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition"
          >
            <option value="">全部状态</option>
            <option value="待投递">待投递</option>
            <option value="已投递">已投递</option>
            <option value="笔试">笔试</option>
            <option value="面试">面试</option>
            <option value="通过">通过</option>
            <option value="已挂">已挂</option>
            <option value="Offer">Offer</option>
            <option value="已拒">已拒</option>
            <option value="超时自动归档">超时自动归档</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 表格工作台视图 -->
    <div v-if="viewMode === 'table'" class="bg-slate-800/50 backdrop-blur border border-slate-700/60 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-slate-900/60 border-b border-slate-700/60 text-slate-400 font-semibold uppercase tracking-wider">
              <th class="py-3.5 px-4">公司与城市</th>
              <th class="py-3.5 px-4">目标岗位</th>
              <th class="py-3.5 px-4">工程细分轨道</th>
              <th class="py-3.5 px-4">投递状态</th>
              <th class="py-3.5 px-4">使用简历版本</th>
              <th class="py-3.5 px-4">投递时间 / 更新</th>
              <th class="py-3.5 px-4 text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700/40 text-slate-300">
            <tr v-if="loading" class="text-center py-12">
              <td colspan="7" class="py-8 text-slate-500">
                <Loader2 class="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
                加载投递记录中...
              </td>
            </tr>
            <tr v-else-if="applications.length === 0" class="text-center py-12">
              <td colspan="7" class="py-8 text-slate-500">
                暂无匹配的投递记录
              </td>
            </tr>
            <tr 
              v-for="app in applications" 
              :key="app.id" 
              class="hover:bg-slate-700/30 transition group"
            >
              <!-- 公司与城市 -->
              <td class="py-3 px-4">
                <div class="font-medium text-white flex items-center gap-1.5">
                  {{ app.company?.name || '未知公司' }}
                  <span v-if="app.company?.city" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/60 text-slate-400 font-normal">
                    {{ app.company.city }}
                  </span>
                </div>
                <div class="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                  <span>{{ app.channel || '未知渠道' }}</span>
                  <span v-if="app.salary_min || app.salary_max">
                    {{ app.salary_min }}-{{ app.salary_max }}k
                  </span>
                </div>
              </td>

              <!-- 目标岗位 -->
              <td class="py-3 px-4">
                <div class="font-medium text-slate-200">{{ app.position }}</div>
                <div v-if="app.notes" class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                  {{ app.notes }}
                </div>
              </td>

              <!-- 4轨工程细分 -->
              <td class="py-3 px-4">
                <span 
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border"
                  :class="getTrackBadgeClass(app.track)"
                >
                  <span>{{ trackMap[app.track]?.badge || '⚙️' }}</span>
                  <span>{{ trackMap[app.track]?.name || app.track || '未分类' }}</span>
                </span>
              </td>

              <!-- 投递状态 -->
              <td class="py-3 px-4">
                <div class="relative inline-block">
                  <select
                    :value="app.status"
                    @change="updateStatus(app, ($event.target as HTMLSelectElement).value)"
                    class="appearance-none text-[11px] font-medium px-2.5 py-1 pr-6 rounded-lg border focus:outline-none cursor-pointer transition"
                    :class="getStatusBadgeClass(app.status)"
                  >
                    <option value="待投递">待投递</option>
                    <option value="已投递">已投递</option>
                    <option value="笔试">笔试</option>
                    <option value="面试">面试</option>
                    <option value="通过">通过</option>
                    <option value="已挂">已挂</option>
                    <option value="Offer">Offer</option>
                    <option value="已拒">已拒</option>
                    <option value="超时自动归档">超时自动归档</option>
                  </select>
                  <ChevronDown class="w-3 h-3 text-slate-400 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </td>

              <!-- 使用简历版本 -->
              <td class="py-3 px-4">
                <span class="text-slate-300 font-mono text-[11px] bg-slate-900/60 px-2 py-0.5 rounded border border-slate-700/40">
                  {{ app.resume_version || '默认简历' }}
                </span>
              </td>

              <!-- 时间 -->
              <td class="py-3 px-4 text-slate-400 text-[11px]">
                <div>{{ formatDate(app.applied_at || app.created_at) }}</div>
                <div class="text-[10px] text-slate-500">更新: {{ formatDate(app.updated_at) }}</div>
              </td>

              <!-- 操作 -->
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end gap-1.5 opacity-80 group-hover:opacity-100 transition">
                  <button 
                    v-if="!app.is_archived"
                    @click="archiveApp(app)"
                    title="归档"
                    class="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-700/50 rounded-lg transition"
                  >
                    <Archive class="w-3.5 h-3.5" />
                  </button>
                  <button 
                    v-else
                    @click="unarchiveApp(app)"
                    title="取消归档（恢复活跃）"
                    class="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-slate-700/50 rounded-lg transition"
                  >
                    <RotateCcw class="w-3.5 h-3.5" />
                  </button>
                  <button 
                    @click="openEditModal(app)"
                    title="编辑"
                    class="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700/50 rounded-lg transition"
                  >
                    <Edit3 class="w-3.5 h-3.5" />
                  </button>
                  <button 
                    @click="deleteApp(app)"
                    title="删除"
                    class="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页栏 -->
      <div class="py-3 px-4 bg-slate-900/60 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
        <div>
          共 {{ totalItems }} 条记录，当前第 {{ page }} / {{ totalPages }} 页
        </div>
        <div class="flex items-center gap-2">
          <button 
            :disabled="page <= 1"
            @click="changePage(page - 1)"
            class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/60 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700 transition"
          >
            上一页
          </button>
          <button 
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
            class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/60 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700 transition"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 看板视图组件 -->
    <div v-else>
      <KanbanView />
    </div>

    <!-- 编辑/新增 Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl space-y-4 p-6">
        <div class="flex items-center justify-between pb-3 border-b border-slate-700">
          <h3 class="text-lg font-bold text-white">
            {{ isEditing ? '编辑投递记录' : '新增投递记录' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-white transition">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="saveApplication" class="space-y-4 text-xs">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-slate-400 mb-1">公司 ID / 名称 *</label>
              <input 
                v-model.number="form.company_id" 
                type="number" 
                placeholder="公司 ID" 
                required 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-slate-400 mb-1">目标岗位 *</label>
              <input 
                v-model="form.position" 
                type="text" 
                placeholder="如: 控制算法工程师" 
                required 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-slate-400 mb-1">4轨细分领域 *</label>
              <select 
                v-model="form.track" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="control">🔵 控制算法 (MPC/EKF/运动控制)</option>
                <option value="embedded_auto">🟣 自动化与嵌入式 (STM32H7/RK3588/PLC)</option>
                <option value="mechatronics">🟢 机电一体化与电气 (EPLAN/选型联调)</option>
                <option value="mechanical_cfd">🟠 机械结构与仿真 (SolidWorks/Fluent)</option>
              </select>
            </div>
            <div>
              <label class="block text-slate-400 mb-1">当前状态 *</label>
              <select 
                v-model="form.status" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="待投递">待投递</option>
                <option value="已投递">已投递</option>
                <option value="笔试">笔试</option>
                <option value="面试">面试</option>
                <option value="通过">通过</option>
                <option value="已挂">已挂</option>
                <option value="Offer">Offer</option>
                <option value="已拒">已拒</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-slate-400 mb-1">投递渠道</label>
              <input 
                v-model="form.channel" 
                type="text" 
                placeholder="官网 / Boss / 牛客 / 内推" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-slate-400 mb-1">使用简历版本</label>
              <input 
                v-model="form.resume_version" 
                type="text" 
                placeholder="如: 王云鹤_简历_控制.pdf" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-slate-400 mb-1">薪资下限 (k)</label>
              <input 
                v-model.number="form.salary_min" 
                type="number" 
                placeholder="20" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-slate-400 mb-1">薪资上限 (k)</label>
              <input 
                v-model.number="form.salary_max" 
                type="number" 
                placeholder="35" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">备注 / 投递日志</label>
            <textarea 
              v-model="form.notes" 
              rows="3" 
              placeholder="记录关键要求、面试反馈或内推人..." 
              class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500"
            ></textarea>
          </div>

          <div class="flex justify-end gap-3 pt-3 border-t border-slate-700">
            <button 
              type="button" 
              @click="showModal = false" 
              class="px-4 py-2 rounded-xl bg-slate-700 text-slate-300 hover:bg-slate-600 transition"
            >
              取消
            </button>
            <button 
              type="submit" 
              class="px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-500 transition shadow-lg shadow-blue-500/20"
            >
              保存记录
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import KanbanView from './KanbanView.vue'
import { 
  List, 
  Kanban as KanbanIcon, 
  Plus, 
  Archive, 
  RotateCcw, 
  Search, 
  ChevronDown, 
  Edit3, 
  Trash2, 
  X, 
  Loader2 
} from 'lucide-vue-next'

const viewMode = ref<'table' | 'kanban'>('table')
const activeTab = ref<'active' | 'archived'>('active')
const selectedTrack = ref('')
const selectedStatus = ref('')
const searchQuery = ref('')
const page = ref(1)
const pageSize = ref(15)
const totalItems = ref(0)
const totalPages = ref(1)
const loading = ref(false)
const applications = ref<any[]>([])

const trackMap: Record<string, { name: string; short: string; badge: string; bg: string; text: string; border: string }> = {
  control: { name: '控制算法', short: '控制', badge: '🔵', bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  embedded_auto: { name: '自动化/嵌入式', short: '嵌入式', badge: '🟣', bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
  mechatronics: { name: '机电一体化', short: '机电', badge: '🟢', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  mechanical_cfd: { name: '机械/CFD仿真', short: '机械', badge: '🟠', bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
}

const showModal = ref(false)
const isEditing = ref(false)
const currentEditId = ref<number | null>(null)
const form = ref({
  company_id: 1,
  position: '',
  track: 'control',
  status: '已投递',
  channel: '官网',
  resume_version: '王云鹤_简历_控制.pdf',
  salary_min: 20,
  salary_max: 35,
  notes: ''
})

const getTrackBadgeClass = (track: string) => {
  const t = trackMap[track]
  return t ? `${t.bg} ${t.text} ${t.border}` : 'bg-slate-700/50 text-slate-400 border-slate-600'
}

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case '待投递': return 'bg-slate-700/60 text-slate-300 border-slate-600'
    case '已投递': return 'bg-blue-500/10 text-blue-400 border-blue-500/30'
    case '笔试': return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
    case '面试': return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    case '通过':
    case 'Offer': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    case '已挂':
    case '已拒':
    case '超时自动归档': return 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    default: return 'bg-slate-700/60 text-slate-400 border-slate-600'
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const setTab = (tab: 'active' | 'archived') => {
  activeTab.value = tab
  page.value = 1
  fetchApplications()
}

const setTrack = (track: string) => {
  selectedTrack.value = track
  page.value = 1
  fetchApplications()
}

const onSearch = () => {
  page.value = 1
  fetchApplications()
}

const changePage = (p: number) => {
  page.value = p
  fetchApplications()
}

const fetchApplications = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value.toString(),
      page_size: pageSize.value.toString(),
      active: (activeTab.value === 'active').toString()
    })
    if (selectedTrack.value) params.append('track', selectedTrack.value)
    if (selectedStatus.value) params.append('status', selectedStatus.value)
    if (searchQuery.value) params.append('search', searchQuery.value)

    const res = await fetch(`/api/v1/applications?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      applications.value = data.items || []
      totalItems.value = data.total || 0
      totalPages.value = data.pages || 1
    }
  } catch (err) {
    console.error('Fetch applications failed:', err)
  } finally {
    loading.value = false
  }
}

const updateStatus = async (app: any, newStatus: string) => {
  try {
    const res = await fetch(`/api/v1/applications/${app.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
    if (res.ok) {
      app.status = newStatus
      fetchApplications()
    }
  } catch (err) {
    console.error('Update status failed:', err)
  }
}

const archiveApp = async (app: any) => {
  try {
    const res = await fetch(`/api/v1/applications/${app.id}/archive`, { method: 'POST' })
    if (res.ok) {
      fetchApplications()
    }
  } catch (err) {
    console.error('Archive failed:', err)
  }
}

const unarchiveApp = async (app: any) => {
  try {
    const res = await fetch(`/api/v1/applications/${app.id}/unarchive`, { method: 'POST' })
    if (res.ok) {
      fetchApplications()
    }
  } catch (err) {
    console.error('Unarchive failed:', err)
  }
}

const deleteApp = async (app: any) => {
  if (!confirm(`确定要删除 ${app.company?.name || ''} - ${app.position} 的投递记录吗？`)) return
  try {
    const res = await fetch(`/api/v1/applications/${app.id}`, { method: 'DELETE' })
    if (res.ok) {
      fetchApplications()
    }
  } catch (err) {
    console.error('Delete failed:', err)
  }
}

const openCreateModal = () => {
  isEditing.value = false
  currentEditId.value = null
  form.value = {
    company_id: 1,
    position: '',
    track: 'control',
    status: '已投递',
    channel: '官网',
    resume_version: '王云鹤_简历_控制.pdf',
    salary_min: 20,
    salary_max: 35,
    notes: ''
  }
  showModal.value = true
}

const openEditModal = (app: any) => {
  isEditing.value = true
  currentEditId.value = app.id
  form.value = {
    company_id: app.company_id,
    position: app.position,
    track: app.track || 'control',
    status: app.status,
    channel: app.channel || '',
    resume_version: app.resume_version || '',
    salary_min: app.salary_min || 0,
    salary_max: app.salary_max || 0,
    notes: app.notes || ''
  }
  showModal.value = true
}

const saveApplication = async () => {
  try {
    const url = isEditing.value 
      ? `/api/v1/applications/${currentEditId.value}`
      : '/api/v1/applications'
    const method = isEditing.value ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (res.ok) {
      showModal.value = false
      fetchApplications()
    }
  } catch (err) {
    console.error('Save application failed:', err)
  }
}

onMounted(() => {
  fetchApplications()
})
</script>
