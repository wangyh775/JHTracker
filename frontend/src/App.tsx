import React, { useState, useEffect } from 'react';
import { LandingPortal } from './components/LandingPortal';
import { JobBoard } from './components/JobBoard';
import { RecommendationPanel } from './components/RecommendationPanel';
import { KanbanBoard } from './components/KanbanBoard';
import { ResumeWorkbench } from './components/ResumeWorkbench';
import { JobItem } from './types';
import { JHTrackerLogo } from './components/JHTrackerLogo';
import {
  Sparkles,
  LayoutGrid,
  FileText,
  ShieldCheck,
  Flame,
  Database,
  Compass,
} from 'lucide-react';
import packageJson from '../package.json';

const STORAGE_KEY_CURTAIN_SEEN = 'jhtracker_curtain_unveiled';

export const App: React.FC = () => {
  // Check if user already unveiled the curtain in this browser session
  const [isCurtainOpen, setIsCurtainOpen] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem(STORAGE_KEY_CURTAIN_SEEN) !== 'true';
    } catch {
      return true;
    }
  });

  const [activeTab, setActiveTab] = useState<'jobs' | 'recs' | 'kanban' | 'resumes'>('jobs');
  const [selectedJobForAi, setSelectedJobForAi] = useState<JobItem | null>(null);
  const [appVersion, setAppVersion] = useState<string>(packageJson.version || '0.1.0');
  const [globalStats, setGlobalStats] = useState<{ total_jobs: number; total_companies: number }>({
    total_jobs: 23231,
    total_companies: 3182,
  });

  useEffect(() => {
    fetch('/api/system/version')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.version) {
          setAppVersion(data.version);
        }
      })
      .catch(() => {
        // Fallback to static package.json version
      });

    fetch('/api/jobs/stats')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.total_jobs && data?.total_companies) {
          setGlobalStats({
            total_jobs: data.total_jobs,
            total_companies: data.total_companies,
          });
        }
      })
      .catch(() => {
        // Keep initial fallback stats
      });
  }, []);

  const handleSelectJobForAi = (job: JobItem) => {
    setSelectedJobForAi(job);
    setActiveTab('recs');
  };

  // When user clicks "Enter Workspace", unveil the curtain
  const handleEnterWorkspace = () => {
    setActiveTab('jobs');
    // Pull up the curtain with smooth animation
    setIsCurtainOpen(false);
    try {
      sessionStorage.setItem(STORAGE_KEY_CURTAIN_SEEN, 'true');
    } catch {
      // Storage unavailable
    }
  };

  // Re-open curtain if user wants to see the portal again by clicking Logo
  const handleReopenCurtain = () => {
    setIsCurtainOpen(true);
  };

  const navItems = [
    {
      id: 'jobs' as const,
      label: '校招网申大厅',
      icon: Flame,
      iconColor: 'text-cyan-400',
    },
    {
      id: 'recs' as const,
      label: '智能推荐 (HITL)',
      icon: Sparkles,
      iconColor: 'text-amber-400',
    },
    {
      id: 'kanban' as const,
      label: '投递进展看板',
      icon: LayoutGrid,
      iconColor: 'text-purple-400',
    },
    {
      id: 'resumes' as const,
      label: '简历多版本工作台',
      icon: FileText,
      iconColor: 'text-emerald-400',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#0a0b10] text-[#f3f4f6] relative">
      {/* Full-Screen Cyber Portal Curtain (Overlay on first launch) */}
      <LandingPortal
        isOpen={isCurtainOpen}
        totalJobs={globalStats.total_jobs}
        totalCompanies={globalStats.total_companies}
        onEnterWorkspace={handleEnterWorkspace}
      />

      {/* Navigation Header (Main Workspace) */}
      <header className="sticky top-0 z-40 bg-[#0e1017]/95 backdrop-blur-md border-b border-[#1f2438] shadow-xl">
        <div className="w-full max-w-[1880px] mx-auto px-3 sm:px-5 lg:px-7 h-16 flex items-center justify-between gap-4">
          {/* Enhanced Brand Logo Section - Clickable to lower curtain again */}
          <div
            onClick={handleReopenCurtain}
            className="group flex items-center gap-3 cursor-pointer select-none py-1 px-2 -ml-1.5 rounded-xl hover:bg-slate-800/40 transition-all duration-200"
            title="点击重新拉下赛博指挥舱帷幕"
          >
            <div className="relative">
              <JHTrackerLogo size={38} showCenterDot={true} />
              <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-[#0e1017]" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-cyan-400">
                  JHTracker
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-500/30 font-mono font-medium">
                  v{appVersion}
                </span>
                <span className="hidden sm:inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  ONLINE
                </span>
              </div>
              <p className="hidden md:block text-[11px] text-gray-400 group-hover:text-cyan-300/80 transition-colors">
                本地 AI 智能求职求贤追踪与推荐平台
              </p>
            </div>
          </div>

          {/* Central Workspace Tab Navigation (4 Core Workspaces) */}
          <nav className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto py-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-150 cursor-pointer ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-200 border border-cyan-500/40 shadow-sm font-semibold'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-[#151928] border border-transparent'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : item.iconColor}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status Indicator Area */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            {/* Curtain Pull-Down Quick Trigger */}
            <button
              onClick={handleReopenCurtain}
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-gray-400 hover:text-cyan-300 bg-[#141829] hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition-all cursor-pointer"
              title="拉下赛博门户首页"
            >
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
              <span>门户视口</span>
            </button>

            {/* Global Quick Job Counter */}
            <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#141829] border border-slate-800 text-[11px] text-gray-300 font-mono">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span>全库:</span>
              <strong className="text-cyan-400 font-semibold">{globalStats.total_jobs.toLocaleString()}</strong>
              <span className="text-gray-600">/</span>
              <strong className="text-purple-400 font-semibold">{globalStats.total_companies.toLocaleString()}</strong>
              <span className="text-gray-400 text-[10px]">企</span>
            </div>

            {/* Privacy Shield Pill */}
            <div
              className="flex items-center gap-1.5 text-[11px] text-emerald-400 bg-emerald-950/40 px-2.5 sm:px-3 py-1 rounded-full border border-emerald-500/30 shadow-sm"
              title="用户私有数据（简历、投递状态、权重）严格仅保存在本地 ~/.JHTracker/"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
              <span className="hidden sm:inline">物理隔离</span>
              <span className="text-emerald-300/70 font-mono text-[10px] hidden md:inline">(~/.JHTracker)</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area (Workspaces) */}
      <main className="flex-1 w-full max-w-[1880px] mx-auto px-2 sm:px-4 lg:px-6 py-4">
        {activeTab === 'jobs' && (
          <JobBoard
            onNavigateToKanban={() => setActiveTab('kanban')}
            onSelectJobForAi={handleSelectJobForAi}
          />
        )}
        {activeTab === 'recs' && (
          <RecommendationPanel
            initialJob={selectedJobForAi}
            onNavigateToKanban={() => setActiveTab('kanban')}
          />
        )}
        {activeTab === 'kanban' && <KanbanBoard />}
        {activeTab === 'resumes' && <ResumeWorkbench />}
      </main>

      {/* Footer */}
      <footer className="py-4 text-center text-xs border-t bg-[#0a0b10] border-[#1f2438] text-gray-500 flex items-center justify-center gap-2">
        <span>JHTracker · 本地 AI 智能求职求贤追踪与推荐平台</span>
        <span className="text-[#3b4252]">•</span>
        <span className="font-mono text-gray-500">v{appVersion}</span>
      </footer>
    </div>
  );
};
