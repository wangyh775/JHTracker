import React, { useState, useEffect } from 'react';
import { api } from '../config';
import { KeywordMatrix, KeywordItem } from '../types';
import {
  X,
  Sparkles,
  Save,
  Plus,
  Sliders,
  Trash2,
  Wand2,
  Layers,
  HelpCircle,
  AlertCircle
} from 'lucide-react';

interface KeywordMatrixModalProps {
  isOpen: boolean;
  onClose: () => void;
  matrix?: KeywordMatrix;
  initialMatrix?: KeywordMatrix;
  resumeId?: string;
  resumeTitle?: string;
  markdownContent?: string;
  onSave?: (newMatrix: KeywordMatrix) => Promise<void>;
  onSaveSuccess?: (newMatrix: KeywordMatrix) => Promise<void> | void;
  onAutoExtract?: () => void;
}

export const KeywordMatrixModal: React.FC<KeywordMatrixModalProps> = ({
  isOpen,
  onClose,
  matrix,
  initialMatrix,
  resumeId,
  resumeTitle = '默认简历',
  markdownContent,
  onSave,
  onSaveSuccess,
  onAutoExtract
}) => {
  const [localMatrix, setLocalMatrix] = useState<KeywordMatrix>({
    version: 1,
    updated_at: new Date().toISOString(),
    updated_by: 'USER_MANUAL',
    categories: {
      core: [],
      domain: [],
      base: [],
      negative: []
    }
  });

  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [groundingMsg, setGroundingMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'core' | 'domain' | 'base' | 'negative'>('core');
  const [newKw, setNewKw] = useState('');
  const [newWeight, setNewWeight] = useState(2.0);
  const [newSource, setNewSource] = useState('');

  // 同步传入的 matrix / initialMatrix 或初始化默认值
  useEffect(() => {
    const src = matrix || initialMatrix;
    if (src && src.categories) {
      setLocalMatrix(JSON.parse(JSON.stringify(src)));
    } else {
      setLocalMatrix({
        version: 1,
        updated_at: new Date().toISOString(),
        updated_by: 'USER_MANUAL',
        categories: {
          core: [
            { keyword: 'Python', weight: 2.5, source: '简历高频技术栈', enabled: true },
            { keyword: 'FastAPI', weight: 2.2, source: '后端重点项目', enabled: true }
          ],
          domain: [
            { keyword: '软件工程', weight: 2.0, source: '专业背景', enabled: true }
          ],
          base: [
            { keyword: 'Git', weight: 0.8, source: '协同工具', enabled: true },
            { keyword: 'Linux', weight: 0.8, source: '操作系统', enabled: true }
          ],
          negative: [
            { keyword: '销售', weight: 0.1, source: '排除纯销售岗位', enabled: true },
            { keyword: '纯文职', weight: 0.1, source: '排除非技术文职', enabled: true }
          ]
        }
      });
    }
  }, [matrix, initialMatrix, isOpen]);

  if (!isOpen) return null;

  const handleToggleEnable = (cat: 'core' | 'domain' | 'base' | 'negative', idx: number) => {
    setLocalMatrix((prev) => {
      const next = { ...prev };
      const item = next.categories[cat][idx];
      if (item) {
        item.enabled = !item.enabled;
      }
      return next;
    });
  };

  const handleWeightChange = (cat: 'core' | 'domain' | 'base' | 'negative', idx: number, val: number) => {
    setLocalMatrix((prev) => {
      const next = { ...prev };
      const item = next.categories[cat][idx];
      if (item) {
        item.weight = val;
      }
      return next;
    });
  };

  const handleRemove = (cat: 'core' | 'domain' | 'base' | 'negative', idx: number) => {
    setLocalMatrix((prev) => {
      const next = { ...prev };
      next.categories[cat].splice(idx, 1);
      return next;
    });
  };

  const handleAddKeyword = () => {
    if (!newKw.trim()) return;
    const item: KeywordItem = {
      keyword: newKw.trim(),
      weight: newWeight,
      source: newSource.trim() || '用户手动添加',
      enabled: true
    };
    setLocalMatrix((prev) => {
      const next = { ...prev };
      next.categories[activeTab] = [...(next.categories[activeTab] || []), item];
      return next;
    });
    setNewKw('');
    setNewSource('');
  };

  const handleSaveModal = async () => {
    setSaving(true);
    setValidating(true);
    setGroundingMsg(null);
    try {
      // 1. 调用后端本体命中率自检 (Pre-flight FTS Grounding)
      let matrixToSave = localMatrix;
      try {
        const checkRes = await api.post('/api/hitl/validate-matrix', localMatrix);
        if (checkRes.data && checkRes.data.matrix) {
          matrixToSave = checkRes.data.matrix;
          setLocalMatrix(matrixToSave);
          if (checkRes.data.zero_hit_count > 0) {
            setGroundingMsg(`已探测全库 2.4 万岗位：发现 ${checkRes.data.zero_hit_count} 个生僻无命中词已做风险标注或自动禁用。`);
          }
        }
      } catch {
        // 容错降级
      }

      if (onSave) {
        await onSave(matrixToSave);
      } else if (onSaveSuccess) {
        await onSaveSuccess(matrixToSave);
      }
      onClose();
    } finally {
      setSaving(false);
      setValidating(false);
    }
  };

  const metaTabs = [
    {
      id: 'core' as const,
      label: '🟣 核心技术栈 (Core)',
      desc: '简历主修能力，基础分主拉动力 (1.5x ~ 3.0x)',
      items: localMatrix.categories?.core || [],
      badgeColor: 'border-purple-500/40 text-purple-300 bg-purple-950/40',
      defaultWeight: 2.5
    },
    {
      id: 'domain' as const,
      label: '🔵 业务领域 (Domain)',
      desc: '学术研究课题与垂直赛道 (1.2x ~ 2.0x)',
      items: localMatrix.categories?.domain || [],
      badgeColor: 'border-blue-500/40 text-blue-300 bg-blue-950/40',
      defaultWeight: 2.0
    },
    {
      id: 'base' as const,
      label: '⚪ 通用底座 (Base)',
      desc: '常规工具底座，辅助匹配 (0.5x ~ 1.0x)',
      items: localMatrix.categories?.base || [],
      badgeColor: 'border-slate-500/40 text-slate-300 bg-slate-900/60',
      defaultWeight: 0.8
    },
    {
      id: 'negative' as const,
      label: '🔴 排斥黑名单 (Negative)',
      desc: '不想投递的方向，命中直接强制压低或一票否决 (0.0x ~ 0.3x)',
      items: localMatrix.categories?.negative || [],
      badgeColor: 'border-rose-500/40 text-rose-300 bg-rose-950/40',
      defaultWeight: 0.1
    }
  ];

  const currentMeta = metaTabs.find((t) => t.id === activeTab)!;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-3xl bg-[#0f111a] border border-[#24283b] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#24283b] bg-[#141724]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-gradient-to-br from-purple-500/20 to-cyan-500/20 rounded-xl border border-purple-500/30">
              <Sparkles className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-wide">
                  推荐语义关键词矩阵 (Semantic Profile)
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 font-mono">
                  {resumeTitle || '当前简历'}
                </span>
              </div>
              <p className="text-xs text-[#9ca3af] mt-0.5">
                此矩阵作为推荐系统的「能力塔」，决定向你推送哪些技术栈、领域与拦截不相干职位。
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#9ca3af] hover:text-white hover:bg-[#24283b] transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Category Tabs */}
        <div className="grid grid-cols-4 gap-2 px-6 pt-4 pb-2 bg-[#121522] border-b border-[#24283b]">
          {metaTabs.map((tab) => {
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setNewWeight(tab.defaultWeight);
                }}
                className={`py-2 px-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'bg-[#1b1e2e] border-cyan-500/80 text-white shadow-sm'
                    : 'bg-[#151824] border-[#24283b] text-[#9ca3af] hover:border-cyan-500/30 hover:text-white'
                }`}
              >
                <div className="text-xs font-bold truncate">{tab.label}</div>
                <div className="text-[10px] text-[#6b7280] mt-0.5">
                  已收录 {tab.items.length} 个词
                </div>
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar">
          {/* Grounding Message Banner */}
          {groundingMsg && (
            <div className="p-3 bg-amber-950/30 border border-amber-500/40 rounded-xl flex items-center gap-2 text-xs text-amber-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{groundingMsg}</span>
            </div>
          )}

          {/* Section banner */}
          <div className="p-3 bg-[#151824] border border-[#24283b] rounded-xl flex items-center justify-between">
            <div className="text-xs text-[#d1d5db]">
              <span className="font-bold text-white mr-1.5">{currentMeta.label}</span>
              <span>— {currentMeta.desc}</span>
            </div>
            {onAutoExtract && (
              <button
                onClick={onAutoExtract}
                className="flex items-center gap-1 px-2.5 py-1 bg-purple-900/40 hover:bg-purple-800/60 text-purple-300 text-xs font-medium rounded-lg border border-purple-500/30 transition flex-shrink-0"
                title="调用外部智能体或模型重新提炼当前简历关键词"
              >
                <Wand2 className="h-3 w-3" />
                <span>智能体重析</span>
              </button>
            )}
          </div>

          {/* Keywords List / Capsules */}
          <div className="space-y-2.5">
            {currentMeta.items.length === 0 ? (
              <div className="py-10 text-center text-xs text-[#6b7280] border border-dashed border-[#24283b] rounded-xl">
                该维度暂无关键词，可在下方输入框手动添加
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {currentMeta.items.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border flex flex-col justify-between gap-2 transition ${
                      item.enabled !== false
                        ? 'bg-[#151824] border-[#24283b] hover:border-cyan-500/40'
                        : 'bg-[#12141e] border-[#1e2233] opacity-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleEnable(activeTab, idx)}
                          className={`w-3.5 h-3.5 rounded flex items-center justify-center border text-[9px] ${
                            item.enabled !== false
                              ? 'bg-cyan-600 border-cyan-400 text-white'
                              : 'bg-transparent border-[#4b5563]'
                          }`}
                          title={item.enabled !== false ? '点击临时禁用该词' : '点击重新启用该词'}
                        >
                          {item.enabled !== false && '✓'}
                        </button>
                        <span className="font-bold text-xs text-white tracking-wide">
                          {item.keyword}
                        </span>
                      </div>
                      <button
                        onClick={() => handleRemove(activeTab, idx)}
                        className="text-[#6b7280] hover:text-rose-400 p-1 rounded transition"
                        title="删除此关键词"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    {item.source && (
                      <div className="text-[10px] text-[#9ca3af] truncate pl-5">
                        依据: {item.source}
                      </div>
                    )}

                    {/* Weight Slider */}
                    <div className="flex items-center gap-2 pt-1 border-t border-[#24283b]/60 text-xs">
                      <span className="text-[10px] text-[#6b7280]">权重:</span>
                      <input
                        type="range"
                        min="0.1"
                        max="3.0"
                        step="0.1"
                        value={item.weight}
                        onChange={(e) =>
                          handleWeightChange(activeTab, idx, parseFloat(e.target.value))
                        }
                        className="flex-1 accent-cyan-500 h-1 bg-[#24283b] rounded cursor-pointer"
                      />
                      <span className="font-mono text-cyan-400 font-bold text-xs w-8 text-right">
                        {item.weight.toFixed(1)}x
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Add Area */}
          <div className="pt-3 border-t border-[#24283b] space-y-2">
            <div className="text-xs font-bold text-[#d1d5db] flex items-center gap-1">
              <Plus className="h-3.5 w-3.5 text-cyan-400" />
              <span>添加关键词到【{currentMeta.label.split(' ')[1]}】</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                placeholder="关键词 (如: PyTorch, SLAM)"
                value={newKw}
                onChange={(e) => setNewKw(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddKeyword();
                }}
                className="flex-1 min-w-[160px] px-3 py-1.5 bg-[#151824] border border-[#24283b] rounded-lg text-xs text-white outline-none focus:border-cyan-500"
              />
              <input
                type="text"
                placeholder="来源/理由 (可选)"
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddKeyword();
                }}
                className="flex-1 min-w-[140px] px-3 py-1.5 bg-[#151824] border border-[#24283b] rounded-lg text-xs text-[#9ca3af] outline-none focus:border-cyan-500"
              />
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#151824] border border-[#24283b] rounded-lg">
                <span className="text-[10px] text-[#6b7280]">预设权:</span>
                <input
                  type="number"
                  min="0.1"
                  max="3.0"
                  step="0.1"
                  value={newWeight}
                  onChange={(e) => setNewWeight(parseFloat(e.target.value) || 1.0)}
                  className="w-12 bg-transparent text-cyan-400 font-mono text-xs outline-none text-center font-bold"
                />
              </div>
              <button
                onClick={handleAddKeyword}
                className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs rounded-lg shadow-sm transition"
              >
                加入
              </button>
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="px-6 py-3.5 border-t border-[#24283b] bg-[#141724] flex items-center justify-between">
          <div className="text-[11px] text-[#6b7280]">
            💡 修改并保存后，推荐算法将实时以新权重为基准重新计算
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-[#24283b] hover:bg-[#1f2336] text-xs text-[#9ca3af] transition"
            >
              取消
            </button>
            <button
              disabled={saving}
              onClick={handleSaveModal}
              className="flex items-center gap-1.5 px-5 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg shadow-md transition"
            >
              <Save className="h-3.5 w-3.5" />
              <span>{saving ? '保存更新中...' : '保存并应用画像'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};