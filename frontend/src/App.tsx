import React, { useState, useEffect } from 'react';
import { JobBoard } from './components/JobBoard';
import { RecommendationPanel } from './components/RecommendationPanel';
import { KanbanBoard } from './components/KanbanBoard';
import { ResumeWorkbench } from './components/ResumeWorkbench';
import { JobItem } from './types';
import { Briefcase, Sparkles, LayoutGrid, FileText, ShieldCheck, Flame } from 'lucide-react';
import packageJson from '../package.json';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'recs' | 'kanban' | 'resumes'>('jobs');
  const [selectedJobForAi, setSelectedJobForAi] = useState<JobItem | null>(null);
  const [appVersion, setAppVersion] = useState<string>(packageJson.version || '0.1.0');

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
  }, []);

  const handleSelectJobForAi = (job: JobItem) => {
    setSelectedJobForAi(job);
    setActiveTab('recs');
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
      iconColor: 'text-purple-400',
    },
    {
      id: 'kanban' as const,
      label: '投递进展看板',
      icon: LayoutGrid,
      iconColor: 'text-amber-400',
    },
    {
      id: 'resumes' as const,
      label: '简历多版本工作台',
      icon: FileText,
      iconColor: 'text-emerald-400',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#0a0b10] text-[#f3f4f6]">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 bg-[#11131c]/90 backdrop-blur-md border-b border-[#24283b] shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-500/20">
              <Briefcase className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-base leading-tight text-white tracking-wide">
                  JHTracker
                </h1>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-500/30 font-mono">
                  v{appVersion}
                </span>
              </div>
              <p className="text-[10px] font-medium text-[#9ca3af]">
                AI 本地求职与人在环路决策管理平台
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.15)] font-semibold'
                      : 'text-[#9ca3af] hover:text-white hover:bg-[#151824] border border-transparent'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : item.iconColor}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 bg-emerald-950/40 px-3 py-1 rounded-full border border-emerald-500/30 shadow-sm">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>本地隐私隔离模式 (~/.JHTracker)</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
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
      <footer className="py-4 text-center text-xs border-t bg-[#0a0b10] border-[#24283b] text-[#6b7280] flex items-center justify-center gap-2">
        <span>JHTracker · 本地 AI 智能求职求贤追踪与推荐平台</span>
        <span className="text-[#3b4252]">•</span>
        <span className="font-mono text-[#4b5563]">v{appVersion}</span>
      </footer>
    </div>
  );
};
