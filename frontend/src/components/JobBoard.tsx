import React, { useState, useEffect, useMemo } from 'react';
import { JobItem, FangzhouCategory } from '../types';
import { PinnedJobTable } from './PinnedJobTable';
import { FangzhouTableHeader } from './FangzhouTableHeader';
import { FilterPillsBar } from './FilterPillsBar';
import { FloatingStatsCard } from './FloatingStatsCard';
import { SplineHeader } from './SplineHeader';
import { useVisitedJobs } from '../services/visitedStorage';
import { api } from '../config';
import { AlertCircle, CheckCircle } from 'lucide-react';

interface JobBoardProps {
  onNavigateToKanban?: () => void;
  onSelectJobForAi?: (job: JobItem) => void;
}

export const JobBoard: React.FC<JobBoardProps> = ({
  onNavigateToKanban,
  onSelectJobForAi,
}) => {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' | 'warning' } | null>(null);

  // Filter states
  const [category, setCategory] = useState<FangzhouCategory>('all');
  const [keyword, setKeyword] = useState('');
  const [selectedCity, setSelectedCity] = useState('全部');
  const [selectedBatch, setSelectedBatch] = useState('全部');
  const [hasReferralOnly, setHasReferralOnly] = useState(false);
  const [hideVisited, setHideVisited] = useState(false);

  // Pagination states
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);

  // Spider sync state
  const [spiderRunning, setSpiderRunning] = useState(false);
  const [syncDays, setSyncDays] = useState(30);
  const [selectedSources, setSelectedSources] = useState<string[]>(['fangzhou', 'wondercv']);

  // Stats
  const [stats, setStats] = useState<{ total_jobs: number; total_companies: number } | null>(null);

  // Visited state
  const { visitedSet, markVisited } = useVisitedJobs();

  const showNotification = (text: string, type: 'success' | 'error' | 'warning' = 'success') => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Fetch stats once on mount
  const fetchStats = async () => {
    try {
      const res = await api.get('/api/jobs/stats');
      if (res.data && res.data.total_jobs) {
        setStats({
          total_jobs: res.data.total_jobs,
          total_companies: res.data.total_companies || 3180
        });
      }
    } catch (e) {
      console.warn('Failed to load job stats', e);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  // Fetch jobs from backend
  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {
        limit: pageSize,
        offset: (currentPage - 1) * pageSize
      };
      if (category !== 'all') {
        params.category = category;
      }
      if (selectedCity !== '全部') {
        params.city = selectedCity;
      }
      if (selectedBatch !== '全部') {
        params.batch = selectedBatch.replace('届', '');
      }
      if (hasReferralOnly) {
        params.has_referral = true;
      }
      if (keyword.trim()) {
        params.keyword = keyword.trim();
      }

      const res = await api.get('/api/jobs', { params });
      if (res.data && Array.isArray(res.data.items)) {
        setJobs(res.data.items);
        setTotal(res.data.total || 0);
      } else {
        setJobs([]);
        setTotal(0);
      }
    } catch (err: any) {
      console.error('Failed to load jobs', err);
      setError('无法连接后端服务或获取招聘数据，请检查网络或后端是否启动');
    } finally {
      setLoading(false);
    }
  };

  // Reset to page 1 when primary filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [category, selectedCity, selectedBatch, hasReferralOnly, keyword]);

  // Trigger fetch on filter or pagination changes
  useEffect(() => {
    fetchJobs();
  }, [category, selectedCity, selectedBatch, hasReferralOnly, keyword, currentPage, pageSize]);

  // Client-side filtering for visited jobs
  const displayedJobs = useMemo(() => {
    if (!hideVisited) return jobs;
    return jobs.filter((job) => !visitedSet.has(job.id));
  }, [jobs, hideVisited, visitedSet]);

  // Handle Apply button click
  const handleApplyClick = (job: JobItem) => {
    markVisited(job.id);
    const targetUrl = job.apply_url || job.detail_url;
    if (targetUrl) {
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
    } else {
      showNotification(`已记录网申足迹: ${job.company} - ${job.title}`);
    }
  };

  // Add Job to Kanban Pipeline
  const handleAddToKanban = async (job: JobItem) => {
    try {
      await api.post('/api/applications', {
        job_id: job.id,
        status: 'PENDING_APPLY',
        company: job.company,
        job_title: job.title,
        notes: `从校招网申大厅同步 (内推码: ${job.referral_code || '无'})`
      });
      showNotification(`已同步【${job.company} - ${job.title}】到投递追踪看板！`);
      if (onNavigateToKanban) {
        // Optional quick link or toast
      }
    } catch (err: any) {
      console.error('Failed to add to kanban', err);
      showNotification('同步到看板失败，请重试', 'error');
    }
  };

  // Sync spider with multiple sources and time-window constraint
  const handleSyncSpider = async () => {
    if (selectedSources.length === 0) {
      showNotification('请至少选择一个抓取途径！', 'error');
      return;
    }
    setSpiderRunning(true);
    try {
      const res = await api.post(
        '/api/spiders/batch-sync',
        {
          sources: selectedSources,
          days: syncDays,
          pages: 2,
        },
        {
          timeout: 120000, // 抓取全网数据耗时较长，增加超时至 2 分钟
        }
      );
      const data = res.data;
      if (!data.success && data.message) {
        showNotification(data.message, 'warning');
        return;
      }
      const totalSaved = data.total_saved ?? 0;
      const details = data.details || {};
      const successList = Object.values(details)
        .filter((d: any) => d.success)
        .map((d: any) => `${d.name}: +${d.saved || 0}`);
      const failedList = Object.values(details)
        .filter((d: any) => !d.success)
        .map((d: any) => `${d.name}: 失败`);

      let summary = `同步完成！新增/更新入库 ${totalSaved} 个岗位`;
      if (successList.length > 0) {
        summary += ` (${successList.join(', ')})`;
      }
      if (failedList.length > 0) {
        summary += ` [跳过: ${failedList.join(', ')}]`;
      }

      showNotification(summary, failedList.length > 0 ? 'warning' : 'success');
      await fetchJobs();
      await fetchStats();
    } catch (err: any) {
      console.error('Spider trigger failed', err);
      showNotification('同步全网数据失败，可检查后端日志', 'error');
    } finally {
      setSpiderRunning(false);
    }
  };

  const handleResetFilters = () => {
    setSelectedCity('全部');
    setSelectedBatch('全部');
    setKeyword('');
    setHasReferralOnly(false);
  };

  return (
    <div className="space-y-2.5">
      {/* 3D Spline Tech Header */}
      <SplineHeader
        totalJobs={stats?.total_jobs || total || 23231}
        totalCompanies={stats?.total_companies || 3182}
      />

      {/* Toast Notification */}
      {notification && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-900 border border-cyan-500/50 shadow-2xl text-xs text-cyan-300 animate-bounce">
          {notification.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          )}
          <span>{notification.text}</span>
        </div>
      )}

      {/* Table Header Controls */}
      <FangzhouTableHeader
        activeCategory={category}
        onSelectCategory={setCategory}
        keyword={keyword}
        onKeywordChange={setKeyword}
        hasReferralOnly={hasReferralOnly}
        onToggleReferralOnly={() => setHasReferralOnly(!hasReferralOnly)}
        hideVisited={hideVisited}
        onToggleHideVisited={() => setHideVisited(!hideVisited)}
        visitedCount={visitedSet.size}
      />

      {/* Secondary Filter Pills */}
      <FilterPillsBar
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
        selectedBatch={selectedBatch}
        onSelectBatch={setSelectedBatch}
        onReset={handleResetFilters}
      />

      {/* Error Alert */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-950/30 border border-red-500/40 rounded-lg text-xs text-red-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Pinned Cyber Table */}
      <PinnedJobTable
        jobs={displayedJobs}
        loading={loading}
        total={total}
        currentPage={currentPage}
        pageSize={pageSize}
        visitedSet={visitedSet}
        onPageChange={setCurrentPage}
        onPageSizeChange={(newSize) => {
          setPageSize(newSize);
          setCurrentPage(1);
        }}
        onApplyClick={handleApplyClick}
        onAddToKanban={handleAddToKanban}
        onAiAnalyze={onSelectJobForAi}
      />

      {/* Floating Engine / Stats Card */}
      <FloatingStatsCard
        totalJobs={stats?.total_jobs || total || jobs.length}
        visitedCount={visitedSet.size}
        syncDays={syncDays}
        onSyncDaysChange={setSyncDays}
        selectedSources={selectedSources}
        onSelectedSourcesChange={setSelectedSources}
        onSyncSpider={handleSyncSpider}
        spiderRunning={spiderRunning}
      />
    </div>
  );
};
