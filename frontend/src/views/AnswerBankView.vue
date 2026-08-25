<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-bold text-slate-100">真实科研与算法答辩题库</h2>
        <p class="text-xs text-slate-400">基于大论文真实数据、EI论文、专利及谷瑞特横向提炼的技术深挖防御问答</p>
      </div>
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="搜索关键词 (如 MPC / Fluent / EKF)..." 
        class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none w-64"
      />
    </div>

    <!-- Question Cards -->
    <div class="space-y-4">
      <div 
        v-for="qa in filteredQA" 
        :key="qa.id"
        class="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 shadow-sm hover:border-blue-500/30 transition"
      >
        <div class="flex items-center gap-2.5">
          <span class="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold font-mono">
            {{ qa.category }}
          </span>
          <h3 class="text-sm font-bold text-slate-100">{{ qa.question }}</h3>
        </div>

        <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80">
          {{ qa.answer }}
        </p>

        <div class="flex items-center gap-2 pt-1">
          <span class="text-[11px] text-slate-500">匹配关键词:</span>
          <span 
            v-for="kw in qa.keywords" 
            :key="kw" 
            class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono"
          >
            #{{ kw }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const qaList = ref<any[]>([])
const searchQuery = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/answer-bank')
    if (res.ok) {
      qaList.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to load answer bank', e)
  }
})

const filteredQA = computed(() => {
  if (!searchQuery.value) return qaList.value
  const q = searchQuery.value.toLowerCase()
  return qaList.value.filter(item => 
    item.question.toLowerCase().includes(q) ||
    item.answer.toLowerCase().includes(q) ||
    item.keywords.some((k: string) => k.toLowerCase().includes(q))
  )
})
</script>
