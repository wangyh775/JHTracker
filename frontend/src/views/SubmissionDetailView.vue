<template>
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
