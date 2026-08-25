import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/applications'
  },
  {
    path: '/applications',
    name: 'applications',
    component: () => import('../views/ApplicationsView.vue'),
    meta: { title: '投递总览与工作台' }
  },
  {
    path: '/to-apply',
    name: 'to-apply',
    component: () => import('../views/ToApplyView.vue'),
    meta: { title: '待投递机会库 (4轨智能分发)' }
  },
  {
    path: '/submissions',
    name: 'submissions',
    component: () => import('../views/SubmissionsView.vue'),
    meta: { title: '网申预填核对站 (Zero-Submit)' }
  },
  {
    path: '/submissions/:id',
    name: 'submission-detail',
    component: () => import('../views/SubmissionDetailView.vue'),
    meta: { title: '网申逐项核对与状态回写' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '数据仪表盘 & AI简报' }
  },
  {
    path: '/companies',
    name: 'companies',
    component: () => import('../views/CompaniesView.vue'),
    meta: { title: '目标企业名录' }
  },
  {
    path: '/compare',
    name: 'compare',
    component: () => import('../views/OfferCompareView.vue'),
    meta: { title: 'Offer 综合性价比测算' }
  },
  {
    path: '/qa',
    name: 'qa',
    component: () => import('../views/AnswerBankView.vue'),
    meta: { title: '技术答辩与面试题库' }
  },
  {
    path: '/traces',
    name: 'traces',
    component: () => import('../views/TracesView.vue'),
    meta: { title: 'Agent 自动化审计轨迹' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
