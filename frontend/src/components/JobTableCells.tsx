import React, { useState } from 'react';
import { JobItem } from '../types';
import { Copy, Check, ExternalLink, Flame, Plus, Sparkles, Building2 } from 'lucide-react';

interface ReferralCellProps {
  referralCode?: string;
  copyTip?: string;
}

export const ReferralCell: React.FC<ReferralCellProps> = ({ referralCode, copyTip }) => {
  const [copied, setCopied] = useState(false);

  if (!referralCode) {
    return <span className="text-gray-500 text-xs">-</span>;
  }

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(referralCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-1.5 group/ref">
      <span className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 select-all">
        {referralCode}
      </span>
      <button
        onClick={handleCopy}
        title={copyTip || "点击复制内推码"}
        className="p-1 rounded hover:bg-slate-800 text-gray-400 hover:text-emerald-400 transition-colors"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
    </div>
  );
};

interface CompanyCellProps {
  company: string;
  popularLevel?: number;
  industry?: string;
  isVisited?: boolean;
}

export const CompanyCell: React.FC<CompanyCellProps> = ({ company, popularLevel = 1, isVisited }) => {
  return (
    <div className="flex items-center gap-2 max-w-[200px] h-full py-1">
      <div className={`w-7 h-7 rounded-lg border flex items-center justify-center flex-shrink-0 transition-colors ${
        isVisited 
          ? 'bg-slate-900/60 border-slate-800 text-gray-500' 
          : 'bg-slate-800/80 border-cyber text-cyan-400'
      }`}>
        <Building2 className="w-3.5 h-3.5" />
      </div>
      <div className="flex items-center gap-1.5 min-w-0">
        <span 
          title={company}
          className={`text-xs font-semibold truncate transition-colors ${
            isVisited ? 'text-gray-400 line-through decoration-slate-600' : 'text-gray-100 hover:text-cyan-400'
          }`}
        >
          {company}
        </span>
        {popularLevel >= 3 && (
          <span title="热门大厂/标杆企业" className="flex items-center text-amber-400 flex-shrink-0">
            <Flame className="w-3 h-3 fill-amber-400" />
          </span>
        )}
      </div>
    </div>
  );
};

interface ActionsCellProps {
  job: JobItem;
  onApplyClick: (job: JobItem) => void;
  onAddToKanban: (job: JobItem) => void;
  onAiAnalyze?: (job: JobItem) => void;
}

export const ActionsCell: React.FC<ActionsCellProps> = ({
  job,
  onApplyClick,
  onAddToKanban,
  onAiAnalyze
}) => {
  return (
    <div className="flex items-center justify-center gap-1.5">
      <button
        onClick={(e) => {
          e.stopPropagation();
          onApplyClick(job);
        }}
        className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 hover:border-cyan-400 text-xs font-medium transition-all shadow-sm"
      >
        <span>网申</span>
        <ExternalLink className="w-3 h-3" />
      </button>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onAddToKanban(job);
        }}
        title="同步至投递追踪看板"
        className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-gray-300 hover:text-white border border-slate-700 transition-colors"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>

      {onAiAnalyze && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAiAnalyze(job);
          }}
          title="AI 匹配度分析与简历调优"
          className="p-1 rounded bg-violet-950/60 hover:bg-violet-900 text-violet-300 hover:text-violet-100 border border-violet-500/30 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
