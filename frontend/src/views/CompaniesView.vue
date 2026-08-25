<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-bold text-slate-100">企业与机会清单</h2>
        <p class="text-xs text-slate-400">支持 S/A/B/C Tier 分级筛选、行业/城市过滤及官网直达</p>
      </div>
      <div class="flex items-center gap-2.5">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索企业名称 / 行业..." 
          class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none w-56"
        />
        <select v-model="selectedTier" class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none">
          <option value="">全部 Tier 评级</option>
          <option value="S">Tier S (龙头/天花板)</option>
          <option value="A">Tier A (优质工控/高薪)</option>
          <option value="B">Tier B (稳健/对口)</option>
        </select>
      </div>
    </div>

    <!-- Company Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div 
        v-for="company in filteredCompanies" 
        :key="company.id"
        class="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 hover:border-blue-500/40 transition shadow-sm"
      >
        <div class="flex items-center justify-between">
          <span class="font-bold text-sm text-slate-100">{{ company.name }}</span>
          <span :class="[
            'text-[10px] font-mono px-2 py-0.5 rounded font-bold',
            company.tier === 'S' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' :
            company.tier === 'A' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
            'bg-slate-800 text-slate-400'
          ]">Tier {{ company.tier }}</span>
        </div>

        <div class="space-y-1 text-xs text-slate-400">
          <p>🏭 行业: {{ company.industry || '工业自动化 / 智能制造' }}</p>
          <p>📍 城市: {{ company.city || '苏州 / 深圳 / 全国' }}</p>
          <p v-if="company.notes" class="text-[11px] text-slate-500 line-clamp-2 mt-1">{{ company.notes }}</p>
        </div>

        <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <a 
            v-if="company.careers_url" 
            :href="company.careers_url" 
            target="_blank" 
            class="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            校招官网 ↗
          </a>
          <span v-else class="text-[11px] text-slate-600">无外部直链</span>
          <span class="text-[10px] text-slate-500 font-mono">{{ company.scale || '1000人以上' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const companies = ref<any[]>([])
const searchQuery = ref('')
const selectedTier = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/companies')
    if (res.ok) {
      companies.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch companies', e)
  }
})

const filteredCompanies = computed(() => {
  return companies.value.filter(c => {
    const matchesSearch = !searchQuery.value || c.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || (c.industry && c.industry.includes(searchQuery.value))
    const matchesTier = !selectedTier.value || c.tier === selectedTier.value
    return matchesSearch && matchesTier
  })
})
</script>
