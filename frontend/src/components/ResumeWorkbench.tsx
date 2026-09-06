import React, { useState, useEffect } from 'react';
import { api } from '../config';
import { ResumeItem, JobItem, ParseResumeResponse } from '../types';
import { ResumeImportModal } from './ResumeImportModal';
import { KeywordMatrixModal } from './KeywordMatrixModal';
import { ResumeMarkdownViewer } from './ResumeMarkdownViewer';
import { KeywordMatrix } from '../types';
import {
  FileText,
  Wand2,
  Sparkles,
  Check,
  Plus,
  Save,
  Copy,
  Star,
  Upload,
  Eye,
  Edit3,
  Columns,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Briefcase,
  Search,
  CheckCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  X,
  RefreshCw,
  Layers,
  ArrowRight,
  Cpu,
  Building,
  Target,
  FileDiff,
  Settings,
  Sliders,
  Globe,
  Zap,
  GitBranch
} from 'lucide-react';

export const ResumeWorkbench: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selectedResume, setSelectedResume] = useState<ResumeItem | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [jobId, setJobId] = useState('');
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [jobSearchText, setJobSearchText] = useState('');
  const [jobPickerOpen, setJobPickerOpen] = useState(false);
  const [optResult, setOptResult] = useState<any>(null);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // 调优模式与目标配置
  const [optimizeMode, setOptimizeMode] = useState<'TARGETED' | 'GENERAL'>('TARGETED');
  const [targetCompany, setTargetCompany] = useState('');
  const [targetPosition, setTargetPosition] = useState('');

  // 智能体引擎探活与用户选择
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);
  const [recommendedEngine, setRecommendedEngine] = useState('auto');
  const [selectedEngine, setSelectedEngine] = useState<string>(() => {
    return localStorage.getItem('jhtracker_ats_engine') || 'auto';
  });
  const [savingAsVersion, setSavingAsVersion] = useState(false);

  // Editable fields in workbench
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editCategory, setEditCategory] = useState<'GENERAL' | 'CUSTOMIZED'>('GENERAL');
  const [editSkills, setEditSkills] = useState<string[]>([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [viewMode, setViewMode] = useState<'split' | 'edit' | 'preview' | 'diff'>('split');
  const [diffViewTab, setDiffViewTab] = useState<'rendered' | 'source'>('rendered');
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showMatrixModal, setShowMatrixModal] = useState(false);
  const [showAgentConfigModal, setShowAgentConfigModal] = useState(false);
  const [customBaseUrl, setCustomBaseUrl] = useState('');
  const [customApiKey, setCustomApiKey] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [savingSettings, setSavingSettings] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{
    success?: boolean;
    latency_ms?: number;
    error?: string;
    message?: string;
  } | null>(null);
  const [testedConfigHash, setTestedConfigHash] = useState<string>('');

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3000);
  };

  const fetchResumes = async () => {
    try {
      const res = await api.get('/api/resumes');
      const list: ResumeItem[] = res.data || [];
      setResumes(list);

      // Auto-select default or first resume
      if (list.length > 0) {
        const defaultResume = list.find((r) => r.is_default) || list[0];
        if (!selectedResume || !list.some((r) => r.id === selectedResume.id)) {
          handleSelectResume(defaultResume);
        }
      }
    } catch (err) {
      console.error('Failed to load resumes', err);
    }
  };

  // Load jobs for quick selection in ATS matching
  const fetchRecentJobs = async () => {
    try {
      const res = await api.get('/api/jobs', {
        params: { limit: 50, page: 1 }
      });
      if (res.data && res.data.items) {
        setJobs(res.data.items);
      }
    } catch (err) {
      console.error('Failed to load candidate jobs', err);
    }
  };

  // 探测本地智能体引擎与设置
  const fetchAgents = async () => {
    try {
      const res = await api.get('/api/system/ai-agents');
      if (res.data) {
        setAvailableAgents(res.data.agents || []);
        if (res.data.recommended) {
          setRecommendedEngine(res.data.recommended);
        }
      }
      const settingsRes = await api.get('/api/system/llm-config');
      if (settingsRes.data) {
        const bUrl = settingsRes.data.base_url || '';
        const aKey = settingsRes.data.api_key || '';
        const mModel = settingsRes.data.model || '';
        setCustomBaseUrl(bUrl);
        setCustomApiKey(aKey);
        setCustomModel(mModel);
        if (bUrl.trim()) {
          // 已经配置过的端点默认允许更新或重新测试
          setTestedConfigHash(`${bUrl.trim()}|||${aKey.trim()}|||${mModel.trim()}`);
        }
      }
    } catch (err) {
      console.error('Failed to detect local agents or settings', err);
    }
  };

  const currentConfigHash = `${customBaseUrl.trim()}|||${customApiKey.trim()}|||${customModel.trim()}`;
  const isTestedAndPassed = Boolean(
    testResult?.success && testedConfigHash === currentConfigHash
  );

  const handleTestConnection = async () => {
    if (!customBaseUrl.trim()) {
      showNotification('请先填写 Base URL 接口地址');
      return;
    }
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await api.post('/api/system/llm-config/test', {
        base_url: customBaseUrl.trim(),
        api_key: customApiKey.trim(),
        model: customModel.trim() || 'claude-3-5-sonnet-20241022'
      });
      setTestResult(res.data);
      if (res.data?.success) {
        setTestedConfigHash(currentConfigHash);
        showNotification(`连接成功！延迟: ${res.data.latency_ms || 0}ms`);
      } else {
        showNotification('连接测试未通过，请检查错误提示');
      }
    } catch (err: any) {
      console.error('Test connection error', err);
      const errMsg = err?.response?.data?.error || err?.message || '测试请求失败';
      setTestResult({
        success: false,
        error: errMsg
      });
      showNotification('端点连通性测试失败');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSaveEndpointSettings = async () => {
    if (!isTestedAndPassed) {
      showNotification('请先点击“测试连接”并确保连通成功后，再保存配置');
      return;
    }
    setSavingSettings(true);
    try {
      await api.post('/api/system/llm-config', {
        base_url: customBaseUrl.trim(),
        api_key: customApiKey.trim(),
        model: customModel.trim()
      });
      showNotification('自定义 LLM API 端点配置保存成功！');
      setShowAgentConfigModal(false);
      await fetchAgents();
    } catch (err) {
      console.error('Failed to save AI endpoint settings', err);
      showNotification('保存端点配置失败，请检查后端状态');
    } finally {
      setSavingSettings(false);
    }
  };

  useEffect(() => {
    fetchResumes();
    fetchRecentJobs();
    fetchAgents();
  }, []);

  const handleSelectResume = (r: ResumeItem) => {
    setSelectedResume(r);
    setEditTitle(r.title);
    setEditContent(r.content_markdown || '');
    setEditCategory((r.category as any) || 'GENERAL');
    setEditSkills(r.skills || []);
    setOptResult(null);
    if (r.target_job_id) {
      setJobId(r.target_job_id);
    }
  };

  const handleSetDefault = async (resumeId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.post(`/api/resumes/${resumeId}/set-default`);
      showNotification('已将该版本设为默认简历 (优先参与 AI 推荐加权)');
      await fetchResumes();
    } catch (err) {
      console.error('Failed to set default', err);
    }
  };

  const handleSaveCurrent = async () => {
    setSaving(true);
    try {
      const payload = {
        title: editTitle.trim() || '未命名简历',
        category: editCategory,
        content_md: editContent,
        content_markdown: editContent,
        skills: editSkills,
        target_job_id: jobId || undefined
      };
      // 如果当前是新建未持久化的草稿，自动走 POST 创建
      if (!selectedResume || !selectedResume.id) {
        const res = await api.post('/api/resumes', payload);
        showNotification('简历创建并保存成功！');
        await fetchResumes();
        if (res.data) {
          handleSelectResume(res.data);
        }
      } else {
        await api.put(`/api/resumes/${selectedResume.id}`, payload);
        showNotification('简历更新成功！');
        await fetchResumes();
      }
    } catch (err) {
      console.error('Failed to save resume', err);
      showNotification('保存失败，请检查网络或后端');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAsNew = async () => {
    setSaving(true);
    try {
      const baseTitle = editTitle.trim() || '我的简历';
      const targetTag = selectedJob ? ` - ${selectedJob.company}` : '';
      const newTitle = baseTitle.includes('定制版') ? `${baseTitle} (副本)` : `${baseTitle}${targetTag} 定制版`;
      const payload = {
        title: newTitle,
        category: 'CUSTOMIZED',
        content_md: editContent,
        content_markdown: editContent,
        skills: editSkills,
        target_job_id: jobId || undefined
      };
      const res = await api.post('/api/resumes', payload);
      showNotification(`已另存为新版本: ${newTitle}`);
      await fetchResumes();
      if (res.data) {
        handleSelectResume(res.data);
      }
    } catch (err) {
      console.error('Failed to save as new resume', err);
      showNotification('另存为新版本失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteResume = async (resumeId: string, title: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`确定要删除简历版本 "${title}" 吗？此操作不可逆。`)) {
      return;
    }
    try {
      await api.delete(`/api/resumes/${resumeId}`);
      showNotification(`简历 "${title}" 已删除`);
      if (selectedResume?.id === resumeId) {
        setSelectedResume(null);
      }
      await fetchResumes();
    } catch (err) {
      console.error('Failed to delete resume', err);
      showNotification('删除失败');
    }
  };

  const handleAddSkill = () => {
    const s = newSkillInput.trim();
    if (!s) return;
    if (!editSkills.some((item) => item.toLowerCase() === s.toLowerCase())) {
      setEditSkills([...editSkills, s]);
    }
    setNewSkillInput('');
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setEditSkills(editSkills.filter((s) => s !== skillToRemove));
  };

  const handleImportSuccess = (parsed: ParseResumeResponse) => {
    const targetTitle = (parsed.title || '导入简历').trim();
    const contentMarkdown = parsed.content_markdown || '';
    const skills = parsed.skills || [];

    const isMatchExact = resumes.find(
      (r) => r.title === targetTitle && (r.skills?.join(',') || '') === skills.join(',')
    );

    if (isMatchExact) {
      handleSelectResume(isMatchExact);
      showNotification(`已成功加载并选定入库简历版本: "${targetTitle}"`);
      return;
    }

    const matchedByTitle = resumes.find((r) => r.title === targetTitle);
    if (matchedByTitle) {
      handleSelectResume(matchedByTitle);
      showNotification(`已选定对应版本: "${targetTitle}"`);
    } else {
      const cat = targetTitle.includes('定制') ? 'CUSTOMIZED' : 'GENERAL';
      const newDraftItem: ResumeItem = {
        id: '',
        title: targetTitle,
        category: cat,
        content_markdown: contentMarkdown,
        skills: skills
      };
      setSelectedResume(newDraftItem);
      setEditTitle(targetTitle);
      setEditContent(contentMarkdown);
      setEditCategory(cat as any);
      setEditSkills(skills);
      showNotification('简历已解析填充至工作台，请点击上方"保存"存入本地库');
    }
  };

  const handleSelectJob = (job: JobItem) => {
    setSelectedJob(job);
    setJobId(job.id);
    setTargetCompany(job.company || '');
    setTargetPosition(job.title || '');
    setJobPickerOpen(false);
    showNotification(`已关联目标岗位: ${job.company} - ${job.title}`);
  };

  const handleEngineChange = (engine: string) => {
    setSelectedEngine(engine);
    localStorage.setItem('jhtracker_ats_engine', engine);
    const label = engine === 'auto'
      ? `自动优选 → ${recommendedAgent?.name || recommendedEngine}`
      : (availableAgents.find(a => a.id === engine)?.name || engine);
    showNotification(`已切换 ATS 调优引擎为: ${label}`);
  };

  // 推荐引擎的完整 agent 信息（用于展示友好名称）
  const recommendedAgent = availableAgents.find(a => a.id === recommendedEngine);
  // 当前实际将使用的引擎信息（auto 时解析为推荐引擎）
  const effectiveEngineId = selectedEngine === 'auto' ? recommendedEngine : selectedEngine;
  const effectiveAgent = availableAgents.find(a => a.id === effectiveEngineId);

  const handleOptimize = async (saveAsNewVersion = false) => {
    if (!selectedResume || !selectedResume.id) {
      showNotification('请先保存当前简历后再进行专岗优化');
      return;
    }
    if (saveAsNewVersion) {
      setSavingAsVersion(true);
    } else {
      setOptimizing(true);
    }
    try {
      const res = await api.post('/api/resumes/optimize', {
        resume_id: selectedResume.id,
        job_id: jobId || undefined,
        resume_content_md: editContent || undefined,
        mode: optimizeMode,
        target_company: targetCompany.trim() || undefined,
        target_position: targetPosition.trim() || undefined,
        engine: selectedEngine,
        save_as_version: saveAsNewVersion,
      }, {
        timeout: 120000,
      });
      setOptResult(res.data);
      if (saveAsNewVersion) {
        showNotification('已成功生成并另存为独立的专岗定制版简历！');
      } else {
        showNotification('ATS 诊断分析完成！');
      }
      // 如果后端自动生成了独立优化版，刷新列表并自动切换选中新版本
      if (res.data?.optimized_resume_id) {
        const listRes = await api.get('/api/resumes');
        const list: ResumeItem[] = listRes.data || [];
        setResumes(list);
        const newRes = list.find((item) => item.id === res.data.optimized_resume_id);
        if (newRes) {
          handleSelectResume(newRes);
        }
      }
    } catch (err) {
      console.error('Optimize failed', err);
      showNotification('专岗优化分析失败，请检查智能体服务或网络');
    } finally {
      setOptimizing(false);
      setSavingAsVersion(false);
    }
  };

  const handleApplyAIToEditor = () => {
    if (optResult?.optimized_markdown) {
      setEditContent(optResult.optimized_markdown);
      if (optResult.missing_keywords && optResult.missing_keywords.length > 0) {
        const merged = Array.from(new Set([...editSkills, ...optResult.missing_keywords]));
        setEditSkills(merged);
      }
      showNotification('已将 AI 优化建议及缺失关键词应用到当前编辑器');
    }
  };

  const handleAddSingleMissingSkill = (skill: string) => {
    if (!editSkills.includes(skill)) {
      setEditSkills([...editSkills, skill]);
      showNotification(`已将 "${skill}" 补充至技能清单`);
    }
  };

  // Render markdown text with highlighted skills
  const renderHighlightedContent = () => {
    return (
      <ResumeMarkdownViewer
        content={editContent}
        highlightSkills={editSkills}
        theme="cyan"
        emptyMessage="暂无简历 Markdown 内容，可在左侧输入、粘贴或一键导入本地简历"
      />
    );
  };

  // Render text helper for any markdown content
  const renderMarkdownHelper = (content: string, highlightSkills: string[] = [], theme: 'cyan' | 'emerald' | 'amber' = 'emerald') => {
    return (
      <ResumeMarkdownViewer
        content={content}
        highlightSkills={highlightSkills}
        theme={theme}
        emptyMessage="暂无内容"
      />
    );
  };

  const filteredJobs = jobs.filter(
    (j) =>
      !jobSearchText ||
      j.title.toLowerCase().includes(jobSearchText.toLowerCase()) ||
      j.company.toLowerCase().includes(jobSearchText.toLowerCase()) ||
      (j.city && j.city.toLowerCase().includes(jobSearchText.toLowerCase()))
  );

  return (
    <div className="space-y-3">
      {/* 紧凑化顶栏与综合状态条 */}
      <div className="px-4 py-2.5 rounded-xl border border-[#24283b] bg-[#11131c] shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-cyan-950/60 border border-cyan-500/30 rounded-lg text-cyan-400">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-[#f3f4f6]">多版本简历与专岗优化工作台</h2>
              <span className="text-[10px] bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 px-2 py-0.2 rounded-full font-mono">
                {resumes.length} 个本地版本
              </span>
            </div>
            <p className="text-[11px] text-[#9ca3af] hidden sm:block">
              离线保密存储 · 双栏实时 Markdown 编辑渲染 · ATS 关键词对齐诊断
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={() => setShowMatrixModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-950/40 hover:bg-purple-900/60 text-purple-300 text-xs font-medium rounded-lg border border-purple-500/40 shadow-sm transition"
            title="查看或调整该简历的推荐关键词矩阵（核心技能、研究领域、排斥词）"
          >
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>推荐画像矩阵</span>
          </button>
          <button
            onClick={() => setImportModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#151824] hover:bg-[#1b1e2e] text-cyan-300 text-xs font-medium rounded-lg border border-cyan-500/30 shadow-sm transition"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>导入文件</span>
          </button>
          <button
            onClick={() => {
              const newR: ResumeItem = {
                id: '',
                title: '新建技术简历',
                category: 'GENERAL',
                content_markdown: '# 个人简历\n\n## 专业技能\n- Python, React, FastAPI, Docker\n\n## 项目经历\n- 核心开发者...',
                skills: ['Python', 'React', 'FastAPI', 'Docker']
              };
              setSelectedResume(newR);
              setEditTitle(newR.title);
              setEditContent(newR.content_markdown);
              setEditCategory('GENERAL');
              setEditSkills(newR.skills || []);
              setOptResult(null);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded-lg shadow-sm transition"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>新建空白</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 px-3.5 py-2 rounded-xl text-xs flex items-center gap-2 shadow-sm animate-fadeIn">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* 核心工作台主视口区域 (左侧版本抽屉/面板 + 中间全宽双栏编辑器 + 右侧常驻 ATS 诊断面板) */}
      <div className="grid grid-cols-12 gap-3 items-start">
        {/* 左侧版本列表 (收展式，默认占 2 列，收起占 0 列) */}
        {showLeftSidebar ? (
          <div className="col-span-12 md:col-span-4 xl:col-span-2 bg-[#11131c] p-3 rounded-xl border border-[#24283b] space-y-2.5 shadow-sm">
            <div className="flex justify-between items-center pb-2 border-b border-[#24283b]">
              <span className="font-bold text-xs text-[#f3f4f6] flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-cyan-400" />
                本地版本库
              </span>
              <button
                onClick={() => setShowLeftSidebar(false)}
                className="text-[10px] text-[#6b7280] hover:text-[#f3f4f6] p-0.5 rounded"
                title="折叠列表腾出空间"
              >
                收起
              </button>
            </div>

            <div className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto pr-0.5 custom-scrollbar">
              {resumes.map((r) => {
                const isSelected = selectedResume?.id === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => handleSelectResume(r)}
                    className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'border-cyan-500/80 bg-[#1b1e2e] shadow-sm'
                        : 'border-[#24283b] bg-[#151824] hover:border-cyan-500/40 hover:bg-[#181b2a]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <div className="font-bold text-[#f3f4f6] truncate text-[11px] flex-1">{r.title}</div>
                      {r.parent_resume_id && (
                        <span className="text-[9px] text-purple-400 bg-purple-950/60 border border-purple-500/30 px-1 rounded flex items-center gap-0.5" title={`派生自原始版本: ${r.parent_resume_id}`}>
                          <GitBranch className="h-2 w-2" />
                          派生
                        </span>
                      )}
                      {r.is_default && (
                        <span className="flex items-center gap-0.5 text-[9px] bg-amber-950/60 text-amber-400 border border-amber-500/30 px-1 rounded font-mono flex-shrink-0">
                          <Star className="h-2 w-2 fill-amber-400" />
                          默认
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-1 mt-1 text-[10px] text-[#9ca3af]">
                      <span
                        className={`px-1 py-0.2 rounded text-[9px] ${
                          r.version_type === 'AI_OPTIMIZED'
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                            : 'bg-cyan-950/60 text-cyan-300 border border-cyan-500/30'
                        }`}
                      >
                        {r.version_type === 'AI_OPTIMIZED' ? 'AI 优化' : '原始'}
                      </span>
                      <span
                        className={`px-1 py-0.2 rounded text-[9px] ${
                          r.category === 'CUSTOMIZED'
                            ? 'bg-purple-950/60 text-purple-300 border border-purple-500/30'
                            : 'bg-blue-950/60 text-blue-300 border border-blue-500/30'
                        }`}
                      >
                        {r.category === 'CUSTOMIZED' ? '专岗' : '通用'}
                      </span>
                      {r.skills && r.skills.length > 0 && (
                        <span className="text-[#6b7280] font-mono text-[9px]">
                          {r.skills.length}项技能
                        </span>
                      )}
                    </div>

                    <div className="mt-2 pt-1.5 border-t border-[#24283b]/60 flex items-center justify-between">
                      <button
                        onClick={(e) => handleSetDefault(r.id, e)}
                        disabled={r.is_default}
                        className={`text-[10px] flex items-center gap-1 transition ${
                          r.is_default
                            ? 'text-amber-400 cursor-default'
                            : 'text-[#9ca3af] hover:text-amber-300'
                        }`}
                      >
                        <Star className={`h-2.5 w-2.5 ${r.is_default ? 'fill-amber-400' : ''}`} />
                        {r.is_default ? '推荐画像' : '设默认'}
                      </button>
                      <button
                        onClick={(e) => handleDeleteResume(r.id, r.title, e)}
                        title="删除该简历版本"
                        className="text-[10px] text-[#6b7280] hover:text-rose-400 p-0.5 rounded hover:bg-rose-950/40 transition"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                );
              })}

              {resumes.length === 0 && (
                <div className="py-8 text-center text-[#6b7280] text-xs">
                  暂无简历，点击上方“导入”或“新建”
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="col-span-12 md:col-span-1 xl:col-span-auto flex flex-col items-center">
            <button
              onClick={() => setShowLeftSidebar(true)}
              className="p-2 bg-[#11131c] border border-[#24283b] rounded-xl text-cyan-400 hover:text-cyan-300 hover:border-cyan-500/40 text-xs flex items-center gap-1 shadow-sm"
              title="展开版本库"
            >
              <Layers className="h-4 w-4" />
              <span className="text-[11px] writing-vertical hidden md:inline">版本库</span>
            </button>
          </div>
        )}

        {/* 中间编辑与双栏预览主工作区 */}
        <div
          className={`space-y-3 ${
            showLeftSidebar
              ? 'col-span-12 md:col-span-8 xl:col-span-7'
              : 'col-span-12 md:col-span-11 xl:col-span-8'
          }`}
        >
          {/* 编辑器操作工具条 */}
          <div className="bg-[#11131c] p-2.5 rounded-xl border border-[#24283b] flex flex-wrap items-center justify-between gap-2 shadow-sm">
            <div className="flex items-center gap-2 flex-1 min-w-[240px]">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="简历标题（例如：后端开发-通用版）"
                className="bg-[#151824] border border-[#24283b] text-[#f3f4f6] font-bold text-xs rounded-lg px-2.5 py-1.5 w-full max-w-xs outline-none focus:border-cyan-500"
              />
              <select
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value as any)}
                className="bg-[#151824] border border-[#24283b] text-xs text-[#d1d5db] rounded-lg px-2 py-1.5 outline-none focus:border-cyan-500"
              >
                <option value="GENERAL">通用基准</option>
                <option value="CUSTOMIZED">专岗定制</option>
              </select>
              {(!selectedResume || !selectedResume.id) && (
                <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-950/40 border border-amber-500/30 px-1.5 py-0.5 rounded">
                  <AlertCircle className="h-2.5 w-2.5" />
                  未入库草稿
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5">
              {/* Layout Switcher */}
              <div className="bg-[#151824] p-0.5 rounded-lg border border-[#24283b] flex items-center text-xs">
                <button
                  onClick={() => setViewMode('split')}
                  className={`px-2 py-1 rounded flex items-center gap-1 ${
                    viewMode === 'split'
                      ? 'bg-[#1b1e2e] text-cyan-300 font-semibold'
                      : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                  }`}
                  title="分屏双栏实时预览"
                >
                  <Columns className="h-3 w-3" />
                  <span className="text-[10px]">分屏</span>
                </button>
                <button
                  onClick={() => setViewMode('edit')}
                  className={`px-2 py-1 rounded flex items-center gap-1 ${
                    viewMode === 'edit'
                      ? 'bg-[#1b1e2e] text-cyan-300 font-semibold'
                      : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                  }`}
                  title="纯源码编辑"
                >
                  <Edit3 className="h-3 w-3" />
                  <span className="text-[10px]">编辑</span>
                </button>
                <button
                  onClick={() => setViewMode('preview')}
                  className={`px-2 py-1 rounded flex items-center gap-1 ${
                    viewMode === 'preview'
                      ? 'bg-[#1b1e2e] text-cyan-300 font-semibold'
                      : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                  }`}
                  title="纯高亮预览"
                >
                  <Eye className="h-3 w-3" />
                  <span className="text-[10px]">预览</span>
                </button>
                {optResult?.optimized_markdown && (
                  <button
                    onClick={() => setViewMode('diff')}
                    className={`flex items-center gap-1 px-2 py-1 rounded transition text-xs ${
                      viewMode === 'diff'
                        ? 'bg-amber-500/20 text-amber-300 font-medium border border-amber-500/40'
                        : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                    }`}
                    title="AI润色对比模式"
                  >
                    <FileDiff className="h-3 w-3 text-amber-400" />
                    <span className="text-[10px] font-bold">AI润色对比</span>
                  </button>
                )}
              </div>

              {/* 保存操作 */}
              <button
                disabled={saving}
                onClick={handleSaveCurrent}
                className="flex items-center gap-1 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg shadow-sm transition"
              >
                <Save className="h-3.5 w-3.5" />
                <span>{saving ? '保存中' : (!selectedResume || !selectedResume.id) ? '存入库' : '保存'}</span>
              </button>
              <button
                disabled={saving}
                onClick={handleSaveAsNew}
                className="flex items-center gap-1 px-2.5 py-1.5 bg-[#151824] hover:bg-[#1b1e2e] text-cyan-300 text-xs font-medium rounded-lg border border-cyan-500/30 transition"
                title="复制当前编辑内容为独立的专岗定制版"
              >
                <Copy className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">另存为定制版</span>
              </button>
            </div>
          </div>

          {/* 技能画像（核心技术栈矩阵联动） */}
          <div className="bg-[#11131c] px-3 py-2 rounded-xl border border-[#24283b] flex flex-wrap items-center gap-2 shadow-sm">
            <div className="flex items-center gap-1.5 mr-1">
              <span className="text-[11px] font-bold text-[#d1d5db] flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-purple-400" />
                核心技术栈 ({editSkills.length})
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-950/70 border border-purple-500/30 text-purple-300 font-mono" title="画像技能与推荐矩阵Core象限联动，享有2.5x核心检索与推荐加权">
                Core 2.5x
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 items-center max-h-16 overflow-y-auto pr-1">
              {editSkills.map((s, idx) => (
                <span
                  key={idx}
                  className="bg-purple-950/40 text-purple-200 border border-purple-500/30 px-2 py-0.5 rounded text-[10px] font-mono flex items-center gap-1.5 hover:border-purple-400/60 transition group"
                >
                  <span>{s}</span>
                  <button
                    onClick={() => handleRemoveSkill(s)}
                    className="hover:text-rose-400 text-purple-400/60 hover:bg-purple-900/40 rounded-full w-3.5 h-3.5 flex items-center justify-center font-bold text-xs"
                    title="从核心技能移除"
                  >
                    ×
                  </button>
                </span>
              ))}
              {editSkills.length === 0 && (
                <span className="text-[10px] text-[#6b7280] italic">
                  暂无核心技能，输入技术词回车添加或点击右侧打开四象限矩阵
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5 ml-auto">
              <input
                type="text"
                placeholder="添加核心技能..."
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                className="bg-[#151824] border border-[#24283b] text-xs text-[#f3f4f6] px-2 py-0.5 rounded outline-none focus:border-purple-500 w-32"
              />
              <button
                onClick={handleAddSkill}
                className="px-2 py-0.5 bg-purple-600/30 text-purple-300 hover:bg-purple-600/50 rounded text-xs font-bold transition border border-purple-500/30"
                title="添加至核心技能 (Core)"
              >
                +
              </button>
              <button
                onClick={() => setShowMatrixModal(true)}
                className="px-2 py-0.5 text-[10px] text-purple-300 hover:text-purple-200 bg-purple-950/60 border border-purple-500/40 rounded flex items-center gap-1 transition"
                title="展开完整四象限画像矩阵（业务领域、通用基石、负向排斥词）"
              >
                <Sparkles className="h-2.5 w-2.5" />
                <span>象限矩阵</span>
              </button>
            </div>
          </div>

          {/* Markdown 源码与高亮渲染双栏自适应面板 / AI润色对比面板 */}
          {viewMode === 'diff' && optResult?.optimized_markdown ? (
            <div className="bg-[#11131c] p-3 rounded-xl border border-amber-500/30 flex flex-col shadow-lg">
              {/* Diff Top Bar */}
              <div className="flex flex-wrap justify-between items-center pb-2 mb-2 border-b border-[#24283b] gap-2">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-xs font-bold text-amber-300">
                    <FileDiff className="h-3.5 w-3.5" />
                    AI润色对比模式
                  </span>
                  <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-full bg-cyan-950/40 border border-cyan-500/20 text-cyan-300">
                    <span className="text-[9px]">🤖</span>
                    <span className="font-mono">{optResult.engine_used || '智能体引擎'}</span>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {/* Tab: 渲染对比 vs 源码对比 */}
                  <div className="flex items-center bg-[#151824] p-0.5 rounded-lg border border-[#24283b] text-xs">
                    <button
                      onClick={() => setDiffViewTab('rendered')}
                      className={`px-2 py-0.5 rounded text-[10px] transition ${
                        diffViewTab === 'rendered' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                      }`}
                    >
                      排版预览对比
                    </button>
                    <button
                      onClick={() => setDiffViewTab('source')}
                      className={`px-2 py-0.5 rounded text-[10px] transition ${
                        diffViewTab === 'source' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-[#9ca3af] hover:text-[#f3f4f6]'
                      }`}
                    >
                      Markdown源码对比
                    </button>
                  </div>
                  {/* Quick Action in Diff */}
                  <button
                    onClick={handleApplyAIToEditor}
                    className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold rounded transition shadow-sm"
                  >
                    <Check className="h-3 w-3" />
                    采纳并覆盖
                  </button>
                  <button
                    onClick={() => setViewMode('split')}
                    className="px-2 py-1 bg-[#1e2235] hover:bg-[#282d44] text-[#9ca3af] hover:text-[#f3f4f6] text-[10px] rounded transition"
                  >
                    退出对比
                  </button>
                </div>
              </div>

              {/* Diff Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {/* Left: Original / Current Edit */}
                <div className="flex flex-col bg-[#0e1017] p-2.5 rounded-lg border border-[#24283b]">
                  <div className="flex justify-between items-center pb-1.5 mb-1.5 border-b border-[#24283b] text-[10px]">
                    <span className="font-bold text-[#9ca3af]">当前修改前版本 (编辑区)</span>
                    <span className="text-[#6b7280] font-mono">{editContent.length} 字符</span>
                  </div>
                  <div className="w-full h-[calc(100vh-380px)] min-h-[460px] overflow-y-auto custom-scrollbar p-1">
                    {diffViewTab === 'rendered' ? (
                      renderMarkdownHelper(editContent, optResult.matched_keywords || editSkills, 'cyan')
                    ) : (
                      <pre className="text-[11px] font-mono text-[#9ca3af] whitespace-pre-wrap leading-relaxed select-text">
                        {editContent}
                      </pre>
                    )}
                  </div>
                </div>

                {/* Right: AI Optimized */}
                <div className="flex flex-col bg-[#0e1017] p-2.5 rounded-lg border border-amber-500/40">
                  <div className="flex justify-between items-center pb-1.5 mb-1.5 border-b border-amber-500/30 text-[10px]">
                    <span className="font-bold text-amber-300 flex items-center gap-1">
                      <Sparkles className="h-3 w-3 text-amber-400" />
                      AI 深度润色优化版
                    </span>
                    <span className="text-amber-400 font-mono">{optResult.optimized_markdown.length} 字符</span>
                  </div>
                  <div className="w-full h-[calc(100vh-380px)] min-h-[460px] overflow-y-auto custom-scrollbar p-1">
                    {diffViewTab === 'rendered' ? (
                      renderMarkdownHelper(optResult.optimized_markdown, optResult.matched_keywords || editSkills, 'amber')
                    ) : (
                      <pre className="text-[11px] font-mono text-amber-200/90 whitespace-pre-wrap leading-relaxed select-text">
                        {optResult.optimized_markdown}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {/* Markdown Textarea */}
              {(viewMode === 'split' || viewMode === 'edit') && (
                <div
                  className={`bg-[#11131c] p-3 rounded-xl border border-[#24283b] flex flex-col ${
                    viewMode === 'edit' ? 'lg:col-span-2' : ''
                  }`}
                >
                  <div className="flex justify-between items-center pb-1.5 mb-1.5 border-b border-[#24283b] text-[11px] text-[#9ca3af]">
                    <span className="font-bold text-[#f3f4f6]">Markdown 源码</span>
                    <span className="font-mono text-[10px]">{editContent.length} 字符</span>
                  </div>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    placeholder="在此输入或编辑简历 Markdown 内容..."
                    className="w-full h-[calc(100vh-360px)] min-h-[480px] p-3 bg-[#0e1017] border border-[#24283b] rounded-lg text-xs font-mono text-[#f3f4f6] resize-none focus:outline-none focus:border-cyan-500/60 leading-relaxed custom-scrollbar"
                  />
                </div>
              )}

              {/* Rendered ATS Preview */}
              {(viewMode === 'split' || viewMode === 'preview') && (
                <div
                  className={`bg-[#11131c] p-3 rounded-xl border border-[#24283b] flex flex-col ${
                    viewMode === 'preview' ? 'lg:col-span-2' : ''
                  }`}
                >
                  <div className="flex justify-between items-center pb-1.5 mb-1.5 border-b border-[#24283b] text-[11px] text-[#9ca3af]">
                    <span className="font-bold text-[#f3f4f6]">实时渲染与画像高亮</span>
                    <span className="text-cyan-400 text-[10px]">青色标签为已命中技能</span>
                  </div>
                  <div className="w-full h-[calc(100vh-360px)] min-h-[480px] p-3 bg-[#0e1017] border border-[#24283b] rounded-lg overflow-y-auto custom-scrollbar">
                    {renderHighlightedContent()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 右侧常驻 ATS 专岗诊断与调优面板 (占 3 列) */}
        <div className="col-span-12 xl:col-span-3 bg-[#11131c] p-3.5 rounded-xl border border-[#24283b] space-y-3 shadow-sm flex flex-col">
          <div className="flex items-center justify-between pb-2 border-b border-[#24283b]">
            <div className="flex items-center gap-1.5">
              <Wand2 className="h-4 w-4 text-cyan-400" />
              <span className="font-bold text-xs text-[#f3f4f6]">ATS 诊断调优</span>
            </div>
            {/* 智能体引擎选择胶囊下拉与设置入口 */}
            <div className="flex items-center gap-1.5">
              <select
                value={selectedEngine}
                onChange={(e) => handleEngineChange(e.target.value)}
                className="bg-[#151824] border border-cyan-500/30 text-cyan-300 text-[10px] rounded px-1.5 py-0.5 outline-none hover:border-cyan-400 transition cursor-pointer font-mono max-w-[130px] truncate"
              >
                <option value="auto">⚡ 自动优选 → {recommendedAgent?.name || recommendedEngine || '等待探测...'}</option>
                {availableAgents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.id === 'builtin' ? '📦 ' : agent.id === 'custom_api' ? '🌐 ' : '🤖 '}
                    {agent.name}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setShowAgentConfigModal(true)}
                title="配置自定义 LLM API 端点 (OpenAI 兼容)"
                className="p-1 rounded bg-[#151824] border border-[#24283b] hover:border-cyan-500/60 text-[#9ca3af] hover:text-cyan-300 transition"
              >
                <Settings className="h-3 w-3" />
              </button>
            </div>
          </div>

          {/* 当前调度引擎状态条：让用户直观看到实际命中的本地 CLI */}
          <div className="px-2 py-1 bg-[#0e1017] rounded-md border border-[#24283b] flex items-center justify-between text-[10px]">
            <span className="text-[#6b7280] flex items-center gap-1">
              <Cpu className="h-3 w-3 text-cyan-400" />
              当前调度:
            </span>
            <span className="font-mono font-medium flex items-center gap-1">
              {effectiveEngineId === 'builtin' ? (
                <span className="text-amber-400/90 flex items-center gap-0.5">
                  <span>📦</span> {effectiveAgent?.name || '内置规则引擎'}
                </span>
              ) : effectiveEngineId === 'custom_api' ? (
                <span className="text-emerald-400 flex items-center gap-0.5">
                  <span>🌐</span> {effectiveAgent?.name || '自定义 LLM API'}
                  {selectedEngine === 'auto' && (
                    <span className="text-[9px] text-emerald-500/80 bg-emerald-950/40 px-1 rounded">自动优选</span>
                  )}
                </span>
              ) : (
                <span className="text-cyan-300 flex items-center gap-0.5">
                  <span>🤖</span> {effectiveAgent?.name || effectiveEngineId}
                  {selectedEngine === 'auto' && (
                    <span className="text-[9px] text-cyan-500/70 bg-cyan-950/40 px-1 rounded">自动优选</span>
                  )}
                </span>
              )}
            </span>
          </div>

          {/* 调优模式 Tab 切换 */}
          <div className="grid grid-cols-2 gap-1 p-0.5 bg-[#0e1017] rounded-lg border border-[#24283b] text-xs">
            <button
              onClick={() => setOptimizeMode('TARGETED')}
              className={`py-1 rounded font-medium transition flex items-center justify-center gap-1 ${
                optimizeMode === 'TARGETED'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-[#9ca3af] hover:text-[#f3f4f6]'
              }`}
            >
              <Target className="h-3 w-3" />
              <span>专岗调优</span>
            </button>
            <button
              onClick={() => setOptimizeMode('GENERAL')}
              className={`py-1 rounded font-medium transition flex items-center justify-center gap-1 ${
                optimizeMode === 'GENERAL'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-[#9ca3af] hover:text-[#f3f4f6]'
              }`}
            >
              <Sparkles className="h-3 w-3" />
              <span>通用 STAR 润色</span>
            </button>
          </div>

          {/* 专岗模式下的维度配置 (企业 / 岗位 / 企业+岗位) */}
          {optimizeMode === 'TARGETED' && (
            <div className="space-y-2 bg-[#0e1017]/80 p-2.5 rounded-lg border border-[#24283b] animate-fadeIn">
              <div className="flex items-center justify-between text-[11px] text-[#9ca3af]">
                <span className="font-semibold text-[#d1d5db]">专岗目标设定:</span>
                <button
                  onClick={() => setJobPickerOpen(!jobPickerOpen)}
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 text-[10px]"
                >
                  <Search className="h-2.5 w-2.5" />
                  {jobPickerOpen ? '收起库' : '从岗位库一键填入'}
                </button>
              </div>

              {/* 目标企业 */}
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-[10px] text-[#9ca3af]">
                  <Building className="h-2.5 w-2.5 text-cyan-400" />
                  <span>目标企业 (可选，按大厂/文化对齐)</span>
                </div>
                <input
                  type="text"
                  placeholder="如：腾讯、字节跳动、外企..."
                  value={targetCompany}
                  onChange={(e) => setTargetCompany(e.target.value)}
                  className="w-full px-2 py-1 bg-[#151824] border border-[#24283b] rounded text-xs text-[#f3f4f6] outline-none focus:border-cyan-500"
                />
              </div>

              {/* 目标岗位 */}
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-[10px] text-[#9ca3af]">
                  <Briefcase className="h-2.5 w-2.5 text-cyan-400" />
                  <span>目标职位 / 岗位 (可选，按技能栈对齐)</span>
                </div>
                <input
                  type="text"
                  placeholder="如：后端研发、全栈工程师、风控算法..."
                  value={targetPosition}
                  onChange={(e) => setTargetPosition(e.target.value)}
                  className="w-full px-2 py-1 bg-[#151824] border border-[#24283b] rounded text-xs text-[#f3f4f6] outline-none focus:border-cyan-500"
                />
              </div>

              {/* 已选公共岗位标签 */}
              {selectedJob && (
                <div className="p-1.5 bg-[#151824] border border-cyan-500/30 rounded text-[10px] text-cyan-300 flex items-center justify-between">
                  <span className="truncate">已关联库内 JD: {selectedJob.company} - {selectedJob.title}</span>
                  <button
                    onClick={() => {
                      setSelectedJob(null);
                      setJobId('');
                    }}
                    className="text-[#6b7280] hover:text-rose-400 ml-1"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              )}

              {/* 岗位库快捷选定列表 */}
              {jobPickerOpen && (
                <div className="p-2 bg-[#11131c] border border-[#24283b] rounded-lg space-y-1.5 mt-1 animate-fadeIn">
                  <div className="relative">
                    <Search className="h-3 w-3 text-[#6b7280] absolute left-2 top-2" />
                    <input
                      type="text"
                      placeholder="筛选职位、公司或城市..."
                      value={jobSearchText}
                      onChange={(e) => setJobSearchText(e.target.value)}
                      className="w-full pl-6 pr-2 py-1 bg-[#151824] border border-[#24283b] rounded text-[11px] text-[#f3f4f6] outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div className="max-h-40 overflow-y-auto space-y-1 custom-scrollbar pr-0.5">
                    {filteredJobs.slice(0, 15).map((j) => (
                      <div
                        key={j.id}
                        onClick={() => handleSelectJob(j)}
                        className="p-1.5 rounded hover:bg-[#1b1e2e] cursor-pointer text-[11px] border border-transparent hover:border-cyan-500/30 transition flex flex-col"
                      >
                        <span className="font-bold text-[#f3f4f6] truncate">{j.title}</span>
                        <span className="text-[10px] text-[#9ca3af]">
                          {j.company} · {j.city || '全国'}
                        </span>
                      </div>
                    ))}
                    {filteredJobs.length === 0 && (
                      <div className="py-2 text-center text-[10px] text-[#6b7280]">暂无匹配岗位</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 通用模式下的提示 */}
          {optimizeMode === 'GENERAL' && (
            <div className="p-2.5 bg-[#0e1017]/80 border border-[#24283b] rounded-lg text-xs text-[#9ca3af] space-y-1">
              <div className="text-[#f3f4f6] font-semibold text-[11px] flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-cyan-400" /> 全局通用调优 (Master Polish)
              </div>
              <p className="text-[10px] text-[#9ca3af] leading-relaxed">
                无需绑定具体岗位，深度遵循 STAR 法则强化量化指标（百分比/TPS/成果），收敛冗余描述，生成高质量母版简历。
              </p>
            </div>
          )}

          {/* 启动诊断与调优操作双按钮 */}
          <div className="grid grid-cols-1 gap-1.5">
            <button
              onClick={() => handleOptimize(false)}
              disabled={!selectedResume || optimizing || savingAsVersion}
              className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg text-xs shadow-md shadow-cyan-950/40 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              {optimizing ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>智能体正在深入分析中...</span>
                </>
              ) : (
                <>
                  <Wand2 className="h-3.5 w-3.5" />
                  <span>
                    {optimizeMode === 'TARGETED'
                      ? targetCompany || targetPosition
                        ? `针对【${targetCompany || ''} ${targetPosition || ''}】深度调优`
                        : '专岗 ATS 诊断调优'
                      : '通用 STAR 深度润色调优'}
                  </span>
                </>
              )}
            </button>
          </div>

          {/* 诊断报告结果展示卡片 */}
          {optResult ? (
            <div className="space-y-2.5 pt-1 border-t border-[#24283b]/60">
              {/* ATS 分数与评级 */}
              <div className="p-2.5 bg-[#151824] border border-cyan-500/30 rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-[#9ca3af] flex items-center gap-1">
                    <span>ATS 关键词契合指数</span>
                    {optResult.engine_used && (
                      <span className="text-[9px] text-cyan-300 bg-cyan-950/80 border border-cyan-500/30 px-1.5 py-0.5 rounded font-mono flex items-center gap-0.5">
                        <span>🤖</span>
                        {optResult.engine_used}
                      </span>
                    )}
                  </div>
                  <div className="text-xl font-black text-cyan-400 font-mono">
                    {optResult.ats_score ?? 80}
                    <span className="text-xs text-[#9ca3af] font-normal"> / 100</span>
                  </div>
                </div>
                <div className="text-right">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                      (optResult.ats_score ?? 80) >= 85
                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40'
                        : 'bg-amber-950/80 text-amber-300 border border-amber-500/40'
                    }`}
                  >
                    {(optResult.ats_score ?? 80) >= 85 ? '契合度极高' : '存在技能缺口'}
                  </span>
                </div>
              </div>

              {/* 命中与缺失关键词标签 */}
              {optResult.matched_keywords && (
                <div className="space-y-1 text-xs">
                  <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" /> 已命中技术栈 ({optResult.matched_keywords.length})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {optResult.matched_keywords.map((k: string, i: number) => (
                      <span
                        key={i}
                        className="bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 px-1.5 py-0.2 rounded text-[10px] font-mono"
                      >
                        {k}
                      </span>
                    ))}
                    {optResult.matched_keywords.length === 0 && (
                      <span className="text-[10px] text-[#6b7280]">无明显重合关键词</span>
                    )}
                  </div>
                </div>
              )}

              {optResult.missing_keywords && optResult.missing_keywords.length > 0 && (
                <div className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-rose-400 font-bold flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" /> 建议补齐的缺失词 ({optResult.missing_keywords.length})
                    </span>
                    <span className="text-[9px] text-[#6b7280]">点击标签直接加入画像</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {optResult.missing_keywords.map((k: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => handleAddSingleMissingSkill(k)}
                        className="bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-500/30 hover:border-rose-400 px-1.5 py-0.2 rounded text-[10px] font-mono transition flex items-center gap-0.5"
                        title="点击一键补充到当前简历技能清单"
                      >
                        <span>{k}</span>
                        <Plus className="h-2.5 w-2.5 opacity-60" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 核心建议列表 */}
              {optResult.suggestions && (
                <div className="space-y-1">
                  <span className="text-[10px] text-cyan-300 font-bold">修改建议:</span>
                  <ul className="text-[11px] text-[#d1d5db] space-y-1 list-disc list-inside bg-[#0e1017] p-2 rounded border border-[#24283b] leading-relaxed max-h-48 overflow-y-auto custom-scrollbar">
                    {optResult.suggestions.map((s: string, idx: number) => (
                      <li key={idx} className="text-[#9ca3af]">
                        <span className="text-[#e5e7eb]">{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 采纳与另存操作区 */}
              {optResult.optimized_markdown && (
                <div className="space-y-1.5 pt-1">
                  {/* 查看完整对比 */}
                  <button
                    onClick={() => setViewMode('diff')}
                    className="w-full py-1.5 bg-amber-950/50 hover:bg-amber-900/50 text-amber-300 text-xs font-bold rounded-lg border border-amber-500/40 transition flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <FileDiff className="h-3.5 w-3.5 text-amber-400" />
                    <span>查看原版 vs AI润色版完整对比</span>
                  </button>

                  <button
                    onClick={handleApplyAIToEditor}
                    className="w-full py-1.5 bg-[#151824] hover:bg-[#1b1e2e] text-cyan-300 text-xs font-semibold rounded-lg border border-cyan-500/40 transition flex items-center justify-center gap-1"
                  >
                    <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
                    <span>采纳润色内容至当前编辑区</span>
                  </button>

                  <button
                    onClick={() => handleOptimize(true)}
                    disabled={savingAsVersion}
                    className="w-full py-1.5 bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 text-xs font-semibold rounded-lg border border-emerald-500/40 transition flex items-center justify-center gap-1 disabled:opacity-50"
                  >
                    {savingAsVersion ? (
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    ) : (
                      <Layers className="h-3 w-3 text-emerald-400" />
                    )}
                    <span>另存为专岗派生独立子版本</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-[#6b7280] text-xs space-y-1">
              <Sparkles className="h-6 w-6 text-[#374151] mx-auto mb-1" />
              <p>暂无诊断分析</p>
              <p className="text-[10px] text-[#4b5563]">
                选定目标岗位并点击上方按钮，即可开始 ATS 契合度与关键词缺口对齐
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Resume Import Modal */}
      <ResumeImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportSuccess={handleImportSuccess}
      />

      {/* Keyword Matrix Modal */}
      <KeywordMatrixModal
        isOpen={showMatrixModal}
        onClose={() => setShowMatrixModal(false)}
        resumeId={selectedResume?.id}
        resumeTitle={selectedResume?.title || ''}
        markdownContent={editContent}
        initialMatrix={selectedResume?.keywords_matrix}
        onSaveSuccess={async (updatedMatrix: any) => {
          if (selectedResume) {
            const coreSkills = (updatedMatrix?.categories?.core || [])
              .map((item: any) => item.keyword)
              .filter(Boolean);
            setSelectedResume({
              ...selectedResume,
              skills: coreSkills,
              keywords_matrix: updatedMatrix,
            });
            setEditSkills(coreSkills);
            await fetchResumes();
          }
        }}
      />

      {/* AI Endpoint Config Modal */}
      {showAgentConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-[#11131c] border border-[#24283b] w-full max-w-lg max-h-[90vh] flex flex-col rounded-xl shadow-2xl p-5 space-y-4 my-auto">
            <div className="flex items-center justify-between pb-3 border-b border-[#24283b] shrink-0">
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-[#f3f4f6]">配置自定义 LLM API 端点 (OpenAI 兼容)</h3>
              </div>
              <button
                onClick={() => setShowAgentConfigModal(false)}
                className="text-[#9ca3af] hover:text-[#f3f4f6] text-xs px-2 py-1 rounded"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs overflow-y-auto pr-1">
              <p className="text-[#9ca3af] text-[11px] leading-relaxed">
                无需依赖本地 CLI，JHTracker 支持直接连接任意遵循 OpenAI 规范的本地或云端大模型服务（如本地常驻代理网关、Ollama、OneAPI、DeepSeek、OpenAI 等）。配置保存在本地私有数据库中。
              </p>

              <div className="space-y-1">
                <label className="text-[#9ca3af] font-medium block">
                  Base URL (API 根地址)
                </label>
                <input
                  type="text"
                  placeholder="例如: http://127.0.0.1:8045/v1 或 https://api.deepseek.com/v1"
                  value={customBaseUrl}
                  onChange={(e) => setCustomBaseUrl(e.target.value)}
                  className="w-full p-2 bg-[#0e1017] border border-[#24283b] rounded-lg text-xs font-mono text-[#f3f4f6] focus:outline-none focus:border-emerald-500/60"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#9ca3af] font-medium block">
                  API Key (密钥，本地免鉴权服务可留空)
                </label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={customApiKey}
                  onChange={(e) => setCustomApiKey(e.target.value)}
                  className="w-full p-2 bg-[#0e1017] border border-[#24283b] rounded-lg text-xs font-mono text-[#f3f4f6] focus:outline-none focus:border-emerald-500/60"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#9ca3af] font-medium block">
                  Model (模型名称)
                </label>
                <input
                  type="text"
                  placeholder="例如: claude-3-5-sonnet-20241022 或 deepseek-chat"
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                  className="w-full p-2 bg-[#0e1017] border border-[#24283b] rounded-lg text-xs font-mono text-[#f3f4f6] focus:outline-none focus:border-emerald-500/60"
                />
              </div>

              <div className="p-2.5 bg-emerald-950/20 border border-emerald-500/20 rounded-lg text-[11px] text-emerald-300/90 space-y-1">
                <div className="font-semibold flex items-center gap-1">
                  <span>💡 提示：</span>
                  <span>检测到本机正在运行 OpenAI 兼容网关时，可填入：</span>
                </div>
                <div className="font-mono text-[10px] text-emerald-400 pl-4 space-y-0.5">
                  <div>Base URL: http://127.0.0.1:8045/v1</div>
                  <div>Model: claude-3-5-sonnet-20241022</div>
                </div>
              </div>

              {/* 连通性测试结果状态条 */}
              {testResult && (
                <div
                  className={`p-2.5 rounded-lg text-xs border flex items-start gap-2 ${
                    testResult.success
                      ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                      : 'bg-rose-950/30 border-rose-500/30 text-rose-300'
                  }`}
                >
                  {testResult.success ? (
                    <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  )}
                  <div className="space-y-0.5 overflow-hidden">
                    <div className="font-medium">
                      {testResult.success ? '模型端点探测连通成功' : '模型端点连通失败'}
                    </div>
                    {testResult.success && testResult.latency_ms !== undefined && (
                      <div className="text-[11px] opacity-80 font-mono">
                        响应延迟: {testResult.latency_ms}ms | 模型就绪
                      </div>
                    )}
                    {!testResult.success && testResult.error && (
                      <div className="text-[11px] opacity-90 break-all font-mono">
                        {testResult.error}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between gap-2 pt-3 border-t border-[#24283b] shrink-0">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testingConnection || !customBaseUrl.trim()}
                className="px-3.5 py-1.5 rounded-lg bg-[#1a1e2e] hover:bg-[#24283b] text-indigo-300 hover:text-indigo-200 border border-indigo-500/30 text-xs font-medium transition shadow-sm disabled:opacity-50 flex items-center gap-1.5"
              >
                {testingConnection ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Zap className="h-3.5 w-3.5 text-indigo-400" />
                )}
                <span>{testingConnection ? '正在探测连通性...' : '测试连接'}</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowAgentConfigModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-[#24283b] text-[#9ca3af] hover:text-[#f3f4f6] text-xs transition"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={handleSaveEndpointSettings}
                  disabled={savingSettings || !isTestedAndPassed}
                  title={!isTestedAndPassed ? '请先点击测试连接并通过验证' : '保存此配置'}
                  className={`px-4 py-1.5 rounded-lg text-white text-xs font-medium transition shadow-sm flex items-center gap-1 ${
                    isTestedAndPassed
                      ? 'bg-emerald-600 hover:bg-emerald-500 cursor-pointer'
                      : 'bg-[#1f2430] text-[#6b7280] border border-[#2d3142] cursor-not-allowed opacity-60'
                  }`}
                >
                  {savingSettings && <RefreshCw className="h-3 w-3 animate-spin" />}
                  <span>{isTestedAndPassed ? '保存并更新引擎' : '测试通过后保存'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
