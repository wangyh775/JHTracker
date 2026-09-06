import React, { useState, useEffect } from 'react';
import { Search, Flame, Building, GraduationCap, Briefcase, Sparkles, X } from 'lucide-react';
import { FangzhouCategory } from '../types';

interface FangzhouTableHeaderProps {
  activeCategory: FangzhouCategory;
  onSelectCategory: (category: FangzhouCategory) => void;
  keyword: string;
  onKeywordChange: (val: string) => void;
  hasReferralOnly: boolean;
  onToggleReferralOnly: () => void;
  hideVisited: boolean;
  onToggleHideVisited: () => void;
  visitedCount: number;
}

const CATEGORY_TABS: { key: FangzhouCategory; label: string; icon: React.ReactNode }[] = [
  { key: 'latest', label: '24h最新网申', icon: <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> },
  { key: 'hot', label: '届热门校招', icon: <Flame className="w-3.5 h-3.5 text-amber-400" /> },
  { key: 'state_owned', label: '国企央企汇总', icon: <Building className="w-3.5 h-3.5 text-blue-400" /> },
  { key: 'intern', label: '大厂实习汇总', icon: <Briefcase className="w-3.5 h-3.5 text-violet-400" /> },
  { key: 'all', label: '全部岗位', icon: <GraduationCap className="w-3.5 h-3.5 text-emerald-400" /> },
];

export const FangzhouTableHeader: React.FC<FangzhouTableHeaderProps> = ({
  activeCategory,
  onSelectCategory,
  keyword,
  onKeywordChange,
  hasReferralOnly,
  onToggleReferralOnly,
  hideVisited,
  onToggleHideVisited,
  visitedCount,
}) => {
  const [localKeyword, setLocalKeyword] = useState(keyword);

  useEffect(() => {
    setLocalKeyword(keyword);
  }, [keyword]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localKeyword !== keyword) {
        onKeywordChange(localKeyword);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [localKeyword, keyword, onKeywordChange]);

  const handleClear = () => {
    setLocalKeyword('');
    onKeywordChange('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onKeywordChange(localKeyword);
    }
  };

  return (
    <div className="w-full bg-cyber-card border border-cyber rounded-xl p-3.5 space-y-3 shadow-lg">
      {/* Category Tabs & Quick Search */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Category Tabs */}
        <div className="flex items-center flex-wrap gap-1 bg-[#0a0a0e] p-1 rounded-lg border border-cyber">
          {CATEGORY_TABS.map((tab) => {
            const isActive = activeCategory === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onSelectCategory(tab.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Search Bar with Debounce & Enter trigger */}
        <div className="relative w-full md:w-72">
          <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="搜索职位 / 城市 / 公司名称 (按回车直接搜)..."
            value={localKeyword}
            onChange={(e) => setLocalKeyword(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full pl-9 pr-8 py-1.5 bg-[#0a0a0e] border border-cyber rounded-lg text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500/80 transition-colors"
          />
          {localKeyword && (
            <button
              onClick={handleClear}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              title="清除输入"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Quick Filter Toggles */}
      <div className="flex items-center justify-between pt-2 border-t border-cyber/70 text-xs">
        <div className="flex items-center gap-4">
          {/* Has Referral Toggle */}
          <label className="flex items-center gap-1.5 cursor-pointer select-none text-gray-300 hover:text-cyan-300 transition-colors">
            <input
              type="checkbox"
              checked={hasReferralOnly}
              onChange={onToggleReferralOnly}
              className="rounded bg-slate-900 border-cyber text-cyan-500 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5 cursor-pointer"
            />
            <span>仅看带内推码</span>
          </label>

          {/* Hide Visited Toggle */}
          <label className="flex items-center gap-1.5 cursor-pointer select-none text-gray-300 hover:text-cyan-300 transition-colors">
            <input
              type="checkbox"
              checked={hideVisited}
              onChange={onToggleHideVisited}
              className="rounded bg-slate-900 border-cyber text-cyan-500 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5 cursor-pointer"
            />
            <span>隐藏已看网申</span>
            {visitedCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-gray-400 font-mono">
                {visitedCount}
              </span>
            )}
          </label>
        </div>
      </div>
    </div>
  );
};
