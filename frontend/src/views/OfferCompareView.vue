<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div>
      <h2 class="text-base font-bold text-slate-100">多 Offer 综合价值对比分析器</h2>
      <p class="text-xs text-slate-400">综合测算月薪、年终奖、12% 顶格公积金、到手收入与 30 岁置业财务潜力</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Calculator Inputs -->
      <div class="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <h3 class="text-sm font-bold text-slate-200">Offer 薪资与福利参数</h3>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-slate-400 mb-1">月薪 Base (元)</label>
            <input v-model.number="form.monthly_base" type="number" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-slate-400 mb-1">薪数 (月)</label>
              <input v-model.number="form.months" type="number" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
            </div>
            <div>
              <label class="block text-slate-400 mb-1">公积金缴纳比例</label>
              <select v-model.number="form.housing_fund_rate" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none">
                <option :value="0.12">12% (顶格缴纳 - 推荐)</option>
                <option :value="0.08">8% (中等标准)</option>
                <option :value="0.05">5% (最低标准)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">工作城市</label>
            <input v-model="form.city" type="text" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-100 outline-none" />
          </div>

          <button @click="calculate" class="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition mt-2 cursor-pointer">
            重新计算综合价值
          </button>
        </div>
      </div>

      <!-- Result Breakdown Card -->
      <div class="p-5 bg-gradient-to-br from-slate-900 via-slate-900/90 to-blue-950/30 border border-blue-500/20 rounded-xl space-y-4">
        <h3 class="text-sm font-bold text-blue-400">综合财务与买房潜力测算</h3>

        <div v-if="result" class="space-y-3 text-xs">
          <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 flex items-center justify-between">
            <span class="text-slate-400">税前年薪总包 (Gross):</span>
            <span class="text-base font-bold text-slate-100 font-mono">￥{{ result.annual_gross?.toLocaleString() }}</span>
          </div>

          <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 flex items-center justify-between">
            <span class="text-slate-400">预估税后到手现金:</span>
            <span class="text-base font-bold text-emerald-400 font-mono">￥{{ result.annual_net?.toLocaleString() }}</span>
          </div>

          <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 flex items-center justify-between">
            <span class="text-slate-400">年度公积金总额 (双边入账):</span>
            <span class="text-base font-bold text-amber-400 font-mono">￥{{ result.annual_housing_fund?.toLocaleString() }}</span>
          </div>

          <div class="p-3.5 bg-blue-600/10 border border-blue-500/30 rounded-lg space-y-1">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-200">综合总价值 Package:</span>
              <span class="text-lg font-extrabold text-blue-400 font-mono">￥{{ result.total_benefit_package?.toLocaleString() }}</span>
            </div>
            <p class="text-[11px] text-slate-400 mt-1">{{ result.city_rating }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const form = ref({
  monthly_base: 22000,
  months: 15,
  housing_fund_rate: 0.12,
  city: '苏州'
})

const result = ref<any>(null)

const calculate = async () => {
  try {
    const res = await fetch('/api/v1/compare/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (res.ok) {
      result.value = await res.json()
    }
  } catch (e) {
    console.error('Calculate failed', e)
  }
}

onMounted(() => {
  calculate()
})
</script>
