/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#0a0b10',          // 全局最深底色
          surface: '#11131c',     // 一级卡片/面板底色
          card: '#151824',        // 二级卡片/嵌入区域底色
          muted: '#1b1e2e',       // 悬浮/激活色块
          border: '#1e2235',      // 标准边框（低调暗蓝）
          borderLight: '#282d45', // 高亮/悬浮边框
          text: '#f3f4f6',        // 主文字
          subtext: '#9ca3af',     // 次级说明文字
          dim: '#6b7280',         // 弱化占位文字
          cyan: '#06b6d4',        // 品牌赛博青
          cyanGlow: 'rgba(6, 182, 212, 0.25)',
          purple: '#8b5cf6',      // 辅助科技紫
          emerald: '#10b981',     // 积极/推荐绿
          amber: '#f59e0b',       // 提醒/进行中黄
          rose: '#f43f5e',        // 预警/归档红
        },
      },
      boxShadow: {
        'cyber-sm': '0 0 10px -2px rgba(6, 182, 212, 0.15)',
        'cyber-md': '0 0 15px -3px rgba(6, 182, 212, 0.25)',
        'purple-sm': '0 0 10px -2px rgba(139, 92, 246, 0.2)',
      }
    },
  },
  plugins: [],
}
