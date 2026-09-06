import React, { useState, useEffect, useMemo, useRef } from 'react';
import { api } from '../config';
import { RecommendationItem, JobItem, ResumeItem, AgentPushItem } from '../types';
import {
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Building2,
  MapPin,
  CheckCircle2,
  Cpu,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Sliders,
  Flame,
  ArrowUpRight,
  Search,
  Filter,
  Layers,
  X,
  TrendingUp,
  TrendingDown,
  Zap,
  Target,
  BarChart3,
  Compass,
  RefreshCw,
  Bot,
  AlertCircle,
} from 'lucide-react';

interface WeightDetail {
  feature_key: string;
  weight: number;
  accept_count?: number;
  reject_count?: number;
}

interface RecommendationPanelProps {
  initialJob?: JobItem | null;
  onNavigateToKanban?: () => void;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  initialJob,
  onNavigateToKanban,
}) => {
  const [recs, setRecs] = useState<RecommendationItem[]>([]);
  const [agentPushes, setAgentPushes] = useState<AgentPushItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPushes, setLoadingPushes] = useState(false);
  const [activeResume, setActiveResume] = useState<ResumeItem | null>(null);
  const [learningNotice, setLearningNotice] = useState<string | null>(null);
  const [acceptedJobIds, setAcceptedJobIds] = useState<Set<string>>(new Set());

  // HITL Weights
  const [weightsList, setWeightsList] = useState<WeightDetail[]>([]);
  const [weightsTab, setWeightsTab] = useState<'ALL' | 'CATEGORY' | 'INDUSTRY' | 'CITY'>('ALL');
  const [isResettingWeights, setIsResettingWeights] = useState(false);
  const [isSyncingFromDb, setIsSyncingFromDb] = useState(false);

  // Card JD accordion state
  const [expandedJobIds, setExpandedJobIds] = useState<Set<string>>(new Set());

  // Filter & Controls
  const [minMatchThreshold, setMinMatchThreshold] = useState<number>(40);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCity, setSelectedCity] = useState<string>('全部');
  const [focusedInitialJob, setFocusedInitialJob] = useState<JobItem | null>(initialJob || null);

  // Reject Reason Modal / Popover State
  const [rejectModalJob, setRejectModalJob] = useState<{ id: string; company: string; title: string } | null>(null);
  const [selectedRejectReasons, setSelectedRejectReasons] = useState<string[]>([]);
  
  // AbortController ref to prevent race conditions on concurrent fetches
  const recsAbortControllerRef = useRef<AbortController | null>(null);

  // Sync initialJob prop if updated
  useEffect(() => {
    if (initialJob) {
      setFocusedInitialJob(initialJob);
    }
  }, [initialJob]);

  // Fetch recommendations with cancellation to avoid race conditions
  const fetchRecommendations = async () => {
    if (recsAbortControllerRef.current) {
      recsAbortControllerRef.current.abort();
    }
    const controller = new AbortController();
    recsAbortControllerRef.current = controller;

    try {
      setLoading(true);
      const res = await api.get<RecommendationItem[]>('/api/recommendations', {
        params: { top_k: 36, min_score: 0.3 },
        signal: controller.signal,
      });
      setRecs(res.data || []);
    } catch (e: any) {
      if (
        e?.name === 'CanceledError' || 
        e?.name === 'AbortError' || 
        e?.code === 'ERR_CANCELED' ||
        e?.message?.includes('canceled') ||
        e?.message?.includes('aborted')
      ) {
        // Request was aborted by newer request, ignore completely
        return;
      }
      console.error('Failed to fetch recommendations:', e);
    } finally {
      if (recsAbortControllerRef.current === controller) {
        setLoading(false);
      }
    }
  };

  // Fetch agent pushes
  const fetchAgentPushes = async () => {
    try {
      setLoadingPushes(true);
      const res = await api.get<AgentPushItem[]>('/api/agent-pushes');
      setAgentPushes(res.data || []);
    } catch (e) {
      console.error('Failed to fetch agent pushes:', e);
    } finally {
      setLoadingPushes(false);
    }
  };

  // Fetch active resume & HITL weights
  const fetchResumeAndWeights = async () => {
    try {
      const resumesRes = await api.get('/api/resumes');
      if (resumesRes.data && resumesRes.data.length > 0) {
        const active = resumesRes.data.find((r: any) => r.is_default || r.is_active) || resumesRes.data[0];
        setActiveResume(active);
      }

      const weightsRes = await api.get<{ weights?: Record<string, number>; details?: WeightDetail[] } | WeightDetail[]>('/api/hitl/weights');
      if (weightsRes.data) {
        if (Array.isArray(weightsRes.data)) {
          setWeightsList(weightsRes.data);
        } else if (weightsRes.data.details && Array.isArray(weightsRes.data.details)) {
          setWeightsList(weightsRes.data.details);
        }
      }
    } catch (e) {
      console.error('Failed to fetch user context & weights:', e);
    }
  };

  useEffect(() => {
    fetchRecommendations();
    fetchAgentPushes();
    fetchResumeAndWeights();
  }, []);

  const handleFeedback = async (
    jobId: string,
    action: 'ACCEPT' | 'REJECT',
    company: string,
    rejectReasons?: string[],
    matchScore?: number,
    recommendReason?: string
  ) => {
    try {
      await api.post('/api/recommendations/feedback', {
        job_id: jobId,
        action,
        reject_reasons: rejectReasons && rejectReasons.length > 0 ? rejectReasons : undefined,
        match_score: matchScore,
        recommend_reason: recommendReason,
      });

      if (action === 'ACCEPT') {
        setAcceptedJobIds((prev) => new Set([...prev, jobId]));
        setLearningNotice(`已将【${company}】加入投递进展看板，模型已强化该岗位特征权重！`);
      } else {
        const reasonTip = rejectReasons && rejectReasons.length > 0
          ? `已根据反馈原因【${rejectReasons.join('、')}】定向抑制`
          : '已温和衰减相关维度';
        setLearningNotice(`已负向抑制【${company}】（${reasonTip}），该岗位已自推荐流移除。`);
      }
      setTimeout(() => setLearningNotice(null), 4000);

      // Refresh list, pushes and weights
      await fetchRecommendations();
      await fetchAgentPushes();
      await fetchResumeAndWeights();
    } catch (e) {
      console.error('Failed to submit feedback:', e);
    }
  };

  const handleResetWeights = async (featureKey?: string) => {
    try {
      setIsResettingWeights(true);
      await api.post('/api/hitl/weights/reset', { feature_key: featureKey });
      setLearningNotice(featureKey ? `已重置特征【${featureKey}】权重` : '已重置全部 HITL 特征偏好为基准线 1.0');
      setTimeout(() => setLearningNotice(null), 3000);
      await fetchResumeAndWeights();
      await fetchRecommendations();
    } catch (e) {
      console.error('Failed to reset weights:', e);
    } finally {
      setIsResettingWeights(false);
    }
  };

  const handleSyncFromPublicDb = async () => {
    try {
      setIsSyncingFromDb(true);
      const res = await api.post<{ status: string; message: string; stats: any }>('/api/hitl/sync-from-db');
      setLearningNotice(res.data?.message || '已成功从全网岗位大厅同步特征字典');
      setTimeout(() => setLearningNotice(null), 3500);
      await fetchResumeAndWeights();
    } catch (e: any) {
      console.error('Failed to sync features from public db:', e);
      const errMsg = e?.response?.data?.detail || e?.message || '同步失败，请检查后端服务';
      setLearningNotice(`同步失败: ${errMsg}`);
      setTimeout(() => setLearningNotice(null), 4000);
    } finally {
      setIsSyncingFromDb(false);
    }
  };

  const toggleExpand = (jobId: string) => {
    setExpandedJobIds((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      return next;
    });
  };

  // Active Resume Skills list
  const activeSkills = useMemo(() => {
    if (!activeResume?.skills) return [];
    return activeResume.skills.map((s) => s.toLowerCase().trim());
  }, [activeResume]);

  // Extract cities from current recommendations for quick filter pills
  const availableCities = useMemo(() => {
    const cities = new Set<string>();
    recs.forEach((r) => {
      const loc = r.job.location || r.job.city;
      if (loc) {
        // Simple extraction: split by spaces or commas
        const parts = loc.split(/[,/、\s]/).map((p) => p.trim()).filter(Boolean);
        parts.forEach((p) => {
          if (p.length >= 2 && p.length <= 4) cities.add(p);
        });
      }
    });
    return ['全部', ...Array.from(cities).slice(0, 8)];
  }, [recs]);

  // Filtered recommendations
  const filteredRecs = useMemo(() => {
    return recs.filter((item) => {
      const scoreVal = item.score ?? item.match_score ?? 0;
      const matchPct = Number.isFinite(scoreVal)
        ? Math.min(Math.round(scoreVal <= 1.0 ? scoreVal * 100 : scoreVal * 20), 99)
        : 80;

      if (matchPct < minMatchThreshold) return false;

      if (selectedCity !== '全部') {
        const loc = (item.job.location || item.job.city || '').toLowerCase();
        if (!loc.includes(selectedCity.toLowerCase())) return false;
      }

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const inTitle = item.job.title.toLowerCase().includes(q);
        const inCompany = item.job.company.toLowerCase().includes(q);
        const inTags = (item.job.type_tags || []).some((t) => t.toLowerCase().includes(q));
        if (!inTitle && !inCompany && !inTags) return false;
      }

      return true;
    });
  }, [recs, minMatchThreshold, selectedCity, searchQuery]);

  // Filtered weights for sidebar
  const filteredWeights = useMemo(() => {
    let list = weightsList;
    if (weightsTab === 'CATEGORY') list = weightsList.filter((w) => w.feature_key.startsWith('category:'));
    else if (weightsTab === 'INDUSTRY') list = weightsList.filter((w) => w.feature_key.startsWith('industry:'));
    else if (weightsTab === 'CITY') list = weightsList.filter((w) => w.feature_key.startsWith('city:'));

    return [...list].sort((a, b) => {
      const activeA = (a.accept_count || 0) + (a.reject_count || 0);
      const activeB = (b.accept_count || 0) + (b.reject_count || 0);
      if (activeA !== activeB) return activeB - activeA;
      return Math.abs(b.weight - 1.0) - Math.abs(a.weight - 1.0);
    });
  }, [weightsList, weightsTab]);

  return (
    <div className="space-y-4 font-sans text-[#f3f4f6]">
      {/* Dynamic Learning Feedback Toast */}
      {learningNotice && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl bg-[#0e111a] border border-cyan-500/60 shadow-[0_0_25px_rgba(6,182,212,0.3)] text-xs text-cyan-200 animate-fade-in backdrop-blur-md">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 animate-pulse" />
          <span>{learningNotice}</span>
          {onNavigateToKanban && (
            <button
              onClick={onNavigateToKanban}
              className="ml-2 px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-300 text-[11px] inline-flex items-center gap-1 transition-colors"
            >
              去看板查看
              <ArrowUpRight className="w-3 h-3" />
            </button>
          )}
        </div>
      )}

      {/* Main Top Hub: Engine Profile & Lens */}
      <div className="relative overflow-hidden rounded-2xl border border-[#24283b] bg-gradient-to-r from-[#0d101a] via-[#121624] to-[#0f131f] p-5 shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.4)]">
                <Sparkles className="w-4 h-4 animate-spin-slow" />
              </div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                智能协同推荐决策工作台
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-500/30 text-cyan-300 font-mono flex items-center gap-1">
                  <Cpu className="w-3 h-3" /> HITL 强化闭环 v2.4
                </span>
              </h1>
            </div>
            <p className="text-xs text-[#9ca3af] max-w-4xl leading-relaxed">
              基于当前激活简历的技能向量，结合你在大厅与推荐流中的【感兴趣 / 抑制】实时回馈。系统动态强化正向特征、负向衰减无关行业，实现千人千面的精准求职雷达。
            </p>
          </div>

          {/* Active Resume Status Badge */}
          <div className="flex items-center gap-3 bg-[#161a29]/90 border border-[#2a3047] px-4 py-2.5 rounded-xl shadow-inner">
            <div className="text-right">
              <div className="text-[11px] text-[#9ca3af] flex items-center gap-1 justify-end">
                <Layers className="w-3 h-3 text-cyan-400" />
                当前基准画像
              </div>
              <div className="text-xs font-semibold text-cyan-200">
                {activeResume ? activeResume.title : '未激活默认简历'}
              </div>
            </div>
            <div className="h-7 w-[1px] bg-[#2d344d]" />
            <div className="flex flex-col items-start text-[11px]">
              <span className="text-[#9ca3af]">已收录技能</span>
              <span className="font-mono text-emerald-400 font-bold">
                {activeResume?.skills?.length || 0} 项
              </span>
            </div>
          </div>
        </div>

        {/* Focused Initial Job Lens (Triggered from Job Lobby) */}
        {focusedInitialJob && (
          <div className="mt-4 pt-4 border-t border-[#24283b]/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 bg-cyan-950/20 border border-cyan-500/30 p-3.5 rounded-xl">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-cyan-900/40 text-cyan-400 border border-cyan-500/30 flex-shrink-0 mt-0.5">
                <Target className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-900/60 text-cyan-300 border border-cyan-500/40">
                    网申大厅定位透镜
                  </span>
                  <span className="text-xs font-bold text-white">{focusedInitialJob.title}</span>
                  <span className="text-xs text-[#9ca3af] flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    {focusedInitialJob.company}
                  </span>
                  {focusedInitialJob.salary_range && (
                    <span className="text-xs font-mono text-amber-400">
                      {focusedInitialJob.salary_range}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-[#9ca3af] mt-1 flex items-center gap-2 flex-wrap">
                  <span>地点: {focusedInitialJob.location || '全国'}</span>
                  <span>•</span>
                  <span>标签: {(focusedInitialJob.type_tags || ['研发技术']).join(' / ')}</span>
                  <span>•</span>
                  <span className="text-cyan-300/80">已在下方优先关联此类岗位的衍生推荐与技能比对</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end md:self-auto flex-shrink-0">
              <button
                onClick={() => handleFeedback(focusedInitialJob.id, 'ACCEPT', focusedInitialJob.company)}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium inline-flex items-center gap-1 shadow-md shadow-cyan-900/40 transition-all"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
                加入待投递
              </button>
              <button
                onClick={() => setFocusedInitialJob(null)}
                className="p-1.5 text-[#9ca3af] hover:text-white rounded-lg hover:bg-[#1f2438] transition-colors"
                title="关闭岗位透镜"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Two-Column Layout (70% Grid, 30% HITL Weights Visualization) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column: Recommendations Feed (8 cols on lg, 9 on xl) */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-3.5">
          {/* AI Agent Dedicated Push Banner & Cards Area */}
          <div className="p-4 rounded-xl border border-indigo-500/30 bg-gradient-to-r from-[#121124] via-[#0e111a] to-[#121626] shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-[#252445] pb-3 mb-3.5">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-indigo-950/80 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-bold text-white tracking-wide uppercase flex items-center gap-1.5">
                      AI 智能体特选直推专区
                      <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      MCP 协同发现 ({agentPushes.length})
                    </span>
                  </div>
                  <p className="text-[11px] text-[#9ca3af] mt-0.5">
                    基于你的当前默认简历、HITL 动态偏好与 2.4万+ 全量岗位库由智能体定向挖掘的高潜岗位
                  </p>
                </div>
              </div>
              <button
                onClick={fetchAgentPushes}
                disabled={loadingPushes}
                className="text-[11px] font-mono text-indigo-300 hover:text-white px-2.5 py-1 rounded-lg bg-indigo-950/50 hover:bg-indigo-900/60 border border-indigo-500/30 transition-all flex items-center gap-1"
                title="刷新智能体特推列表"
              >
                <RefreshCw className={`w-3 h-3 ${loadingPushes ? 'animate-spin' : ''}`} />
                刷新特推
              </button>
            </div>

            {loadingPushes ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[1, 2].map((i) => (
                  <div key={i} className="p-3.5 rounded-xl border border-[#24283b] bg-[#0c0e17] animate-pulse h-28" />
                ))}
              </div>
            ) : agentPushes.length === 0 ? (
              <div className="py-6 px-4 text-center rounded-xl bg-[#0a0c14]/70 border border-dashed border-[#282744] text-xs text-[#9ca3af] space-y-1.5">
                <p className="text-[#cbd5e1] font-medium flex items-center justify-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-indigo-400" />
                  暂无未处理的 AI 智能体特推岗位
                </p>
                <p className="text-[11px] text-[#6b7280]">
                  外部 MCP Agent 调用 <code className="text-indigo-300 font-mono">job_agent_push</code> 工具推送后，将在此处以高亮卡片直观呈现。
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {agentPushes.map((push) => {
                  const job = push.job;
                  if (!job) return null;
                  const isAccepted = acceptedJobIds.has(job.id);
                  const targetUrl = job.application_link || job.source_url;

                  return (
                    <div
                      key={push.id}
                      className="p-3.5 rounded-xl border border-indigo-500/40 bg-[#0c0d18] hover:border-indigo-400/70 transition-all shadow-md relative flex flex-col justify-between group"
                    >
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-900/50 text-indigo-300 border border-indigo-500/30">
                              {job.company}
                            </span>
                            <h4 className="text-sm font-bold text-white group-hover:text-indigo-200 transition-colors mt-1 line-clamp-1">
                              {job.title}
                            </h4>
                          </div>
                          <div className="flex items-center gap-1 text-[11px] font-mono text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30">
                            <Sparkles className="w-3 h-3 text-amber-400" />
                            {Math.round((push.match_score || 0.95) * 100)}% 契合
                          </div>
                        </div>

                        {/* Recommend Reason */}
                        <div className="p-2 rounded-lg bg-[#141426] border border-indigo-950/80 text-[11px] text-indigo-200/90 leading-relaxed">
                          <span className="text-indigo-400 font-semibold mr-1">💡 Agent 推荐理由:</span>
                          {push.recommend_reason}
                        </div>

                        <div className="flex items-center gap-2 text-[11px] text-[#9ca3af] flex-wrap">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-[#6b7280]" />
                            {job.location || '全国'}
                          </span>
                          {job.industry && (
                            <span className="flex items-center gap-1">
                              <Building2 className="w-3 h-3 text-[#6b7280]" />
                              {job.industry}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="pt-2.5 mt-2.5 border-t border-[#20203a] flex items-center justify-between gap-2">
                        {targetUrl ? (
                          <a
                            href={targetUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-indigo-300 hover:text-white font-mono hover:underline"
                          >
                            <ExternalLink className="w-3 h-3" />
                            直达网申
                          </a>
                        ) : (
                          <span className="text-[11px] text-[#6b7280] font-mono">已收录</span>
                        )}

                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => setRejectModalJob({ id: job.id, company: job.company, title: job.title })}
                            className="p-1.5 text-[#9ca3af] hover:text-rose-400 hover:bg-rose-950/40 rounded-lg border border-[#24283b] hover:border-rose-500/30 transition-all"
                            title="不感兴趣 (支持选择原因定向抑制)"
                          >
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(job.id, 'ACCEPT', job.company, undefined, push.match_score, push.recommend_reason)}
                            disabled={isAccepted}
                            className={`px-3 py-1.5 text-xs rounded-lg font-medium inline-flex items-center gap-1 shadow-sm transition-all ${
                              isAccepted
                                ? 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 cursor-default'
                                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-950/50'
                            }`}
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                            {isAccepted ? '已加入待投递' : '采纳直推'}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Controls Bar: Filter Threshold, City Quick Tabs, Search */}
          <div className="p-3.5 rounded-xl border border-[#24283b] bg-[#0e111a] flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-md">
            {/* Search and City Filter */}
            <div className="flex items-center gap-2.5 flex-1 flex-wrap">
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="在推荐流中速搜职位、企业、技能标签..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#151926] text-xs text-[#f3f4f6] placeholder-[#6b7280] pl-8 pr-3 py-1.5 rounded-lg border border-[#24283b] focus:outline-none focus:border-cyan-500/50 transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6b7280] hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>

              {/* City quick pills */}
              <div className="flex items-center gap-1 overflow-x-auto py-0.5">
                {availableCities.map((city) => (
                  <button
                    key={city}
                    onClick={() => setSelectedCity(city)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                      selectedCity === city
                        ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-500/40 shadow-sm'
                        : 'bg-[#151926] text-[#9ca3af] hover:text-white border border-[#24283b]'
                    }`}
                  >
                    {city}
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold Slider and Counter */}
            <div className="flex items-center gap-3 self-end md:self-auto border-t md:border-t-0 pt-2 md:pt-0 border-[#24283b]">
              <div className="flex items-center gap-2 text-xs text-[#9ca3af]">
                <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                <span>阈值:</span>
                <span className="font-mono text-cyan-300 font-bold text-[11px] min-w-[32px]">
                  ≥{minMatchThreshold}%
                </span>
                <input
                  type="range"
                  min="40"
                  max="90"
                  step="5"
                  value={minMatchThreshold}
                  onChange={(e) => setMinMatchThreshold(Number(e.target.value))}
                  className="w-20 accent-cyan-400 cursor-pointer h-1.5 bg-[#1b2030] rounded-lg"
                />
              </div>

              <span className="text-[11px] font-mono text-[#6b7280] px-2 py-0.5 bg-[#141826] rounded border border-[#24283b]">
                共 {filteredRecs.length} 岗
              </span>
            </div>
          </div>

          {/* Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5">
              {[1, 2, 3, 4, 5, 6].map((idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[#24283b] bg-[#0e111a] animate-pulse space-y-3"
                >
                  <div className="h-4 bg-[#1a1f30] rounded w-3/4" />
                  <div className="h-3 bg-[#151926] rounded w-1/2" />
                  <div className="h-12 bg-[#121624] rounded" />
                  <div className="h-6 bg-[#161a28] rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : filteredRecs.length === 0 ? (
            <div className="py-20 text-center text-[#9ca3af] bg-[#0e111a] rounded-xl border border-[#24283b] text-xs space-y-3">
              <Compass className="w-8 h-8 text-[#4b5563] mx-auto animate-bounce" />
              <p className="text-sm font-medium text-white">当前筛选条件下暂无推荐岗位</p>
              <p className="text-[#6b7280] max-w-md mx-auto">
                可尝试调低匹配度阈值（如设为 ≥50%）、重置城市筛选，或在右侧重置模型特征偏好。
              </p>
              <button
                onClick={() => {
                  setMinMatchThreshold(50);
                  setSelectedCity('全部');
                  setSearchQuery('');
                }}
                className="px-3.5 py-1.5 rounded-lg bg-[#181d2e] hover:bg-[#20273d] text-cyan-300 border border-cyan-500/30 text-xs font-mono transition-colors"
              >
                一键重置筛选条件
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5">
              {filteredRecs.map((rec) => {
                const { job } = rec;
                const scoreVal = rec.score ?? rec.match_score ?? 0;
                const matchPct = Number.isFinite(scoreVal)
                  ? Math.min(Math.round(scoreVal <= 1.0 ? scoreVal * 100 : scoreVal * 20), 99)
                  : 82;

                const displayReason = rec.reason || rec.recommend_reason || '技能偏好匹配推荐';
                const targetUrl = job.apply_url || job.detail_url;
                const isExpanded = expandedJobIds.has(job.id);
                const isAccepted = acceptedJobIds.has(job.id);

                // Analyze matched skills
                const jobTags = job.type_tags || [];
                const matchedSkills = jobTags.filter((tag) =>
                  activeSkills.some((s) => s.includes(tag.toLowerCase()) || tag.toLowerCase().includes(s))
                );
                const otherTags = jobTags.filter((tag) => !matchedSkills.includes(tag));

                const isHighMatch = matchPct >= 85;

                return (
                  <div
                    key={job.id}
                    className={`flex flex-col justify-between p-4 rounded-xl border transition-all duration-200 bg-[#0e111a] hover:bg-[#121624] relative group ${
                      isHighMatch
                        ? 'border-cyan-500/40 hover:border-cyan-400/80 shadow-[0_0_15px_rgba(6,182,212,0.08)]'
                        : 'border-[#24283b] hover:border-[#384161]'
                    }`}
                  >
                    {/* High match accent light */}
                    {isHighMatch && (
                      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent rounded-t-xl" />
                    )}

                    <div className="space-y-2.5">
                      {/* Title & Score Indicator */}
                      <div className="flex items-start justify-between gap-2">
                        <span
                          className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-1"
                          title={job.title}
                        >
                          {job.title}
                        </span>
                        <div
                          className={`flex-shrink-0 px-2 py-0.5 rounded-full text-[11px] font-mono font-bold border flex items-center gap-1 ${
                            isHighMatch
                              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                              : 'bg-cyan-950/40 text-cyan-300 border-cyan-500/30'
                          }`}
                        >
                          {isHighMatch && <Flame className="w-3 h-3 text-amber-400" />}
                          {matchPct}%
                        </div>
                      </div>

                      {/* Company, Salary & Meta */}
                      <div className="flex flex-wrap items-center gap-2 text-xs text-[#9ca3af]">
                        <span className="flex items-center gap-1 font-semibold text-[#f3f4f6]">
                          <Building2 className="w-3.5 h-3.5 text-[#6b7280]" />
                          {job.company}
                        </span>
                        {job.salary_range && (
                          <span className="text-amber-400 font-mono text-[11px] font-semibold">
                            {job.salary_range}
                          </span>
                        )}
                        {job.location && (
                          <span className="flex items-center gap-0.5 text-[11px] text-[#6b7280]">
                            <MapPin className="w-3 h-3" />
                            {job.location}
                          </span>
                        )}
                      </div>

                      {/* AI Matching Reason */}
                      <div className="text-[11px] text-cyan-200/90 bg-cyan-950/30 border border-cyan-500/20 px-2.5 py-1.5 rounded-lg flex items-start gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                        <span className="line-clamp-2 leading-relaxed">{displayReason}</span>
                      </div>

                      {/* Skill Match Breakdown */}
                      <div className="space-y-1 pt-1">
                        <div className="flex items-center justify-between text-[10px] text-[#6b7280]">
                          <span>技能点亮画像</span>
                          <span className="font-mono">
                            命中 {matchedSkills.length} / 需补充 {otherTags.length}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {matchedSkills.map((tag, idx) => (
                            <span
                              key={`matched-${idx}`}
                              className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-emerald-950/50 text-emerald-300 border border-emerald-500/30 flex items-center gap-0.5"
                              title="已命中简历画像"
                            >
                              <Zap className="w-2.5 h-2.5 text-emerald-400" />
                              {tag}
                            </span>
                          ))}
                          {otherTags.slice(0, 3).map((tag, idx) => (
                            <span
                              key={`other-${idx}`}
                              className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-[#161a29] text-[#9ca3af] border border-[#24283b]"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Expandable JD Details Accordion */}
                      {job.description && (
                        <div className="pt-1">
                          <button
                            onClick={() => toggleExpand(job.id)}
                            className="text-[11px] text-[#9ca3af] hover:text-cyan-300 flex items-center gap-1 font-mono transition-colors"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-3.5 h-3.5" /> 收起职责要求
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-3.5 h-3.5" /> 展开职责要求
                              </>
                            )}
                          </button>
                          {isExpanded && (
                            <div className="mt-2 p-2.5 rounded-lg bg-[#08090e] border border-[#24283b] text-[11px] text-[#cbd5e1] leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap font-sans">
                              {job.description}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Bottom Actions Bar */}
                    <div className="pt-3 mt-3 border-t border-[#24283b] flex items-center justify-between gap-2">
                      {targetUrl ? (
                        <a
                          href={targetUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-mono hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          网申通道
                        </a>
                      ) : (
                        <span className="text-[11px] text-[#6b7280] font-mono">站内已收录</span>
                      )}

                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setRejectModalJob({ id: job.id, company: job.company, title: job.title })}
                          className="p-1.5 text-[#9ca3af] hover:text-rose-400 hover:bg-rose-950/40 rounded-lg border border-[#24283b] hover:border-rose-500/30 transition-all"
                          title="不感兴趣 (支持选择原因定向抑制特征)"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(job.id, 'ACCEPT', job.company, undefined, scoreVal, displayReason)}
                          disabled={isAccepted}
                          className={`px-3 py-1.5 text-xs rounded-lg font-medium inline-flex items-center gap-1 shadow-sm transition-all ${
                            isAccepted
                              ? 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 cursor-default'
                              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950/50'
                          }`}
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          {isAccepted ? '已加入待投递' : '感兴趣'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: HITL Weights Visualization Dashboard (4 cols on lg, 3 on xl) */}
        <div className="lg:col-span-4 xl:col-span-3 space-y-4 sticky top-4">
          <div className="rounded-xl border border-[#24283b] bg-[#0e111a] p-4 shadow-lg space-y-4">
            {/* Header & Reset Action */}
            <div className="flex items-center justify-between gap-2 border-b border-[#24283b] pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white tracking-wide uppercase">
                  HITL 学习权重矩阵
                </h3>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => handleSyncFromPublicDb()}
                  disabled={isSyncingFromDb}
                  className="text-[11px] font-mono text-cyan-300 hover:text-cyan-200 hover:bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30 hover:border-cyan-400/50 transition-all flex items-center gap-1"
                  title="扫描全量岗位数据库，增量对齐所有最新行业/城市/类型特征字典"
                >
                  <RefreshCw className={`w-3 h-3 ${isSyncingFromDb ? 'animate-spin' : ''}`} />
                  同步全网
                </button>
                <button
                  onClick={() => handleResetWeights()}
                  disabled={isResettingWeights}
                  className="text-[11px] font-mono text-[#9ca3af] hover:text-rose-300 hover:bg-rose-950/30 px-2 py-0.5 rounded border border-[#24283b] hover:border-rose-500/30 transition-all flex items-center gap-1"
                  title="一键将所有学习到的偏好权重恢复到基准 1.0"
                >
                  <RotateCcw className={`w-3 h-3 ${isResettingWeights ? 'animate-spin' : ''}`} />
                  重置
                </button>
              </div>
            </div>

            <p className="text-[11px] text-[#9ca3af] leading-relaxed">
              实时记录你的交互反馈。数值大于 1.0 表示偏好强化，小于 1.0 表示负向抑制。
            </p>

            {/* Tabs for Category filtering */}
            <div className="grid grid-cols-4 gap-1 p-1 bg-[#141826] rounded-lg border border-[#24283b] text-[11px] font-mono">
              {(['ALL', 'CATEGORY', 'INDUSTRY', 'CITY'] as const).map((tab) => {
                const labelMap = {
                  ALL: '全部',
                  CATEGORY: '类型',
                  INDUSTRY: '行业',
                  CITY: '城市',
                };
                return (
                  <button
                    key={tab}
                    onClick={() => setWeightsTab(tab)}
                    className={`py-1 rounded text-center transition-colors ${
                      weightsTab === tab
                        ? 'bg-cyan-900/60 text-cyan-300 font-bold'
                        : 'text-[#9ca3af] hover:text-white'
                    }`}
                  >
                    {labelMap[tab]}
                  </button>
                );
              })}
            </div>

            {/* Weights Energy Bar Gauges List */}
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {filteredWeights.length === 0 ? (
                <div className="py-8 text-center text-[11px] text-[#6b7280] space-y-1">
                  <p>当前分类下暂无偏好特征记录</p>
                  <p className="text-[10px]">在左侧点击【感兴趣】或【不感兴趣】即可训练模型</p>
                </div>
              ) : (
                filteredWeights.map((item) => {
                  const w = item.weight ?? 1.0;
                  const isBoosted = w > 1.0;
                  const isDamped = w < 1.0;

                  // Clean display name
                  const cleanKey = item.feature_key
                    .replace(/^category:/, '岗位·')
                    .replace(/^enterprise:/, '性质·')
                    .replace(/^industry:/, '行业·')
                    .replace(/^city:/, '城市·')
                    .replace(/^tag:/, '标签·');

                  // Normalize bar percentage (0.05 to 2.0 scale)
                  // Baseline 1.0 sits at 50%
                  const pct = Math.min(100, Math.max(5, (w / 2.0) * 100));

                  return (
                    <div
                      key={item.feature_key}
                      className="p-2 rounded-lg bg-[#141826] border border-[#202538] text-xs space-y-1.5 group"
                    >
                      <div className="flex items-center justify-between gap-1 text-[11px]">
                        <span className="font-medium text-[#f3f4f6] truncate max-w-[140px]" title={item.feature_key}>
                          {cleanKey}
                        </span>
                        <div className="flex items-center gap-1.5 font-mono">
                          <span
                            className={`font-bold flex items-center gap-0.5 ${
                              isBoosted
                                ? 'text-emerald-400'
                                : isDamped
                                ? 'text-rose-400'
                                : 'text-[#9ca3af]'
                            }`}
                          >
                            {isBoosted ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : isDamped ? (
                              <TrendingDown className="w-3 h-3" />
                            ) : null}
                            {w.toFixed(2)}x
                          </span>
                          <button
                            onClick={() => handleResetWeights(item.feature_key)}
                            className="text-[#6b7280] hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
                            title="重置此特征"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      </div>

                      {/* Energy Gauge Slider */}
                      <div className="w-full h-1.5 bg-[#1b2030] rounded-full overflow-hidden relative">
                        {/* Center baseline marker at 50% */}
                        <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-[#3a4463] z-10" />
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            isBoosted
                              ? 'bg-gradient-to-r from-cyan-500 to-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                              : isDamped
                              ? 'bg-gradient-to-r from-rose-500 to-amber-500'
                              : 'bg-[#4b5563]'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>

                      {/* Feedback counts micro-labels */}
                      {(item.accept_count !== undefined || item.reject_count !== undefined) && (
                        <div className="flex items-center justify-between text-[10px] text-[#6b7280] font-mono pt-0.5">
                          <span>
                            反馈: 赞 {item.accept_count ?? 0} / 踩 {item.reject_count ?? 0}
                          </span>
                          <span>
                            {isBoosted ? '优先命中' : isDamped ? '降频推荐' : '中立基准'}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Quick Helper / Explain */}
            <div className="p-2.5 rounded-lg bg-[#141826]/70 border border-[#24283b] text-[11px] text-[#9ca3af] space-y-1">
              <div className="font-semibold text-[#cbd5e1] flex items-center gap-1">
                <Cpu className="w-3 h-3 text-cyan-400" />
                P0/P1 平滑协同学习规则
              </div>
              <p className="text-[10px] text-[#6b7280] leading-normal">
                已启用 P0 定向归因惩罚（拒绝时按选择的原因定向扣减相应职能/行业/城市，不连坐）与 P1 平滑加权综合分公式（职能50%+行业30%+城市20%）。
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Reject Reasons Modal / Popover */}
      {rejectModalJob && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#0e111a] border border-[#24283b] rounded-2xl w-full max-w-md p-5 shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-400">
                  <AlertCircle className="w-4 h-4" />
                  <span>不感兴趣反馈 · 定向抑制模型特征</span>
                </div>
                <h4 className="text-sm font-bold text-white line-clamp-1">
                  {rejectModalJob.title}
                </h4>
                <p className="text-xs text-[#9ca3af]">
                  {rejectModalJob.company}
                </p>
              </div>
              <button
                onClick={() => {
                  setRejectModalJob(null);
                  setSelectedRejectReasons([]);
                }}
                className="p-1 text-[#6b7280] hover:text-white rounded-lg hover:bg-[#1a1f30]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-[#141826] border border-[#24283b] text-xs text-[#9ca3af] space-y-2">
              <p className="text-[#cbd5e1] font-medium">请选择拒绝原因（支持多选，系统将定向衰减对应的特征维度）：</p>
              <div className="grid grid-cols-2 gap-2 pt-1">
                {[
                  { key: 'direction', label: '岗职方向不符', desc: '仅抑制职能类别' },
                  { key: 'industry', label: '赛道/行业不喜欢', desc: '仅抑制垂直行业' },
                  { key: 'location', label: '工作地点不合适', desc: '仅抑制期望城市' },
                  { key: 'company', label: '企业文化/不考虑', desc: '仅排除岗位，不连累特征' },
                  { key: 'skills', label: '技能要求过高/不匹配', desc: '微调技能契合度' },
                  { key: 'other', label: '其他/纯不感兴趣', desc: '全局温和微调' },
                ].map((item) => {
                  const isChecked = selectedRejectReasons.includes(item.key);
                  return (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => {
                        setSelectedRejectReasons((prev) =>
                          isChecked ? prev.filter((k) => k !== item.key) : [...prev, item.key]
                        );
                      }}
                      className={`p-2.5 rounded-lg border text-left transition-all ${
                        isChecked
                          ? 'bg-rose-950/40 border-rose-500/50 text-white'
                          : 'bg-[#181d2e] border-[#24283b] text-[#9ca3af] hover:border-[#38415c]'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className={isChecked ? 'text-rose-300' : 'text-[#cbd5e1]'}>
                          {item.label}
                        </span>
                        {isChecked && <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" />}
                      </div>
                      <p className="text-[10px] text-[#6b7280] mt-0.5">{item.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={() => {
                  // Direct reject without specific reason
                  handleFeedback(rejectModalJob.id, 'REJECT', rejectModalJob.company, []);
                  setRejectModalJob(null);
                  setSelectedRejectReasons([]);
                }}
                className="text-xs text-[#6b7280] hover:text-[#9ca3af] hover:underline px-2 py-1 font-mono"
              >
                跳过原因直接拒绝
              </button>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setRejectModalJob(null);
                    setSelectedRejectReasons([]);
                  }}
                  className="px-3 py-1.5 rounded-lg border border-[#24283b] text-xs text-[#9ca3af] hover:text-white hover:bg-[#1a1f30]"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleFeedback(
                      rejectModalJob.id,
                      'REJECT',
                      rejectModalJob.company,
                      selectedRejectReasons
                    );
                    setRejectModalJob(null);
                    setSelectedRejectReasons([]);
                  }}
                  className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-950/50 transition-all"
                >
                  确认并定向抑制
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
