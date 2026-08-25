<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header & AI Daily Briefing Card -->
    <div class="p-5 rounded-2xl bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-slate-900/60 border border-blue-500/20 shadow-xl space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="text-xl">💡</span>
          <div>
            <h2 class="text-sm font-bold text-slate-100 flex items-center gap-2">
              AI Daily Briefing (每日求职智能简报)
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-mono">Agent Assistant</span>
            </h2>
            <p class="text-xs text-slate-400">已为你自动聚合 7 天未响应投递与待审批高匹配推荐</p>
          </div>
        </div>
        <span class="text-xs text-slate-400 font-mono">{{ todayStr }}</span>
      </div>

      <!-- Briefing Sub-cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 待 Follow-up 预警 -->
        <div class="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-xs">
            <span class="font-semibold text-amber-400 flex items-center gap-1.5">
              <span>⏳</span> 超 7 天无响应待 Follow-up
            </span>
            <span class="text-[11px] text-slate-500 font-mono">{{ briefing.stale_unanswered?.length || 0 }} 项</span>
          </div>
          <div v-if="briefing.stale_unanswered?.length" class="space-y-1.5">
            <div 
              v-for="item in briefing.stale_unanswered" 
              :key="item.id" 
              class="flex items-center justify-between text-xs p-2 rounded bg-slate-800/40"
            >
              <span class="text-slate-200 font-medium">{{ item.position }}</span>
              <span class="text-amber-400/90 text-[11px]">已过 {{ item.days_elapsed }} 天</span>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500 text-center py-2">
            ✓ 暂无超时未响应投递
          </div>
        </div>

        <!-- 高分待审批推荐 -->
        <div class="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-xs">
            <span class="font-semibold text-emerald-400 flex items-center gap-1.5">
              <span>⭐</span> 高匹配度待审批推荐 (≥80分)
            </span>
            <span class="text-[11px] text-slate-500 font-mono">{{ briefing.high_match_pending?.length || 0 }} 个新岗位</span>
          </div>
          <div v-if="briefing.high_match_pending?.length" class="space-y-1.5">
            <div 
              v-for="item in briefing.high_match_pending" 
              :key="item.id" 
              class="flex items-center justify-between text-xs p-2 rounded bg-slate-800/40"
            >
              <span class="text-slate-200 font-medium truncate max-w-[200px]">{{ item.position }}</span>
              <span class="text-emerald-400 font-mono font-bold">{{ item.match_score }}分</span>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500 text-center py-2">
            ✓ 暂无待审批推荐，可前往决策收件箱查看
          </div>
        </div>
      </div>
    </div>

    <!-- Analytics KPI Row -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3.5">
      <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-center space-y-1">
        <span class="text-xs text-slate-400">目标企业数</span>
        <p class="text-2xl font-bold text-slate-100 font-mono">{{ briefing.stats?.total_companies || 0 }}</p>
      </div>
      <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-center space-y-1">
        <span class="text-xs text-slate-400">已投递简历</span>
        <p class="text-2xl font-bold text-blue-400 font-mono">{{ briefing.stats?.applied_count || 0 }}</p>
      </div>
      <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-center space-y-1">
        <span class="text-xs text-slate-400">技术笔面试中</span>
        <p class="text-2xl font-bold text-amber-400 font-mono">{{ briefing.stats?.interview_count || 0 }}</p>
      </div>
      <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-center space-y-1">
        <span class="text-xs text-slate-400">待审批岗位</span>
        <p class="text-2xl font-bold text-purple-400 font-mono">{{ briefing.stats?.pending_approval || 0 }}</p>
      </div>
      <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-center space-y-1 col-span-2 md:col-span-1">
        <span class="text-xs text-slate-400">已收获 Offer</span>
        <p class="text-2xl font-bold text-emerald-400 font-mono">{{ briefing.stats?.offer_count || 0 }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const briefing = ref<any>({ stats: {}, stale_unanswered: [], high_match_pending: [] })
const todayStr = new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', weekday: 'short' })

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/dashboard/briefing')
    if (res.ok) {
      briefing.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch dashboard briefing', e)
  }
})
</script>
