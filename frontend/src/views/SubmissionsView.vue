<template>
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
                  :to="`/submissions/${sub.id}`" 
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
