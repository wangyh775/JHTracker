import React, { useState } from 'react';
import { Activity, Clock, Sliders, ChevronDown, ChevronUp, Database, Check } from 'lucide-react';

export interface SpiderSourceOption {
  id: string;
  name: string;
  description: string;
  supportsDays?: boolean;
}

export const AVAILABLE_SPIDER_SOURCES: SpiderSourceOption[] = [
  {
    id: 'fangzhou',
    name: '求职方舟',
    description: '全网校招聚合数据源',
    supportsDays: true,
  },
  {
    id: 'wondercv',
    name: '超级简历',
    description: '名企名校校招网申投递列表',
    supportsDays: false,
  },
  {
    id: 'nowcoder',
    name: '牛客网',
    description: '互联网/IT校招日程广场',
    supportsDays: true,
  },
];

interface FloatingStatsCardProps {
  totalJobs: number;
  visitedCount: number;
  syncDays: number;
  onSyncDaysChange: (days: number) => void;
  selectedSources?: string[];
  onSelectedSourcesChange?: (sources: string[]) => void;
  onSyncSpider?: () => void;
  spiderRunning?: boolean;
}

const SYNC_DAY_OPTIONS = [
  { label: '近7天', value: 7 },
  { label: '近15天', value: 15 },
  { label: '近30天', value: 30 },
  { label: '近45天', value: 45 },
  { label: '近90天', value: 90 },
];

export const FloatingStatsCard: React.FC<FloatingStatsCardProps> = ({
  totalJobs,
  visitedCount,
  syncDays,
  onSyncDaysChange,
  selectedSources = ['fangzhou'],
  onSelectedSourcesChange,
  onSyncSpider,
  spiderRunning = false,
}) => {
  // Default to collapsed button
  const [isOpen, setIsOpen] = useState(false);

  const toggleSource = (sourceId: string) => {
    if (!onSelectedSourcesChange) return;
    if (selectedSources.includes(sourceId)) {
      // Keep at least 1 source selected
      if (selectedSources.length > 1) {
        onSelectedSourcesChange(selectedSources.filter((id) => id !== sourceId));
      }
    } else {
      onSelectedSourcesChange([...selectedSources, sourceId]);
    }
  };

  const selectedSourceNames = AVAILABLE_SPIDER_SOURCES.filter((s) =>
    selectedSources.includes(s.id)
  )
    .map((s) => s.name)
    .join('、');

  return (
    <div className="fixed bottom-6 right-6 z-40 font-sans text-gray-200">
      {/* Collapsed Pill Button & Quick Run Trigger */}
      {!isOpen && (
        <div className="flex items-center gap-1.5 p-1 bg-[#11131c]/95 hover:bg-[#141724] backdrop-blur-md border border-[#24283b] hover:border-cyan-500/40 rounded-full shadow-lg transition-all duration-200">
          {/* Main Pill: Click to expand settings */}
          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-full text-xs font-semibold text-gray-100 hover:text-cyan-300 transition-colors cursor-pointer"
            title="点击展开采集配置"
          >
            <div className="relative flex items-center justify-center">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>采集引擎</span>
            </div>
            <div className="flex items-center gap-1 pl-1.5 border-l border-gray-700/60 text-[11px] font-mono text-cyan-400">
              <span>{totalJobs}</span>
              <span className="text-gray-500">岗</span>
            </div>
            <ChevronUp className="w-3.5 h-3.5 text-gray-400 hover:text-cyan-300 transition-transform" />
          </button>

          {/* Quick Run Button: Directly triggers spider with current configuration */}
          {onSyncSpider && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                if (!spiderRunning && selectedSources.length > 0) {
                  onSyncSpider();
                }
              }}
              disabled={spiderRunning || selectedSources.length === 0}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                spiderRunning
                  ? 'bg-cyan-950/70 text-cyan-300 border border-cyan-500/50 cursor-wait'
                  : selectedSources.length === 0
                  ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                  : 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 font-semibold cursor-pointer active:scale-95 shadow-sm'
              }`}
              title={`直接开始同步当前选中的 ${selectedSources.length} 个渠道 (近${syncDays}天)`}
            >
              <Activity className={`w-3.5 h-3.5 ${spiderRunning ? 'animate-spin' : ''}`} />
              <span>{spiderRunning ? '采集同步中...' : '立即采集'}</span>
            </button>
          )}
        </div>
      )}

      {/* Expanded Panel */}
      {isOpen && (
        <div className="bg-[#11131c]/95 backdrop-blur-md border border-[#24283b] rounded-2xl p-4 shadow-xl w-84 text-gray-200 transition-all duration-200">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-cyber pb-2.5 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
              <span className="text-xs font-semibold text-gray-100">全网岗位智能采集配置</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-cyan-400/80 font-mono bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-500/20">
                LOCAL-FIRST
              </span>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-200 hover:bg-[#1a1d2d] transition-colors"
                title="收起为按钮"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-[#0a0a0e] p-2.5 rounded-lg border border-cyber">
              <div className="text-[10px] text-gray-400">已收录网申</div>
              <div className="text-base font-bold font-mono text-cyan-400 mt-0.5">{totalJobs}</div>
            </div>
            <div className="bg-[#0a0a0e] p-2.5 rounded-lg border border-cyber">
              <div className="text-[10px] text-gray-400">已浏览足迹</div>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">{visitedCount}</div>
            </div>
          </div>

          {/* Source Selection (Multiple Channels) */}
          <div className="bg-[#0a0a0e]/80 border border-cyber rounded-lg p-2.5 mb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-[11px] text-gray-300 font-medium">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                <span>数据抓取途径</span>
              </div>
              <span className="text-[10px] text-gray-400">
                已启用 {selectedSources.length} 个渠道
              </span>
            </div>
            <div className="space-y-1.5">
              {AVAILABLE_SPIDER_SOURCES.map((source) => {
                const isSelected = selectedSources.includes(source.id);
                return (
                  <div
                    key={source.id}
                    onClick={() => !spiderRunning && toggleSource(source.id)}
                    className={`flex items-center justify-between px-2.5 py-1.5 rounded-md border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-cyan-950/40 border-cyan-500/50 text-gray-100 shadow-sm'
                        : 'bg-[#151722]/60 border-cyber text-gray-400 hover:text-gray-300 hover:border-gray-700'
                    } ${spiderRunning ? 'opacity-60 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3.5 h-3.5 rounded flex items-center justify-center border transition-all ${
                          isSelected
                            ? 'bg-cyan-500 border-cyan-400 text-black'
                            : 'border-gray-600 bg-black/40'
                        }`}
                      >
                        {isSelected && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                      </div>
                      <span className="font-medium text-[11px]">{source.name}</span>
                    </div>
                    <span className="text-[10px] text-gray-500 truncate max-w-[120px]">
                      {source.description}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Time Window Constraint Setting */}
          <div className="bg-[#0a0a0e]/80 border border-cyber rounded-lg p-2.5 mb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-[11px] text-gray-300 font-medium">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>爬取时效范围</span>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-500/30">
                最近 {syncDays} 天
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1">
              {SYNC_DAY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  disabled={spiderRunning}
                  onClick={() => onSyncDaysChange(opt.value)}
                  className={`py-1 text-[10px] rounded transition-all text-center ${
                    syncDays === opt.value
                      ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                      : 'bg-[#151722] hover:bg-[#1f2233] text-gray-400 hover:text-gray-200 border border-cyber'
                  } ${spiderRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-1.5">
            {onSyncSpider && (
              <button
                onClick={onSyncSpider}
                disabled={spiderRunning || selectedSources.length === 0}
                className={`w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                  spiderRunning || selectedSources.length === 0
                    ? 'bg-slate-800 text-gray-400 cursor-not-allowed border border-cyber'
                    : 'bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 hover:border-cyan-400 shadow-sm'
                }`}
              >
                <Activity className={`w-3.5 h-3.5 ${spiderRunning ? 'animate-spin text-cyan-400' : ''}`} />
                <span>
                  {spiderRunning
                    ? `正在同步[${selectedSourceNames || '渠道'}] (近${syncDays}天)...`
                    : selectedSources.length === 0
                    ? '请至少勾选一个渠道'
                    : `同步已选渠道 [${selectedSources.length}] (近${syncDays}天)`}
                </span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
