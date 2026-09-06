import React from 'react';
import { MapPin, Calendar, RotateCcw } from 'lucide-react';

interface FilterPillsBarProps {
  selectedCity: string;
  onSelectCity: (city: string) => void;
  selectedBatch: string;
  onSelectBatch: (batch: string) => void;
  onReset: () => void;
}

const TOP_CITIES = ['全部', '北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '苏州', '合肥', '西安', '全国', '海外'];
const BATCH_OPTIONS = ['全部', '27秋招', '26秋招', '26春招', '日常实习', '校园招聘', '提前批', '补录'];

export const FilterPillsBar: React.FC<FilterPillsBarProps> = ({
  selectedCity,
  onSelectCity,
  selectedBatch,
  onSelectBatch,
  onReset,
}) => {
  const hasActiveFilters = selectedCity !== '全部' || selectedBatch !== '全部';

  return (
    <div className="w-full bg-cyber-card border border-cyber rounded-xl p-3 space-y-2.5 text-xs shadow-md">
      {/* City Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1 text-gray-400 font-medium whitespace-nowrap min-w-[50px]">
          <MapPin className="w-3 h-3 text-cyan-400" />
          <span>城市:</span>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {TOP_CITIES.map((city) => {
            const isSelected = selectedCity === city;
            return (
              <button
                key={city}
                onClick={() => onSelectCity(city)}
                className={`px-2.5 py-0.5 rounded-full text-[11px] transition-all whitespace-nowrap ${
                  isSelected
                    ? 'bg-cyan-500/15 text-cyan-200 border border-cyan-500/40 shadow-sm font-semibold'
                    : 'bg-[#0a0a0e] text-gray-400 border border-cyber hover:text-gray-200 hover:border-slate-700'
                }`}
              >
                {city}
              </button>
            );
          })}
        </div>
      </div>

      {/* Batch Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1 text-gray-400 font-medium whitespace-nowrap min-w-[50px]">
          <Calendar className="w-3 h-3 text-violet-400" />
          <span>届别:</span>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {BATCH_OPTIONS.map((batch) => {
            const isSelected = selectedBatch === batch;
            return (
              <button
                key={batch}
                onClick={() => onSelectBatch(batch)}
                className={`px-2.5 py-0.5 rounded-full text-[11px] transition-all whitespace-nowrap ${
                  isSelected
                    ? 'bg-cyan-500/15 text-cyan-200 border border-cyan-500/40 shadow-sm font-semibold'
                    : 'bg-[#0a0a0e] text-gray-400 border border-cyber hover:text-gray-200 hover:border-slate-700'
                }`}
              >
                {batch}
              </button>
            );
          })}

          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 ml-auto px-2 py-0.5 text-[11px] text-gray-400 hover:text-cyan-400 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>重置筛选</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
