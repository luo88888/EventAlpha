/** 事件详情页 /events/{id}。
 *
 * Next 15：params 是 Promise，必须 await。
 * 事件不存在（后端 404）→ notFound() 触发 not-found.tsx。
 * analysis 为 null → AnalysisCard 降级为 EmptyAnalysis。
 */

import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  Database,
  Layers,
} from "lucide-react";

import { fetchEventDetail } from "@/lib/api";
import { getTypeMeta } from "@/lib/constants";
import { formatDateTime } from "@/lib/utils";
import { AnalysisCard } from "@/components/AnalysisCard";
import { EventTypeTag } from "@/components/EventTypeTag";
import { ImportanceBadge } from "@/components/ImportanceBadge";
import { SourceList } from "@/components/SourceList";

export default async function EventDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const idNum = parseInt(id, 10);
  if (Number.isNaN(idNum)) notFound();

  let detail;
  try {
    detail = await fetchEventDetail(idNum);
  } catch (err) {
    if ((err as Error & { status?: number }).status === 404) notFound();
    throw err; // 交给 error.tsx
  }

  const a = detail.analysis;
  const typeMeta = getTypeMeta(detail.event_type);
  const TypeIcon = typeMeta.icon;

  return (
    <div className="space-y-6">
      {/* 返回 */}
      <Link
        href="/events"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--color-fg-muted)] transition hover:text-[var(--color-fg)]"
      >
        <ArrowLeft className="h-4 w-4" />
        返回事件库
      </Link>

      {/* ===== 事件头（渐变毛玻璃）===== */}
      <header className="relative overflow-hidden rounded-3xl border border-white/8 gradient-flow p-6 sm:p-8">
        <div className="relative">
          <div className="flex flex-wrap items-center gap-2">
            <EventTypeTag type={detail.event_type} />
            {a && (
              <ImportanceBadge
                level={a.importance_level}
                score={a.importance_score}
                size="md"
                glow={a.importance_level === "S"}
              />
            )}
            <span className="tabular rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs text-[var(--color-fg-muted)]">
              {detail.event_id}
            </span>
          </div>

          <h1 className="mt-4 text-2xl font-bold leading-snug tracking-tight text-[var(--color-fg)] sm:text-3xl">
            {detail.event_title}
          </h1>

          {detail.summary && (
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[var(--color-fg-muted)]">
              {detail.summary}
            </p>
          )}

          {/* 元数据网格 */}
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetaItem
              icon={TypeIcon}
              label="事件类型"
              value={typeMeta.label}
            />
            <MetaItem
              icon={Building2}
              label="事件主体"
              value={detail.event_subject ?? "—"}
            />
            <MetaItem
              icon={Calendar}
              label="事件时间"
              value={formatDateTime(detail.event_time)}
            />
            <MetaItem
              icon={Layers}
              label="来源数"
              value={`${detail.source_count} 个`}
            />
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-[var(--color-fg-subtle)]">
            <span className="inline-flex items-center gap-1">
              <Database className="h-3 w-3" />
              入库 {formatDateTime(detail.created_at)}
            </span>
            {a && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" />
                分析于 {formatDateTime(a.created_at)}
              </span>
            )}
          </div>
        </div>
        {/* 装饰光斑 */}
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl" />
      </header>

      {/* ===== 影响分析 ===== */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-[var(--color-fg)]">
          🧠 影响分析
        </h2>
        <AnalysisCard analysis={detail.analysis} />
      </section>

      {/* ===== 来源 ===== */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-[var(--color-fg)]">
          📰 事件来源
          <span className="text-sm font-normal text-[var(--color-fg-subtle)]">
            {detail.sources.length} 条原始新闻
          </span>
        </h2>
        <SourceList sources={detail.sources} />
      </section>
    </div>
  );
}

/** 元数据项：图标 + 标签 + 值。 */
function MetaItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.03] p-3">
      <div className="flex items-center gap-1.5 text-xs text-[var(--color-fg-subtle)]">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <p className="mt-1 truncate text-sm font-medium text-[var(--color-fg)]" title={value}>
        {value}
      </p>
    </div>
  );
}
