<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div>
      <h2 class="text-base font-bold text-slate-100">Agent 行为与决策审计轨迹</h2>
      <p class="text-xs text-slate-400">查看 Hermes 后台定时搜寻任务、打分评估与防重跳过的完整可解释性日志</p>
    </div>

    <div class="space-y-3">
      <div 
        v-for="trace in traces" 
        :key="trace.id"
        class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-xs"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-bold text-blue-400 font-mono">{{ trace.agent_name }}</span>
            <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">{{ trace.action }}</span>
          </div>
          <span class="text-[11px] text-slate-500 font-mono">{{ trace.created_at }}</span>
        </div>

        <div v-if="trace.details" class="p-2.5 bg-slate-950/80 rounded border border-slate-800/80 text-[11px] font-mono text-slate-300 overflow-x-auto">
          {{ trace.details }}
        </div>
      </div>

      <div v-if="!traces.length" class="text-center py-10 text-xs text-slate-500">
        暂无 Agent 执行日志记录
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const traces = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/traces')
    if (res.ok) {
      traces.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to load traces', e)
  }
})
</script>
