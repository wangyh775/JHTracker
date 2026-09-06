import React, { useState, useEffect } from 'react';
import { api } from '../config';
import { ResumeItem, JobItem, ParseResumeResponse } from '../types';
import { ResumeImportModal } from './ResumeImportModal';
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
  ArrowRight
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

  // Editable fields in workbench
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editCategory, setEditCategory] = useState<'GENERAL' | 'CUSTOMIZED'>('GENERAL');
  const [editSkills, setEditSkills] = useState<string[]>([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [viewMode, setViewMode] = useState<'split' | 'edit' | 'preview'>('split');
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);

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

  useEffect(() => {
    fetchResumes();
    fetchRecentJobs();
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
    setJobPickerOpen(false);
    showNotification(`已关联目标岗位: ${job.company} - ${job.title}`);
  };

  const handleOptimize = async () => {
    if (!selectedResume || !selectedResume.id) {
      showNotification('请先保存当前简历后再进行专岗优化');
      return;
    }
    setOptimizing(true);
    try {
      const res = await api.post('/api/resumes/optimize', {
        resume_id: selectedResume.id,
        job_id: jobId || undefined,
        resume_content_md: editContent || undefined,
        mode: jobId ? 'CUSTOMIZED' : 'GENERAL',
        save_as_version: false,
      });
      setOptResult(res.data);
      showNotification('专岗 ATS 诊断分析完成！');
      // 如果后端自动生成了独立优化版，刷新列表
      if (res.data?.optimized_resume_id) {
        await fetchResumes();
      }
    } catch (err) {
      console.error('Optimize failed', err);
      showNotification('专岗优化分析失败，请检查网络或目标岗位 ID');
    } finally {
      setOptimizing(false);
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

  // Render markdown text with highlighted skills
  const renderHighlightedContent = () => {
    if (!editContent) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-[#6b7280] italic p-8 text-xs text-center">
          <FileText className="h-8 w-8 text-[#374151] mb-2" />
          暂无简历 Markdown 内容，可在左侧输入、粘贴或一键导入本地简历
        </div>
      );
    }

    const lines = editContent.split('\n');
    return (
      <div className="space-y-1 font-mono text-xs text-[#d1d5db] leading-relaxed select-text p-1">
        {lines.map((line, idx) => {
          if (line.startsWith('# ')) {
            return (
              <h1 key={idx} className="text-base font-bold text-cyan-400 border-b border-cyan-500/30 pb-1 mt-2">
                {line.replace('# ', '')}
              </h1>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h2 key={idx} className="text-sm font-bold text-[#f3f4f6] border-b border-[#24283b] pb-1 mt-3">
                {line.replace('## ', '')}
              </h2>
            );
          }
          if (line.startsWith('### ')) {
            return (
              <h3 key={idx} className="text-xs font-bold text-cyan-300 mt-2">
                {line.replace('### ', '')}
              </h3>
            );
          }

          // Highlight skills in regular text
          let renderedLine: React.ReactNode = line;
          if (editSkills.length > 0) {
            const escapedSkills = editSkills
              .filter(Boolean)
              .map((s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'));
            if (escapedSkills.length > 0) {
              const regex = new RegExp(`(${escapedSkills.join('|')})`, 'gi');
              const parts = line.split(regex);
              renderedLine = parts.map((part, pIdx) =>
                editSkills.some((s) => s.toLowerCase() === part.toLowerCase()) ? (
                  <span
                    key={pIdx}
                    className="bg-cyan-950/80 text-cyan-300 px-1 rounded border border-cyan-500/40 font-semibold shadow-sm"
                  >
                    {part}
                  </span>
                ) : (
                  part
                )
              );
            }
          }

          return (
            <p key={idx} className="text-[#9ca3af] min-h-[1.2em]">
              {renderedLine}
            </p>
          );
        })}
      </div>
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
                      <div className="font-bold text-[#f3f4f6] truncate text-[11px]">{r.title}</div>
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

          {/* 技能画像标签管理条 */}
          <div className="bg-[#11131c] px-3 py-2 rounded-xl border border-[#24283b] flex flex-wrap items-center gap-1.5 shadow-sm">
            <span className="text-[11px] font-bold text-[#d1d5db] flex items-center gap-1 mr-1">
              <Sparkles className="h-3 w-3 text-cyan-400" />
              画像技能 ({editSkills.length}):
            </span>
            <div className="flex flex-wrap gap-1 items-center max-h-16 overflow-y-auto pr-1">
              {editSkills.map((s, idx) => (
                <span
                  key={idx}
                  className="bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.2 rounded text-[10px] font-mono flex items-center gap-1"
                >
                  {s}
                  <button
                    onClick={() => handleRemoveSkill(s)}
                    className="hover:text-rose-400 text-[#9ca3af] font-bold"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-1 ml-auto">
              <input
                type="text"
                placeholder="添加技能标签..."
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                className="bg-[#151824] border border-[#24283b] text-xs text-[#f3f4f6] px-2 py-0.5 rounded outline-none focus:border-cyan-500 w-28"
              />
              <button
                onClick={handleAddSkill}
                className="px-2 py-0.5 bg-cyan-600/30 text-cyan-300 hover:bg-cyan-600/50 rounded text-xs font-bold transition"
              >
                +
              </button>
            </div>
          </div>

          {/* Markdown 源码与高亮渲染双栏自适应面板 */}
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
        </div>

        {/* 右侧常驻 ATS 专岗诊断与调优面板 (占 3 列) */}
        <div className="col-span-12 xl:col-span-3 bg-[#11131c] p-3.5 rounded-xl border border-[#24283b] space-y-3 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-[#24283b]">
            <div className="flex items-center gap-1.5">
              <Wand2 className="h-4 w-4 text-cyan-400" />
              <span className="font-bold text-xs text-[#f3f4f6]">专岗 ATS 诊断调优</span>
            </div>
            <span className="text-[10px] text-cyan-400 bg-cyan-950/60 px-1.5 py-0.2 rounded border border-cyan-500/30 font-mono">
              智能对齐
            </span>
          </div>

          {/* 目标岗位快捷选定模块 */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-[#9ca3af]">
              <span>目标对齐岗位:</span>
              <button
                onClick={() => setJobPickerOpen(!jobPickerOpen)}
                className="text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 text-[10px]"
              >
                <Search className="h-2.5 w-2.5" />
                {jobPickerOpen ? '收起库' : '从岗位库选岗'}
              </button>
            </div>

            {selectedJob ? (
              <div className="p-2 bg-[#151824] border border-cyan-500/40 rounded-lg text-xs space-y-1 relative">
                <button
                  onClick={() => {
                    setSelectedJob(null);
                    setJobId('');
                  }}
                  className="absolute top-1.5 right-1.5 text-[#6b7280] hover:text-rose-400"
                  title="清除选择"
                >
                  <X className="h-3 w-3" />
                </button>
                <div className="font-bold text-[#f3f4f6] truncate pr-4">{selectedJob.title}</div>
                <div className="text-[11px] text-cyan-300">{selectedJob.company}</div>
                <div className="flex items-center gap-2 text-[10px] text-[#9ca3af]">
                  <span>{selectedJob.city || '全国'}</span>
                  {selectedJob.salary_range && <span>· {selectedJob.salary_range}</span>}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  placeholder="输入目标岗位 ID 或在此粘贴..."
                  value={jobId}
                  onChange={(e) => {
                    setJobId(e.target.value);
                    setSelectedJob(null);
                  }}
                  className="w-full px-2.5 py-1.5 bg-[#151824] border border-[#24283b] rounded-lg text-xs text-[#f3f4f6] outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            )}

            {/* 下拉/展开式岗位选择器 */}
            {jobPickerOpen && (
              <div className="p-2 bg-[#0e1017] border border-[#24283b] rounded-lg space-y-2 mt-1 animate-fadeIn">
                <div className="relative">
                  <Search className="h-3 w-3 text-[#6b7280] absolute left-2 top-2" />
                  <input
                    type="text"
                    placeholder="按职位名、公司或城市筛选..."
                    value={jobSearchText}
                    onChange={(e) => setJobSearchText(e.target.value)}
                    className="w-full pl-6 pr-2 py-1 bg-[#151824] border border-[#24283b] rounded text-[11px] text-[#f3f4f6] outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="max-h-44 overflow-y-auto space-y-1 custom-scrollbar pr-0.5">
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

          {/* 启动诊断按钮 */}
          <button
            onClick={handleOptimize}
            disabled={!selectedResume || optimizing}
            className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg text-xs shadow-md shadow-cyan-950/40 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            {optimizing ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>ATS 深度诊断中...</span>
              </>
            ) : (
              <>
                <Wand2 className="h-3.5 w-3.5" />
                <span>{jobId ? '针对所选岗位 ATS 诊断' : '通用 STAR 法则润色诊断'}</span>
              </>
            )}
          </button>

          {/* 诊断报告结果展示卡片 */}
          {optResult ? (
            <div className="space-y-2.5 pt-1 border-t border-[#24283b]/60">
              {/* ATS 分数与评级 */}
              <div className="p-2.5 bg-[#151824] border border-cyan-500/30 rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-[#9ca3af]">ATS 关键词契合指数</div>
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
                  <span className="text-[10px] text-rose-400 font-bold flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> 建议补齐的缺失词 ({optResult.missing_keywords.length})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {optResult.missing_keywords.map((k: string, i: number) => (
                      <span
                        key={i}
                        className="bg-rose-950/60 text-rose-300 border border-rose-500/30 px-1.5 py-0.2 rounded text-[10px] font-mono"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 核心建议列表 */}
              {optResult.suggestions && (
                <div className="space-y-1">
                  <span className="text-[10px] text-cyan-300 font-bold">修改建议:</span>
                  <ul className="text-[11px] text-[#d1d5db] space-y-1 list-disc list-inside bg-[#0e1017] p-2 rounded border border-[#24283b] leading-relaxed">
                    {optResult.suggestions.map((s: string, idx: number) => (
                      <li key={idx} className="text-[#9ca3af]">
                        <span className="text-[#e5e7eb]">{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 采纳 AI 优化结果至编辑器 */}
              {optResult.optimized_markdown && (
                <button
                  onClick={handleApplyAIToEditor}
                  className="w-full py-1.5 bg-[#151824] hover:bg-[#1b1e2e] text-cyan-300 text-xs font-semibold rounded-lg border border-cyan-500/40 transition flex items-center justify-center gap-1"
                >
                  <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
                  <span>采纳专岗建议至编辑器</span>
                </button>
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
    </div>
  );
};
