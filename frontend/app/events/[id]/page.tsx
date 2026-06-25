/** 事件详情页 /events/{id}。
 *
 * Next 15：params 是 Promise，必须 await。
 * 事件不存在（后端 404）→ notFound() 触发 not-found.tsx。
 * 真实库当前全无分析，analysis 为 null → AnalysisCard 降级为 EmptyAnalysis。
 */

import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchEventDetail } from "@/lib/api";
import { AnalysisCard } from "@/components/AnalysisCard";
import { EventTypeTag } from "@/components/EventTypeTag";
import { ImportanceBadge } from "@/components/ImportanceBadge";
import { SourceList } from "@/components/SourceList";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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

  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <Link
        href="/"
        className="mb-4 inline-block text-sm text-blue-600 hover:underline"
      >
        ← 返回列表
      </Link>

      {/* 事件头 */}
      <header className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <EventTypeTag type={detail.event_type} />
          {a && <ImportanceBadge level={a.importance_level} score={a.importance_score} />}
          <span className="text-xs text-gray-400">{detail.event_id}</span>
        </div>
        <h1 className="mt-3 text-xl font-bold text-gray-900">{detail.event_title}</h1>
        {detail.summary && (
          <p className="mt-2 text-sm text-gray-600">{detail.summary}</p>
        )}
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-gray-500">
          {detail.event_subject && <span>主体：{detail.event_subject}</span>}
          <span>事件时间：{formatDate(detail.event_time)}</span>
          <span>入库时间：{formatDate(detail.created_at)}</span>
          <span>{detail.source_count} 个来源</span>
        </div>
      </header>

      {/* 分析卡片 */}
      <section className="mb-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">影响分析</h2>
        <AnalysisCard analysis={detail.analysis} />
      </section>

      {/* 来源列表 */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">来源</h2>
        <SourceList sources={detail.sources} />
      </section>
    </main>
  );
}
