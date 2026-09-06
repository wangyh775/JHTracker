import React, { useMemo, useCallback, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, ColumnResizedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { JobItem } from '../types';
import { CompanyCell, ActionsCell } from './JobTableCells';
import { Sparkles, MapPin, Calendar, ExternalLink, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Building2, Clock, AlertCircle } from 'lucide-react';

interface PinnedJobTableProps {
  jobs: JobItem[];
  loading: boolean;
  total: number;
  currentPage: number;
  pageSize: number;
  visitedSet?: Set<string>;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onApplyClick: (job: JobItem) => void;
  onAddToKanban: (job: JobItem) => void;
  onAiAnalyze?: (job: JobItem) => void;
}

const NATURE_KEYWORDS = [
  '央企研究所', '军工央企', '航天央企', '央企国企', '省属国企', '市属国企', 
  '国企（央企子公司）', '央企', '国企', '外企', '上市公司', '大型民企', 
  '民企', '民营', '事业单位', '合资'
];

const BATCH_KEYWORDS = ['校招', '校园招聘', '秋招', '春招', '实习', '提前批', '届', '直聘', '管培生', '专岗'];
const DIRTY_KEYWORDS = ['街道', '大厦', '园区', '路', '弄', '号', '省', '市', '区', '镇'];

// 预编译关键词正则，将多轮循环 includes 优化为 O(1) ~ O(M) 正则单次匹配
const NATURE_REGEX = new RegExp(NATURE_KEYWORDS.join('|'));
const BATCH_REGEX = new RegExp(BATCH_KEYWORDS.join('|'));
const DIRTY_REGEX = new RegExp(DIRTY_KEYWORDS.join('|'));
const SOE_PREFIX_REGEX = /中国|中铁|中船|中冶|航空工业|国家电网/;

/**
 * 结构化解析职位信息，消除跨列与同格重复：
 * 1. nature (企业性质)：如 央企、国企、外企、上市公司、民企 等
 * 2. industry (行业领域)：如 人工智能、半导体、云计算、移动互联网、金融 等
 * 3. recruitmentTags (招聘标签)：纯招聘批次或技能标签，如 校园招聘、秋招、Python 等
 */
function parseJobAttributes(company: string, rawInd: string | undefined, typeTags: string[] | undefined) {
  const tags: string[] = Array.isArray(typeTags) ? typeTags : [];
  const indTrimmed = rawInd?.trim() || '';

  // 1. 寻找企业性质 (Nature)
  let nature: string | null = null;
  for (const t of tags) {
    if (NATURE_REGEX.test(t)) {
      nature = t;
      break;
    }
  }
  if (!nature && indTrimmed && NATURE_REGEX.test(indTrimmed)) {
    nature = indTrimmed;
  }
  if (!nature && company && SOE_PREFIX_REGEX.test(company)) {
    nature = '央国企';
  }

  // 2. 寻找行业 (Industry)
  let industry: string | null = null;
  // 如果原 ind 存在且不是企业性质，且不是地址杂质
  if (indTrimmed && indTrimmed !== nature && !NATURE_REGEX.test(indTrimmed) && !DIRTY_REGEX.test(indTrimmed)) {
    if (indTrimmed !== '综合') {
      industry = indTrimmed;
    }
  }
  // 若未找到具体行业，从 tags 里寻找纯行业标签（非性质、非批次、非地址）
  if (!industry) {
    for (const t of tags) {
      if (
        t !== nature &&
        !NATURE_REGEX.test(t) &&
        !BATCH_REGEX.test(t) &&
        !DIRTY_REGEX.test(t)
      ) {
        industry = t;
        break;
      }
    }
  }
  if (!industry && indTrimmed === '综合') {
    industry = '综合业务';
  }

  // 3. 提取招聘标签 (Recruitment Tags)
  // 严格剔除性质、行业与地址脏数据，杜绝跨列与同列重复
  const recruitmentTags: string[] = [];
  for (const t of tags) {
    if (t === nature || t === industry) continue;
    if (NATURE_REGEX.test(t)) continue;
    if (industry && t === industry) continue;
    if (DIRTY_REGEX.test(t)) continue;
    recruitmentTags.push(t);
  }

  return { nature, industry, recruitmentTags };
}

export const PinnedJobTable: React.FC<PinnedJobTableProps> = ({
  jobs,
  loading,
  total,
  currentPage,
  pageSize,
  visitedSet,
  onPageChange,
  onPageSizeChange,
  onApplyClick,
  onAddToKanban,
  onAiAnalyze,
}) => {
  // Column definitions with Left-Pinned Columns
  const columnDefs = useMemo<ColDef[]>(() => [
    {
      headerName: '招聘企业',
      field: 'company',
      pinned: 'left',
      width: 170,
      minWidth: 150,
      filter: 'agTextColumnFilter',
      cellRenderer: (params: any) => {
        const job = params.data;
        if (!job) return null;
        const isVisited = visitedSet ? visitedSet.has(job.id) : false;
        return (
          <CompanyCell
            company={job.company}
            popularLevel={job.popular_level}
            isVisited={isVisited}
          />
        );
      },
    },
    {
      headerName: '岗位名称',
      field: 'title',
      pinned: 'left',
      width: 320,
      minWidth: 260,
      filter: 'agTextColumnFilter',
      cellRenderer: (params: any) => {
        const job = params.data;
        if (!job) return null;
        return (
          <div className="flex items-center h-full py-1">
            <span
              className="text-xs font-medium text-gray-200 hover:text-cyan-400 cursor-pointer truncate transition-colors"
              title={job.title}
              onClick={() => onApplyClick(job)}
            >
              {job.title}
            </span>
          </div>
        );
      },
    },
    {
      headerName: '薪资 / 学历要求',
      field: 'salary_range',
      width: 150,
      minWidth: 130,
      cellRenderer: (params: any) => {
        const job = params.data;
        if (!job) return null;
        const hasSalary = Boolean(job.salary_range);
        const hasEdu = Boolean(job.education_req);

        if (!hasSalary && !hasEdu) {
          return <span className="text-gray-500 text-xs">-</span>;
        }

        return (
          <div className="flex items-center gap-1.5 h-full py-1 overflow-hidden">
            {hasSalary && (
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 truncate max-w-[90px]" title={job.salary_range}>
                {job.salary_range}
              </span>
            )}
            {hasEdu && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-gray-300 border border-slate-700 truncate max-w-[65px]" title={job.education_req}>
                {job.education_req}
              </span>
            )}
          </div>
        );
      },
    },
    {
      headerName: '招聘届别',
      field: 'batch',
      width: 110,
      minWidth: 95,
      cellRenderer: (params: any) => {
        const batch = params.value;
        if (!batch) return <span className="text-gray-500 text-xs">-</span>;
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
            {batch}
          </span>
        );
      },
    },
    {
      headerName: '工作地点',
      field: 'location',
      width: 140,
      minWidth: 120,
      cellRenderer: (params: any) => {
        const loc = params.value;
        if (!loc) return <span className="text-gray-500 text-xs">全国/多城市</span>;
        return (
          <div className="flex items-center gap-1 text-xs text-gray-300 truncate" title={loc}>
            <MapPin className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
            <span className="truncate">{loc}</span>
          </div>
        );
      },
    },
    {
      headerName: '发布时间',
      field: 'publish_date',
      width: 110,
      minWidth: 100,
      sort: 'desc',
      cellRenderer: (params: any) => {
        const date = params.value;
        if (!date) return <span className="text-gray-500 text-xs">-</span>;
        return (
          <div className="flex items-center gap-1 text-[11px] font-mono text-gray-400">
            <Calendar className="w-3 h-3 text-gray-500 flex-shrink-0" />
            <span>{date}</span>
          </div>
        );
      },
    },
    {
      headerName: '截止日期',
      field: 'deadline',
      width: 125,
      minWidth: 115,
      cellRenderer: (params: any) => {
        const deadline = params.value;
        if (!deadline) {
          return (
            <span className="text-[11px] text-gray-500 italic">
              招满即止
            </span>
          );
        }

        // 计算距离截止日期的天数 (基于 UTC+8 当天日期)
        const targetDate = new Date(deadline);
        const now = new Date();
        const diffMs = targetDate.setHours(23, 59, 59, 999) - now.getTime();
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

        let badge = null;
        if (diffDays < 0) {
          badge = (
            <span className="text-[10px] px-1 py-0.2 rounded bg-slate-800 text-gray-400 border border-slate-700">
              已截止
            </span>
          );
        } else if (diffDays <= 3) {
          badge = (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-500/40 flex items-center gap-0.5 font-medium animate-pulse">
              <AlertCircle className="w-2.5 h-2.5 text-rose-400 flex-shrink-0" />
              剩{diffDays === 0 ? '今天' : `${diffDays}天`}
            </span>
          );
        } else if (diffDays <= 7) {
          badge = (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-500/40 flex items-center gap-0.5 font-medium">
              <Clock className="w-2.5 h-2.5 text-amber-400 flex-shrink-0" />
              剩{diffDays}天
            </span>
          );
        }

        return (
          <div className="flex items-center gap-1.5 h-full py-1">
            <span className={`text-[11px] font-mono ${diffDays < 0 ? 'text-gray-500 line-through' : 'text-gray-300'}`}>
              {deadline}
            </span>
            {badge}
          </div>
        );
      },
    },
    {
      headerName: '企业性质 / 所属行业',
      field: 'industry',
      width: 170,
      minWidth: 150,
      flex: 1,
      cellRenderer: (params: any) => {
        const job = params.data;
        if (!job) return null;
        const { nature, industry } = parseJobAttributes(job.company, job.industry, job.type_tags);

        if (!nature && !industry) {
          return <span className="text-gray-600 text-xs">-</span>;
        }

        return (
          <div className="flex items-center gap-1.5 h-full py-1 overflow-hidden">
            {/* 企业性质：紫粉色徽章 */}
            {nature && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded bg-purple-950/50 text-purple-300 border border-purple-500/30 truncate max-w-[85px]"
                title={`企业性质: ${nature}`}
              >
                {nature}
              </span>
            )}
            {/* 行业分类：青色微光徽章，且严格不与企业性质重复 */}
            {industry && industry !== nature && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/50 text-cyan-300 border border-cyan-500/30 truncate max-w-[95px]"
                title={`所属行业: ${industry}`}
              >
                {industry}
              </span>
            )}
          </div>
        );
      },
    },
    {
      headerName: '网申操作',
      pinned: 'right',
      width: 180,
      minWidth: 170,
      cellRenderer: (params: any) => {
        const job = params.data;
        if (!job) return null;
        return (
          <ActionsCell
            job={job}
            onApplyClick={onApplyClick}
            onAddToKanban={onAddToKanban}
            onAiAnalyze={onAiAnalyze}
          />
        );
      },
    },
  ], [onApplyClick, onAddToKanban, onAiAnalyze]);

  const defaultColDef = useMemo<ColDef>(() => ({
    sortable: true,
    filter: false,
    resizable: true,
  }), []);

  const saveTimerRef = useRef<any>(null);

  const onGridReady = useCallback((params: GridReadyEvent) => {
    try {
      const savedState = localStorage.getItem('jhtracker_pinned_table_cols');
      if (savedState) {
        const parsed = JSON.parse(savedState);
        if (Array.isArray(parsed) && parsed.length > 0) {
          params.api.applyColumnState({
            state: parsed,
            applyOrder: false,
          });
        }
      }
    } catch (e) {
      console.warn('Failed to restore column state:', e);
    }
  }, []);

  const onColumnResized = useCallback((params: ColumnResizedEvent) => {
    // 仅在用户手动拖拽调整完成时持久化
    if (params.finished && params.api) {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
      saveTimerRef.current = setTimeout(() => {
        try {
          const colState = params.api.getColumnState();
          if (colState && colState.length > 0) {
            localStorage.setItem('jhtracker_pinned_table_cols', JSON.stringify(colState));
          }
        } catch (e) {
          console.warn('Failed to save column state:', e);
        }
      }, 200);
    }
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="w-full flex flex-col rounded-xl overflow-hidden border border-cyber bg-cyber-card shadow-xl">
      {/* Table Sub-header status */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#131520] border-b border-cyber text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
          <span className="text-gray-300 text-xs">
            网申大厅实时同步已就绪
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span className="text-gray-400">
            全库匹配: <strong className="text-cyan-400 font-semibold">{total.toLocaleString()}</strong> 岗位
          </span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">
            本页显示: <strong className="text-cyan-300 font-mono">{jobs.length}</strong> 条
          </span>
        </div>
      </div>

      {/* Grid Container */}
      <div className="ag-theme-alpine-dark ag-theme-custom-dark w-full h-[calc(100vh-270px)] min-h-[740px] bg-[#0e1017]">
        <AgGridReact
          rowData={jobs}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          animateRows={false}
          rowSelection="single"
          loading={loading}
          onGridReady={onGridReady}
          onColumnResized={onColumnResized}
          headerHeight={38}
          rowHeight={44}
          suppressCellFocus={true}
          enableCellTextSelection={true}
          overlayLoadingTemplate='<div class="p-4 rounded-lg bg-[#111320] border border-[#1e2235] text-cyan-400 font-medium text-xs shadow-xl flex items-center gap-2"><span>正在实时加载全网校招岗位数据...</span></div>'
          overlayNoRowsTemplate='<div class="p-4 rounded-lg bg-[#111320] border border-[#1e2235] text-gray-400 text-xs shadow-xl">暂无符合当前筛选条件的岗位</div>'
        />
      </div>

      {/* Pagination Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#11131c] border-t border-cyber text-xs text-gray-400 select-none">
        <div className="flex items-center gap-2">
          <span>每页显示:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="bg-[#181a26] border border-cyber text-gray-200 rounded px-2.5 py-1 outline-none focus:border-cyan-500 cursor-pointer font-medium"
          >
            <option value={50}>50 条</option>
            <option value={100}>100 条 (推荐)</option>
            <option value={200}>200 条</option>
            <option value={500}>500 条</option>
          </select>
          <span className="text-gray-500 ml-2">
            第 {((currentPage - 1) * pageSize) + (total > 0 ? 1 : 0)} - {Math.min(currentPage * pageSize, total)} 条 (共 {total} 条)
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage <= 1 || loading}
            title="第一页"
            className="p-1.5 rounded border border-cyber hover:bg-cyan-500/15 hover:text-cyan-300 hover:border-cyan-500/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-gray-400 transition-colors"
          >
            <ChevronsLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1 || loading}
            title="上一页"
            className="p-1.5 rounded border border-cyber hover:bg-cyan-500/15 hover:text-cyan-300 hover:border-cyan-500/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-gray-400 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="px-3 py-1 font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-500/30 rounded">
            {currentPage} / {totalPages}
          </span>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages || loading}
            title="下一页"
            className="p-1.5 rounded border border-cyber hover:bg-cyan-500/15 hover:text-cyan-300 hover:border-cyan-500/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-gray-400 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage >= totalPages || loading}
            title="最后一页"
            className="p-1.5 rounded border border-cyber hover:bg-cyan-500/15 hover:text-cyan-300 hover:border-cyan-500/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-gray-400 transition-colors"
          >
            <ChevronsRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
