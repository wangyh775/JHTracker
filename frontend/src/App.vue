<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
    <!-- Top Navigation Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/25">
          CT
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold tracking-tight text-white">Career Tracker OS</h1>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">v2.0 Pro</span>
          </div>
          <p class="text-xs text-slate-400">大连交大 • 机械工程硕士 • 2027届秋招全生命周期中枢</p>
        </div>
      </div>

      <!-- Actions & Floating Drawer Triggers -->
      <div class="flex items-center gap-3">
        <button 
          @click="showFeedbackDrawer = true"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600/15 hover:bg-emerald-600/25 text-emerald-400 border border-emerald-500/30 transition cursor-pointer"
        >
          <span>💡</span> 记录面试反馈
        </button>

        <button 
          @click="triggerGlobalAutofill"
          :disabled="isAutofilling"
          class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/20 transition disabled:opacity-50 cursor-pointer"
        >
          <span v-if="isAutofilling" class="animate-spin text-sm">⟳</span>
          <span v-else>⚡</span>
          一键预填网申
        </button>

        <button 
          @click="showClipboard = !showClipboard"
          :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition cursor-pointer', showClipboard ? 'bg-blue-600/20 text-blue-400 border-blue-500/40' : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200']"
        >
          <span>📋</span> 档案速查板
        </button>
      </div>
    </header>

    <!-- App Body: Sidebar + Dynamic Route Workspace + Optional Clipboard Drawer -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Navigation Sidebar -->
      <aside class="w-60 border-r border-slate-800/80 bg-slate-900/40 p-3 flex flex-col justify-between shrink-0">
        <div class="space-y-4">
          <!-- 1. 工作台与投递管线 -->
          <div>
            <span class="text-[10px] uppercase font-bold text-slate-500 px-3 tracking-wider">投递管线 PIPELINE</span>
            <nav class="space-y-1 mt-1">
              <router-link 
                to="/applications"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>📋</span> 投递总览 (表格/看板)
              </router-link>
              <router-link 
                to="/to-apply"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>🎯</span> 待投机会库 (4轨分发)
              </router-link>
              <router-link 
                to="/submissions"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>🛡️</span> 预填核对站 (Zero-Submit)
              </router-link>
            </nav>
          </div>

          <!-- 2. 机会库与决策 -->
          <div>
            <span class="text-[10px] uppercase font-bold text-slate-500 px-3 tracking-wider">机会与决策 DECISIONS</span>
            <nav class="space-y-1 mt-1">
              <router-link 
                to="/companies"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>🏢</span> 目标企业名录
              </router-link>
              <router-link 
                to="/dashboard"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>📊</span> 数据仪表盘 & 简报
              </router-link>
              <router-link 
                to="/compare"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>⚖️</span> Offer 综合性价比
              </router-link>
            </nav>
          </div>

          <!-- 3. 知识库与问答 -->
          <div>
            <span class="text-[10px] uppercase font-bold text-slate-500 px-3 tracking-wider">工具与知识库 TOOLKIT</span>
            <nav class="space-y-1 mt-1">
              <router-link 
                to="/qa"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>📖</span> 答辩与面试题库
              </router-link>
              <router-link 
                to="/traces"
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left cursor-pointer text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                active-class="bg-blue-600/15 text-blue-400 border border-blue-500/20 font-semibold"
              >
                <span>🕵️</span> Agent 审计轨迹
              </router-link>
            </nav>
          </div>
        </div>

        <!-- 4-Track System Overview Badge -->
        <div class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[11px] space-y-1.5">
          <div class="flex items-center justify-between text-slate-300 font-bold">
            <span>🎯 4 轨简历体系</span>
            <span class="text-blue-400 font-mono text-[10px]">Active</span>
          </div>
          <div class="grid grid-cols-2 gap-1 text-[10px] text-slate-400 font-medium">
            <span class="text-blue-400">🔵 控制算法</span>
            <span class="text-purple-400">🟣 嵌入式/固件</span>
            <span class="text-emerald-400">🟢 机电/电气</span>
            <span class="text-amber-400">🟠 机械/仿真</span>
          </div>
        </div>
      </aside>

      <!-- Main Dynamic Content Workspace (Router View) -->
      <main class="flex-1 overflow-y-auto p-6 bg-slate-950/90">
        <router-view />
      </main>

      <!-- Right Slide-Out Profile Clipboard Drawer -->
      <aside 
        v-if="showClipboard"
        class="w-96 border-l border-slate-800 bg-slate-900/95 p-4 flex flex-col justify-between shrink-0 shadow-2xl transition-all overflow-y-auto"
      >
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div class="flex items-center gap-2">
              <span class="text-base">📋</span>
              <h2 class="text-xs font-bold uppercase tracking-wider text-slate-200">个人求职档案速查板</h2>
            </div>
            <button @click="showClipboard = false" class="text-slate-400 hover:text-slate-200 text-xs cursor-pointer">✕</button>
          </div>

          <!-- Tab Selection for Profile Data -->
          <div class="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px]">
            <button 
              @click="profileTab = 'basic'"
              :class="['flex-1 py-1 rounded font-medium transition cursor-pointer', profileTab === 'basic' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200']"
            >
              基本信息
            </button>
            <button 
              @click="profileTab = 'tracks'"
              :class="['flex-1 py-1 rounded font-medium transition cursor-pointer', profileTab === 'tracks' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200']"
            >
              4轨话术
            </button>
            <button 
              @click="profileTab = 'projects'"
              :class="['flex-1 py-1 rounded font-medium transition cursor-pointer', profileTab === 'projects' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200']"
            >
              核心项目
            </button>
          </div>

          <!-- Tab 1: Basic Info -->
          <div v-if="profileTab === 'basic'" class="space-y-3">
            <div 
              v-for="item in basicProfileItems" 
              :key="item.label"
              class="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 hover:border-slate-700 transition"
            >
              <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span>{{ item.label }}</span>
                <button 
                  @click="copyToClipboard(item.value)" 
                  class="text-blue-400 hover:text-blue-300 font-medium cursor-pointer"
                >
                  复制
                </button>
              </div>
              <div class="text-xs text-slate-200 font-mono select-all break-all">{{ item.value }}</div>
            </div>
          </div>

          <!-- Tab 2: 4-Track Greetings -->
          <div v-else-if="profileTab === 'tracks'" class="space-y-3">
            <div 
              v-for="track in trackGreetings" 
              :key="track.name"
              class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 space-y-1.5"
            >
              <div class="flex items-center justify-between text-xs font-bold text-slate-200">
                <span>{{ track.icon }} {{ track.name }}</span>
                <button 
                  @click="copyToClipboard(track.text)"
                  class="text-[10px] text-blue-400 hover:text-blue-300 cursor-pointer font-normal"
                >
                  复制整段话术
                </button>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed select-all">
                {{ track.text }}
              </p>
            </div>
          </div>

          <!-- Tab 3: Key Projects -->
          <div v-else class="space-y-3">
            <div 
              v-for="proj in projectHighlights" 
              :key="proj.title"
              class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 space-y-1.5"
            >
              <div class="flex items-center justify-between text-xs font-bold text-slate-200">
                <span>{{ proj.title }}</span>
                <button 
                  @click="copyToClipboard(proj.summary)"
                  class="text-[10px] text-blue-400 hover:text-blue-300 cursor-pointer font-normal"
                >
                  复制摘要
                </button>
              </div>
              <div class="text-[10px] text-blue-400 font-mono">{{ proj.tech }}</div>
              <p class="text-[11px] text-slate-400 leading-relaxed select-all">
                {{ proj.summary }}
              </p>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-slate-800 text-[11px] text-slate-500 text-center">
          数据源自 <code>data/profile.md</code>
        </div>
      </aside>
    </div>

    <!-- Global Feedback Modal / Drawer -->
    <div v-if="showFeedbackDrawer" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>💡 记录面试/投递反馈与反思 (HITL)</span>
          </h3>
          <button @click="showFeedbackDrawer = false" class="text-slate-400 hover:text-white text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitFeedback" class="space-y-3.5 text-xs">
          <div>
            <label class="block text-slate-400 mb-1">企业 / 岗位名称 *</label>
            <input v-model="feedbackForm.company_name" required type="text" placeholder="例如：大疆创新 - 嵌入式驱动工程师" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-blue-500" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-slate-400 mb-1">反馈类型</label>
              <select v-model="feedbackForm.feedback_type" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-blue-500">
                <option value="interview_question">面试高频提问</option>
                <option value="technical_gap">技术差距/知识盲区</option>
                <option value="hr_negotiation">薪资/HR沟通点</option>
                <option value="rejection_reason">未通过复盘</option>
              </select>
            </div>
            <div>
              <label class="block text-slate-400 mb-1">对应 4 轨方向</label>
              <select v-model="feedbackForm.track" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-blue-500">
                <option value="控制算法">🔵 控制算法</option>
                <option value="自动化与嵌入式">🟣 自动化与嵌入式</option>
                <option value="机电一体化与电气">🟢 机电一体化与电气</option>
                <option value="机械结构与仿真">🟠 机械结构与仿真</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">反馈核心内容 / 面试点详情 *</label>
            <textarea v-model="feedbackForm.content" required rows="4" placeholder="记录面试官深入考查的问题、自己的回答亮点或遗漏点..." class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-blue-500"></textarea>
          </div>

          <div>
            <label class="block text-slate-400 mb-1">转化为长期记忆规则 (用于后续推荐调优)</label>
            <input v-model="feedbackForm.rule_summary" type="text" placeholder="例如：后续控制算法面试需重点强化 MPC 终端约束推导" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-blue-500" />
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button type="button" @click="showFeedbackDrawer = false" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition cursor-pointer">
              取消
            </button>
            <button type="submit" class="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow transition cursor-pointer">
              提交并存入知识库
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showClipboard = ref(false)
const showFeedbackDrawer = ref(false)
const isAutofilling = ref(false)
const profileTab = ref<'basic' | 'tracks' | 'projects'>('basic')

const feedbackForm = ref({
  company_name: '',
  feedback_type: 'interview_question',
  track: '控制算法',
  content: '',
  rule_summary: ''
})

const basicProfileItems = [
  { label: '姓名 / 学历', value: '大连交通大学 • 机械工程硕士 (2027届)' },
  { label: '本科院校 / 专业', value: '大连交通大学 • 车辆工程 (卓越工程师班)' },
  { label: '手机号码', value: '18840858168' },
  { label: '电子邮箱', value: '2900645068@qq.com' },
  { label: '意向工作城市', value: '苏州 / 深圳 / 杭州 / 上海 / 大连' },
  { label: '求职身份', value: '2027届应届毕业生' }
]

const trackGreetings = [
  {
    name: '控制算法方向',
    icon: '🔵',
    text: '您好！我是大连交通大学27届硕士生，主修机械工程，主攻MPC模型预测控制、EKF状态估计与机械臂轨迹规划。在研究生期间发表SCI/EI论文并持有发明专利，具备扎实的现代控制理论推导与仿真落地能力。期待能应聘贵司控制算法岗位！'
  },
  {
    name: '自动化与嵌入式方向',
    icon: '🟣',
    text: '您好！我是大连交通大学27届机械工程硕士，具备STM32H7/RK3588等主控芯片的嵌入式开发经验，深入掌握FreeRTOS多任务调度、EtherCAT总线与CAN/UART工业通讯，熟悉Klipper 3D打印固件架构及底层驱动移植，期待与您沟通嵌入式岗位！'
  },
  {
    name: '机电一体化与电气方向',
    icon: '🟢',
    text: '您好！我是大连交通大学27届硕士生，具有丰富的机电一体化系统集成与电气原理图设计经验，熟练使用EPLAN进行电气选型、驱动器配线与PLC逻辑调试，具备完整的机电整机调试交付经验，渴望加入贵司机电团队！'
  },
  {
    name: '机械结构与仿真方向',
    icon: '🟠',
    text: '您好！我是大连交通大学27届机械工程硕士，熟练掌握SolidWorks精密机械结构设计、CoreXY传动机构优化，并能熟练运用ANSYS/Fluent进行结构静力学与热流固耦合仿真分析，期待应聘贵司机械设计/结构工程师岗位！'
  }
]

const projectHighlights = [
  {
    title: '多自由度机械臂运动控制与MPC轨迹跟踪系统',
    tech: 'MATLAB / Python / ROS2 / MPC',
    summary: '建立了6-DOF机械臂刚柔耦合动力学模型，设计了基于连续离散混合系统的MPC控制器，末端轨迹跟踪误差控制在0.15mm以内，大幅提升了动态响应带宽。'
  },
  {
    title: '工业级高速 3D 打印机电气与运动控制平台',
    tech: 'STM32H7 / FreeRTOS / Klipper / CAN',
    summary: '独立完成整机电气控制架构与抗震机柜设计，基于STM32H7构建主控子系统，结合输入整形算法消除共振，实现了600mm/s高速打印与精准温控。'
  }
]

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  alert('已复制到剪贴板！')
}

async function triggerGlobalAutofill() {
  isAutofilling.value = true
  try {
    const res = await fetch('/api/autofill/run', { method: 'POST' })
    const data = await res.json()
    if (data.code === 200 && data.data?.submission_id) {
      router.push(`/submissions/${data.data.submission_id}`)
    } else {
      router.push('/submissions')
    }
  } catch (err) {
    console.error('Autofill failed:', err)
    router.push('/submissions')
  } finally {
    isAutofilling.value = false
  }
}

async function submitFeedback() {
  try {
    const res = await fetch('/api/feedbacks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedbackForm.value)
    })
    const data = await res.json()
    if (data.code === 200) {
      alert('已成功记录面试反馈并存入系统！')
      showFeedbackDrawer.value = false
      feedbackForm.value = {
        company_name: '',
        feedback_type: 'interview_question',
        track: '控制算法',
        content: '',
        rule_summary: ''
      }
    }
  } catch (err) {
    console.error('Submit feedback failed:', err)
  }
}
</script>
