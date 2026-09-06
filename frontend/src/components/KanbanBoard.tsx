import React, { useState, useEffect, useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  useDroppable,
} from '@dnd-kit/core';
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { api } from '../config';
import { ApplicationItem, ApplicationStatus } from '../types';
import {
  Clock,
  Send,
  FileCheck,
  Users,
  Award,
  Building2,
  Calendar,
  Sparkles,
  GripVertical,
  ChevronLeft,
  ChevronRight,
  ChevronsLeftRight,
  ChevronsRightLeft,
  ArrowRight,
  TrendingUp,
  MapPin,
  ExternalLink,
  Layers,
  Briefcase,
  GraduationCap,
  ChevronDown,
  ChevronUp,
  Archive,
  ArchiveRestore,
  Trash2,
  Inbox,
  AlertTriangle,
} from 'lucide-react';

export const STAGES: {
  id: ApplicationStatus;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  badge: string;
  border: string;
  bg: string;
}[] = [
  {
    id: 'PENDING_APPLY',
    label: '待投递',
    shortLabel: '待投',
    icon: Clock,
    color: 'text-amber-400',
    badge: 'bg-amber-950/60 text-amber-400 border-amber-500/40',
    border: 'border-amber-500/20 hover:border-amber-500/40',
    bg: 'bg-amber-950/10',
  },
  {
    id: 'APPLIED',
    label: '已投递',
    shortLabel: '已投',
    icon: Send,
    color: 'text-blue-400',
    badge: 'bg-blue-950/60 text-blue-400 border-blue-500/40',
    border: 'border-blue-500/20 hover:border-blue-500/40',
    bg: 'bg-blue-950/10',
  },
  {
    id: 'OA_SCREENING',
    label: '笔试 / 测评',
    shortLabel: '笔试',
    icon: FileCheck,
    color: 'text-purple-400',
    badge: 'bg-purple-950/60 text-purple-400 border-purple-500/40',
    border: 'border-purple-500/20 hover:border-purple-500/40',
    bg: 'bg-purple-950/10',
  },
  {
    id: 'INTERVIEW_STAGE',
    label: '面试进行中',
    shortLabel: '面试',
    icon: Users,
    color: 'text-cyan-400',
    badge: 'bg-cyan-950/60 text-cyan-400 border-cyan-500/40',
    border: 'border-cyan-500/20 hover:border-cyan-500/40',
    bg: 'bg-cyan-950/10',
  },
  {
    id: 'OFFER_RECEIVED',
    label: '斩获 Offer',
    shortLabel: 'Offer',
    icon: Award,
    color: 'text-emerald-400',
    badge: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40',
    border: 'border-emerald-500/30 hover:border-emerald-500/60',
    bg: 'bg-emerald-950/15',
  },
];

// Helper to determine next status
const getNextStage = (current: ApplicationStatus): ApplicationStatus | null => {
  const order: ApplicationStatus[] = [
    'PENDING_APPLY',
    'APPLIED',
    'OA_SCREENING',
    'INTERVIEW_STAGE',
    'OFFER_RECEIVED',
  ];
  const idx = order.indexOf(current);
  if (idx !== -1 && idx < order.length - 1) {
    return order[idx + 1];
  }
  return null;
};

// Draggable Kanban Card Component
interface KanbanCardProps {
  app: ApplicationItem;
  isOverlay?: boolean;
  onAdvanceStage?: (appId: string, nextStatus: ApplicationStatus) => void;
  onArchive?: (appId: string, isArchived: boolean) => void;
  onDelete?: (appId: string) => void;
}

const KanbanCardInner: React.FC<KanbanCardProps> = ({
  app,
  isOverlay = false,
  onAdvanceStage,
  onArchive,
  onDelete,
}) => {
  const [expanded, setExpanded] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: app.id, data: { app } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.25 : 1,
  };

  const nextStage = getNextStage(app.status);
  const nextStageObj = nextStage ? STAGES.find((s) => s.id === nextStage) : null;
  const currentStageMeta = STAGES.find((s) => s.id === app.status) || STAGES[0];
  const CurrentIcon = currentStageMeta.icon;
  const targetApplyUrl = app.apply_url || app.detail_url;

  return (
    <div
      ref={setNodeRef}
      style={style}
      data-expanded={expanded ? 'true' : 'false'}
      className={`group relative rounded-lg border p-2.5 transition-all select-none kanban-card-optimized ${
        isOverlay
          ? 'bg-[#1a1d2e] border-cyan-500/80 shadow-xl ring-1 ring-cyan-500/40 scale-102 z-50 cursor-grabbing'
          : 'bg-[#131622] border-[#222738] hover:border-cyan-500/50 hover:bg-[#181b2a] shadow-sm'
      }`}
    >
      {/* 1. 核心首行：岗位名称（大字号最醒目） + 右上角操作区 */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0 flex-1">
          <h4
            className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors leading-snug line-clamp-2"
            title={app.title}
          >
            {app.title}
          </h4>
        </div>

        {/* 右上角操作组 */}
        <div className="flex items-center gap-1 flex-shrink-0 pt-0.5">
          {/* 直达网申按钮 */}
          {!isOverlay && (
            <a
              href={
                targetApplyUrl ||
                `https://www.baidu.com/s?wd=${encodeURIComponent(`${app.company} ${app.title} 校园招聘 网申`)}`
              }
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-500/40 hover:border-cyan-300 text-cyan-300 hover:text-white text-xs font-medium transition-colors flex items-center gap-1"
              title={targetApplyUrl ? '直达官方网申投递页面' : '在浏览器搜索该岗位网申入口'}
            >
              <ExternalLink className="w-3 h-3" />
              <span>网申</span>
            </a>
          )}

          {/* 归档 / 取消归档按钮 */}
          {!isOverlay && onArchive && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onArchive(app.id, !app.is_archived);
              }}
              className={`p-1 rounded transition-colors ${
                app.is_archived
                  ? 'text-amber-400 hover:text-amber-300 hover:bg-amber-950/40'
                  : 'text-[#64748b] hover:text-amber-400 hover:bg-[#1f2438]'
              }`}
              title={app.is_archived ? '从归档箱恢复至看板' : '归档此卡片（保留记录且防打扰）'}
            >
              {app.is_archived ? <ArchiveRestore className="w-3.5 h-3.5" /> : <Archive className="w-3.5 h-3.5" />}
            </button>
          )}

          {/* 彻底删除按钮 */}
          {!isOverlay && onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(app.id);
              }}
              className="p-1 rounded text-[#64748b] hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              title="彻底删除此投递记录"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          <div
            {...attributes}
            {...listeners}
            className="text-[#64748b] hover:text-[#cbd5e1] p-1 rounded cursor-grab active:cursor-grabbing transition-colors"
            title="按住拖拽移动卡片"
          >
            <GripVertical className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>

      {/* 2. 企业名称行 + AI 匹配度 + 薪资（主视觉次要层级，清晰醒目） */}
      <div className="flex items-center justify-between gap-1.5 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <Building2 className="w-3.5 h-3.5 text-cyan-400/90 flex-shrink-0" />
          <span className="text-xs font-semibold text-slate-200 truncate" title={app.company}>
            {app.company}
          </span>

          {/* AI 匹配分胶囊 */}
          {app.match_score !== undefined && app.match_score !== null && (
            <span
              className={`text-[11px] px-1.5 py-0.5 rounded font-mono font-semibold flex-shrink-0 flex items-center gap-0.5 ${
                app.match_score >= 0.85
                  ? 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-300'
                  : app.match_score >= 0.7
                  ? 'bg-cyan-950/80 border border-cyan-500/40 text-cyan-300'
                  : 'bg-indigo-950/80 border border-indigo-500/40 text-indigo-300'
              }`}
              title={`AI 智能匹配度评分: ${Math.round(app.match_score * 100)}%`}
            >
              <Sparkles className="w-3 h-3" />
              {Math.round(app.match_score * 100)}%
            </span>
          )}
        </div>

        {/* 薪资醒目展示（放在企业行右侧，空间零浪费） */}
        {app.salary_range && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-500/40 text-amber-300 font-mono font-semibold flex-shrink-0">
            {app.salary_range}
          </span>
        )}
      </div>

      {/* 3. AI 推荐理由提示（有则紧凑展示） */}
      {app.recommend_reason && (
        <div className="mb-1.5 px-2 py-0.5 rounded bg-indigo-950/50 border border-indigo-500/25 text-[11px] text-indigo-200 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-cyan-400 flex-shrink-0" />
          <span className="truncate" title={app.recommend_reason}>
            {app.recommend_reason}
          </span>
        </div>
      )}

      {/* 4. 关键标签/属性流式紧凑矩阵（地点、行业、学历、届数、技能标签融汇排列） */}
      <div className="flex flex-wrap items-center gap-1 mb-1.5">
        {/* 工作地点 */}
        <span className="inline-flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded bg-[#181c2b] border border-[#2b3348] text-slate-200">
          <MapPin className="w-3 h-3 text-cyan-400 flex-shrink-0" />
          <span>{app.location || '全国/待定'}</span>
        </span>

        {/* 企业性质/行业 */}
        <span className="inline-flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded bg-[#181c2b] border border-[#2b3348] text-slate-200">
          <Briefcase className="w-3 h-3 text-blue-400 flex-shrink-0" />
          <span>{app.industry || '综合科技'}</span>
        </span>

        {/* 学历要求 */}
        {app.education_req && (
          <span className="inline-flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded bg-[#181c2b] border border-[#2b3348] text-slate-300">
            <GraduationCap className="w-3 h-3 text-purple-400 flex-shrink-0" />
            <span>{app.education_req}</span>
          </span>
        )}

        {/* 招聘届数 */}
        {app.batch && (
          <span className="inline-flex items-center text-[11px] px-1.5 py-0.5 rounded bg-[#181c2b] border border-[#2b3348] text-slate-400">
            <span>{app.batch}</span>
          </span>
        )}

        {/* 岗位技能标签（前 2 个标签直出，溢出 +N） */}
        {app.type_tags && app.type_tags.slice(0, 2).map((tag, idx) => (
          <span
            key={idx}
            className="text-[11px] px-1.5 py-0.5 rounded bg-[#121524] border border-[#22293e] text-slate-400 font-mono"
          >
            #{tag}
          </span>
        ))}
        {app.type_tags && app.type_tags.length > 2 && (
          <span className="text-[11px] text-slate-500 font-mono">+{app.type_tags.length - 2}</span>
        )}
      </div>


      {/* 6. 面试日程提醒条 */}
      {app.interview_time && (
        <div className="mb-1.5 flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-xs text-cyan-300 font-mono">
          <Calendar className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          <span className="truncate">面试: {app.interview_time.replace('T', ' ')}</span>
        </div>
      )}

      {/* 7. 卡片内就地展开/收起详情面板 */}
      {expanded && (
        <div className="mt-1.5 mb-1.5 pt-1.5 border-t border-[#22283a] space-y-1.5 text-xs">
          {app.description && (
            <div>
              <span className="text-[11px] text-slate-400 font-medium block mb-0.5">岗位详细要求 (JD)：</span>
              <div className="p-2 rounded bg-[#0e101a] border border-[#202638] text-slate-200 text-xs leading-relaxed max-h-36 overflow-y-auto custom-scrollbar whitespace-pre-wrap font-mono select-text">
                {app.description}
              </div>
            </div>
          )}
          {app.notes && (
            <div>
              <span className="text-[11px] text-amber-400 font-medium block mb-0.5">备忘记录：</span>
              <div className="p-1.5 rounded bg-amber-950/30 border border-amber-500/30 text-amber-200 text-xs select-text">
                {app.notes}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 8. Footer: 状态徽章 + 投递渠道/时间 + 展开切换 + 快速流转 */}
      <div className="flex items-center justify-between text-xs text-[#94a3b8] font-mono pt-1.5 border-t border-[#1f2434]">
        <div className="flex items-center gap-1.5">
          {/* 当前阶段状态徽章 (随流转动态变更) */}
          <span className={`px-1.5 py-0.5 rounded border text-[11px] font-sans font-medium flex items-center gap-1 ${currentStageMeta.badge}`}>
            <CurrentIcon className={`w-3 h-3 ${currentStageMeta.color}`} />
            <span>{currentStageMeta.shortLabel}</span>
          </span>

          {/* 投递时间或渠道 */}
          <div className="flex items-center gap-0.5 text-slate-400 text-[11px]">
            <Calendar className="w-3 h-3 text-[#64748b]" />
            <span>{app.apply_date || (app.applied_at ? app.applied_at.split('T')[0] : (app.status === 'PENDING_APPLY' ? '待投' : '已记录'))}</span>
          </div>
          {app.channel && (
            <span className="text-slate-300 bg-[#1a1f2e] px-1.5 py-0.5 rounded border border-[#2b3348] text-[10px]">
              {app.channel}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {/* 就地展开/折叠按钮 */}
          {(app.description || app.notes) && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
              className="text-[#94a3b8] hover:text-cyan-300 transition-colors flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded hover:bg-[#1f253a]"
            >
              <span>{expanded ? '收起' : '详情'}</span>
              {expanded ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>
          )}

          {/* 一键推进至下一阶段 */}
          {!isOverlay && nextStageObj && onAdvanceStage && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAdvanceStage(app.id, nextStageObj.id);
              }}
              title={`一键推进至「${nextStageObj.label}」`}
              className="opacity-90 group-hover:opacity-100 transition-opacity flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/90 hover:bg-cyan-900 border border-cyan-500/40 hover:border-cyan-400 text-xs text-cyan-300 font-sans font-medium"
            >
              <span>{nextStageObj.shortLabel}</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const KanbanCard = React.memo(KanbanCardInner);

// Droppable Kanban Column (Expanded or Collapsed)
interface KanbanColumnProps {
  stage: (typeof STAGES)[0];
  apps: ApplicationItem[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onAdvanceStage: (appId: string, nextStatus: ApplicationStatus) => void;
  onArchive?: (appId: string, isArchived: boolean) => void;
  onDelete?: (appId: string) => void;
}

const KanbanColumn: React.FC<KanbanColumnProps> = ({
  stage,
  apps,
  isCollapsed,
  onToggleCollapse,
  onAdvanceStage,
  onArchive,
  onDelete,
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: stage.id,
  });

  const Icon = stage.icon;

  // Exact Window Virtualization (renders OVERSCAN + visible + OVERSCAN items with physical spacer)
  const CARD_HEIGHT = 115; // average height per card after layout optimization
  const OVERSCAN = 3; // 3 cards buffer above and below viewport for butter-smooth scrolling without blanks
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(600);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      setViewportHeight(scrollRef.current.clientHeight || 600);
    }
  }, []);

  const totalCount = apps.length;
  const totalHeight = totalCount * CARD_HEIGHT;

  const { startIndex, endIndex, topSpacerHeight, bottomSpacerHeight, virtualApps } = useMemo(() => {
    if (totalCount === 0) {
      return {
        startIndex: 0,
        endIndex: 0,
        topSpacerHeight: 0,
        bottomSpacerHeight: 0,
        virtualApps: [],
      };
    }

    const calculatedStart = Math.floor(scrollTop / CARD_HEIGHT);
    const visibleCount = Math.ceil(viewportHeight / CARD_HEIGHT);

    const start = Math.max(0, calculatedStart - OVERSCAN);
    const end = Math.min(totalCount, calculatedStart + visibleCount + OVERSCAN);

    const topSpacer = start * CARD_HEIGHT;
    const bottomSpacer = Math.max(0, (totalCount - end) * CARD_HEIGHT);

    return {
      startIndex: start,
      endIndex: end,
      topSpacerHeight: topSpacer,
      bottomSpacerHeight: bottomSpacer,
      virtualApps: apps.slice(start, end),
    };
  }, [apps, scrollTop, viewportHeight, totalCount]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  // Render Collapsed Column (Vertical Minimal Strip)
  if (isCollapsed) {
    return (
      <div
        ref={setNodeRef}
        onClick={onToggleCollapse}
        className={`relative flex flex-col items-center justify-between py-4 px-2 rounded-xl border transition-all cursor-pointer select-none min-h-[640px] w-[50px] flex-shrink-0 ${
          stage.border
        } ${stage.bg} ${
          isOver
            ? 'ring-2 ring-cyan-400/80 bg-cyan-950/50'
            : 'hover:bg-[#161a28]'
        }`}
        title={`点击展开「${stage.label}」(${apps.length})`}
      >
        {/* Top: Icon & Count Badge */}
        <div className="flex flex-col items-center gap-2">
          <div className="p-1 rounded-md bg-[#131622] border border-[#2b3348]">
            <Icon className={`w-4 h-4 ${stage.color}`} />
          </div>
          <span
            className={`text-[11px] font-mono font-bold px-1.5 py-0.5 rounded-full border ${stage.badge}`}
          >
            {apps.length}
          </span>
        </div>

        {/* Center: Vertical Stage Name (Natural Top-to-Bottom CJK Reading) */}
        <div className="py-6 flex flex-col items-center justify-center gap-1">
          {stage.label.split('').map((char, i) => (
            <span
              key={i}
              className="text-[11px] font-medium leading-none text-slate-400 group-hover:text-cyan-300 transition-colors"
            >
              {char}
            </span>
          ))}
        </div>

        {/* Bottom: Expand Chevron Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleCollapse();
          }}
          className="p-1 rounded-md text-[#64748b] hover:text-cyan-300 hover:bg-[#1e2336] transition-colors"
          title="展开该列"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  // Render Expanded Column
  return (
    <div
      ref={setNodeRef}
      className={`relative flex flex-col rounded-xl border p-2.5 min-h-[640px] flex-1 min-w-[240px] transition-all ${
        stage.border
      } ${stage.bg} ${
        isOver
          ? 'ring-2 ring-cyan-500/70 bg-cyan-950/30'
          : ''
      }`}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-[#222738]">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-[#11131e] border border-[#222738]">
            <Icon className={`w-3.5 h-3.5 ${stage.color}`} />
          </div>
          <span className="text-xs font-bold text-[#f1f5f9] tracking-tight">
            {stage.label}
          </span>
          <span
            className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${stage.badge}`}
          >
            {apps.length}
          </span>
        </div>

        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-md text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1a1f30] transition-colors"
          title="收起折叠该列"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Cards Sortable Container */}
      <SortableContext
        items={apps.map((a) => a.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto max-h-[calc(100vh-260px)] pr-1 custom-scrollbar kanban-column-scroll"
        >
          {/* Top Spacer to preserve scroll position */}
          {topSpacerHeight > 0 && (
            <div style={{ height: `${topSpacerHeight}px` }} className="w-full flex-shrink-0" />
          )}

          {/* Virtual Window Cards (1 buffer + visible + 1 buffer) */}
          <div className="space-y-2">
            {virtualApps.map((app) => (
              <KanbanCard
                key={app.id}
                app={app}
                onAdvanceStage={onAdvanceStage}
                onArchive={onArchive}
                onDelete={onDelete}
              />
            ))}
          </div>

          {/* Bottom Spacer to preserve scroll height */}
          {bottomSpacerHeight > 0 && (
            <div style={{ height: `${bottomSpacerHeight}px` }} className="w-full flex-shrink-0" />
          )}

          {apps.length === 0 && (
            <div className="h-36 flex flex-col items-center justify-center border border-dashed border-[#23293d] rounded-xl text-[#64748b] text-[11px] gap-1.5 p-4 text-center mt-2">
              <span className="italic font-medium">暂无投递卡片</span>
              <span className="text-[10px] text-[#475569]">
                拖拽其他阶段卡片至此投放
              </span>
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  );
};

export const KanbanBoard: React.FC = () => {
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCard, setActiveCard] = useState<ApplicationItem | null>(null);
  const [activeTab, setActiveTab] = useState<'active' | 'archived'>('active');
  const [deleteConfirmAppId, setDeleteConfirmAppId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Column collapse state with localStorage persistence
  const [collapsedStages, setCollapsedStages] = useState<Record<string, boolean>>(() => {
    try {
      const saved = localStorage.getItem('jhtracker_kanban_collapsed');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor)
  );

  const fetchApps = async () => {
    try {
      setLoading(true);
      const res = await api.get<ApplicationItem[]>('/api/applications');
      setApps(res.data);
    } catch (e) {
      console.error('Failed to load applications:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, []);

  const toggleCollapse = (stageId: string) => {
    setCollapsedStages((prev) => {
      const next = { ...prev, [stageId]: !prev[stageId] };
      try {
        localStorage.setItem('jhtracker_kanban_collapsed', JSON.stringify(next));
      } catch (e) {
        console.error(e);
      }
      return next;
    });
  };

  const collapseAll = () => {
    const allCollapsed: Record<string, boolean> = {};
    STAGES.forEach((s) => {
      allCollapsed[s.id] = true;
    });
    setCollapsedStages(allCollapsed);
    localStorage.setItem('jhtracker_kanban_collapsed', JSON.stringify(allCollapsed));
  };

  const expandAll = () => {
    setCollapsedStages({});
    localStorage.removeItem('jhtracker_kanban_collapsed');
  };

  const updateAppStatus = async (appId: string, newStatus: ApplicationStatus) => {
    const currentApp = apps.find((a) => a.id === appId);
    if (!currentApp || currentApp.status === newStatus) return;

    const previousApps = [...apps];
    setErrorMessage(null);

    // Optimistic UI update
    setApps((prev) =>
      prev.map((app) => (app.id === appId ? { ...app, status: newStatus } : app))
    );

    try {
      await api.patch(`/api/applications/${appId}/status`, {
        status: newStatus,
      });
    } catch (err) {
      console.error('Failed to update stage:', err);
      // Rollback to previous state on failure
      setApps(previousApps);
      setErrorMessage(`更新岗位「${currentApp.title}」状态失败，已回滚。`);
      setTimeout(() => setErrorMessage(null), 4000);
    }
  };

  const handleArchiveApp = async (appId: string, isArchived: boolean) => {
    const previousApps = [...apps];
    const targetApp = apps.find((a) => a.id === appId);

    // Optimistic UI update
    setApps((prev) =>
      prev.map((app) => (app.id === appId ? { ...app, is_archived: isArchived } : app))
    );

    try {
      await api.patch(`/api/applications/${appId}/archive`, {
        is_archived: isArchived,
      });
    } catch (err) {
      console.error('Failed to update archive status:', err);
      // Rollback to previous state on failure
      setApps(previousApps);
      setErrorMessage(
        `更新岗位「${targetApp?.title || '未知岗位'}」归档状态失败，已回滚。`
      );
      setTimeout(() => setErrorMessage(null), 4000);
    }
  };

  const handleDeleteApp = async (appId: string) => {
    const previousApps = [...apps];
    const targetApp = apps.find((a) => a.id === appId);

    // Optimistic UI update
    setApps((prev) => prev.filter((app) => app.id !== appId));
    setDeleteConfirmAppId(null);

    try {
      await api.delete(`/api/applications/${appId}`);
    } catch (err) {
      console.error('Failed to delete application:', err);
      // Rollback to previous state on failure
      setApps(previousApps);
      setErrorMessage(
        `删除岗位「${targetApp?.title || '未知岗位'}」失败，已回滚。`
      );
      setTimeout(() => setErrorMessage(null), 4000);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const found = apps.find((a) => a.id === active.id);
    if (found) {
      setActiveCard(found);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCard(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    let targetStatus: ApplicationStatus | null = null;
    const isStageColumn = STAGES.some((s) => s.id === overId);

    if (isStageColumn) {
      targetStatus = overId as ApplicationStatus;
    } else {
      const overApp = apps.find((a) => a.id === overId);
      if (overApp) {
        targetStatus = overApp.status;
      }
    }

    if (!targetStatus) return;
    await updateAppStatus(activeId, targetStatus);
  };

  // Filter by active / archived
  const activeApps = useMemo(() => apps.filter((a) => !a.is_archived), [apps]);
  const archivedApps = useMemo(() => apps.filter((a) => !!a.is_archived), [apps]);
  const currentViewApps = activeTab === 'active' ? activeApps : archivedApps;

  // Metrics summary
  const totalApps = activeApps.length;
  const activeInterviews = useMemo(
    () => activeApps.filter((a) => a.status === 'INTERVIEW_STAGE').length,
    [activeApps]
  );
  const totalOffers = useMemo(
    () => activeApps.filter((a) => a.status === 'OFFER_RECEIVED').length,
    [activeApps]
  );
  const appliedCount = useMemo(
    () => activeApps.filter((a) => a.status === 'APPLIED').length,
    [activeApps]
  );

  return (
    <div className="space-y-4">
      {/* Top Metric Strip & Controls */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 p-4 rounded-xl border border-[#222738] bg-[#10121a]">
        {/* Left: Title & Explanations */}
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            <h2 className="text-base font-bold text-[#f8fafc] flex items-center gap-2">
              投递进展看板
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-500/30 text-cyan-300 font-mono">
                实时拖拽流转
              </span>
            </h2>
          </div>
          <p className="text-xs text-[#94a3b8]">
            支持自由折叠各列优化视界，卡片支持跨列拖拽或一键流转推进，变更实时自动持久化至本地私有数据库。
          </p>
        </div>

        {/* Center: Stage Progress Pipeline Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto py-1 text-xs">
          {STAGES.map((s) => {
            const count = currentViewApps.filter((a) => a.status === s.id).length;
            const isCol = !!collapsedStages[s.id];
            const Icon = s.icon;
            return (
              <button
                key={s.id}
                onClick={() => toggleCollapse(s.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-all font-mono text-[11px] ${
                  isCol
                    ? 'bg-[#151824] border-[#222738] text-[#64748b] opacity-60 hover:opacity-100'
                    : `${s.bg} ${s.border} text-[#e2e8f0]`
                }`}
                title={isCol ? `点击展开「${s.label}」` : `点击收起「${s.label}」`}
              >
                <Icon className={`w-3.5 h-3.5 ${s.color}`} />
                <span>{s.shortLabel}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${s.badge}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right: Quick Controls */}
        <div className="flex items-center gap-2 self-start xl:self-auto">
          <button
            onClick={expandAll}
            className="px-2.5 py-1.5 rounded-lg border border-[#24293d] bg-[#141724] hover:bg-[#1a1f30] text-xs text-[#94a3b8] hover:text-white transition-colors flex items-center gap-1"
            title="全部展开"
          >
            <ChevronsLeftRight className="w-3.5 h-3.5 text-cyan-400" />
            <span>全展开</span>
          </button>
          <button
            onClick={collapseAll}
            className="px-2.5 py-1.5 rounded-lg border border-[#24293d] bg-[#141724] hover:bg-[#1a1f30] text-xs text-[#94a3b8] hover:text-white transition-colors flex items-center gap-1"
            title="全部折叠"
          >
            <ChevronsRightLeft className="w-3.5 h-3.5 text-slate-400" />
            <span>全收起</span>
          </button>
          <button
            onClick={fetchApps}
            className="px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/40 hover:bg-cyan-900/50 text-xs font-mono text-cyan-300 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            刷新
          </button>
        </div>
      </div>

      {/* 错误提示浮层（操作回滚提示） */}
      {errorMessage && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between animate-fadeIn">
          <span>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-rose-200 text-xs font-mono ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Tab Switcher: Active Board vs Archived */}
      <div className="flex items-center justify-between border-b border-[#1f2438] pb-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('active')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'active'
                ? 'bg-cyan-500/15 border border-cyan-500/40 text-cyan-300'
                : 'border border-transparent text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#141724]'
            }`}
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>活跃投递</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'active'
                  ? 'bg-cyan-500/20 text-cyan-200'
                  : 'bg-[#1a1f30] text-[#64748b]'
              }`}
            >
              {activeApps.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('archived')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'archived'
                ? 'bg-amber-500/15 border border-amber-500/40 text-amber-300'
                : 'border border-transparent text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#141724]'
            }`}
          >
            <Archive className="w-3.5 h-3.5" />
            <span>已归档箱</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'archived'
                  ? 'bg-amber-500/20 text-amber-200'
                  : 'bg-[#1a1f30] text-[#64748b]'
              }`}
            >
              {archivedApps.length}
            </span>
          </button>
        </div>

        {activeTab === 'archived' && (
          <div className="text-[11px] text-amber-400/80 flex items-center gap-1.5 font-mono">
            <Archive className="w-3 h-3" />
            <span>已归档的卡片保留企业频次防打扰和偏好记忆，支持随时恢复到看板或永久删除</span>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmAppId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-xl border border-red-500/30 bg-[#12141e] p-5 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">彻底删除该投递记录？</h4>
                <p className="text-xs text-[#94a3b8] mt-0.5">此操作不可逆，卡片将从本地私库抹除。</p>
              </div>
            </div>
            <p className="text-xs text-[#64748b] bg-[#0c0e16] p-2.5 rounded-lg border border-[#1e2333]">
              💡 提示：如果只是告一段落或暂时不跟进，推荐使用「归档」以保留企业投递历史与推荐防重复记录。
            </p>
            <div className="flex justify-end gap-2 pt-1">
              <button
                onClick={() => setDeleteConfirmAppId(null)}
                className="px-3 py-1.5 text-xs text-[#94a3b8] hover:text-white bg-[#1a1f30] hover:bg-[#222940] rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleDeleteApp(deleteConfirmAppId)}
                className="px-3.5 py-1.5 text-xs text-red-200 bg-red-950/60 hover:bg-red-900/80 border border-red-500/40 rounded-lg transition-colors font-medium"
              >
                确认彻底删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dnd-kit Drag and Drop Context */}
      {loading ? (
        <div className="py-24 text-center text-xs text-[#64748b]">正在同步本地私有投递数据...</div>
      ) : activeTab === 'archived' && archivedApps.length === 0 ? (
        <div className="py-24 text-center space-y-2 rounded-xl border border-[#1f2438] bg-[#0f111a]">
          <Archive className="w-8 h-8 text-[#475569] mx-auto" />
          <div className="text-xs text-[#94a3b8]">暂无归档卡片</div>
          <div className="text-[11px] text-[#64748b]">
            在「活跃投递」看板中点击卡片右上角的归档按钮，即可将暂时无用的卡片收纳至此。
          </div>
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          {/* Responsive Flexbox Pipeline Layout for Smooth Folding */}
          <div className="flex flex-row items-stretch gap-3 overflow-x-auto pb-4 custom-scrollbar">
            {STAGES.map((stage) => {
              const stageApps = currentViewApps.filter((a) => a.status === stage.id);
              const isCollapsed = !!collapsedStages[stage.id];
              return (
                <KanbanColumn
                  key={stage.id}
                  stage={stage}
                  apps={stageApps}
                  isCollapsed={isCollapsed}
                  onToggleCollapse={() => toggleCollapse(stage.id)}
                  onAdvanceStage={updateAppStatus}
                  onArchive={handleArchiveApp}
                  onDelete={(id) => setDeleteConfirmAppId(id)}
                />
              );
            })}
          </div>

          <DragOverlay>
            {activeCard ? <KanbanCard app={activeCard} isOverlay /> : null}
          </DragOverlay>
        </DndContext>
      )}
    </div>
  );
};
