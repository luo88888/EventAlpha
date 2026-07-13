/** 事件列表页 /events（从根路径移出）。
 *
 * Server Component：URL searchParams 驱动筛选 + 分页，fetchEvents 取数据。
 * 支持 event_type / importance_level / start_time / end_time 筛选、page 分页。
 */

import { fetchEvents } from "@/lib/api";
import { EventListItem } from "@/components/EventListItem";
import { FilterBar } from "@/components/FilterBar";
import { Pagination } from "@/components/Pagination";
import { Inbox } from "lucide-react";

const LIMIT = 20;

export default async function EventsPage({
  searchParams,
}: {
  searchParams: Promise<{
    event_type?: string;
    importance_level?: string;
    start_time?: string;
    end_time?: string;
    page?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, parseInt(sp.page ?? "1", 10) || 1);
  const offset = (page - 1) * LIMIT;

  const events = await fetchEvents({
    event_type: sp.event_type,
    importance_level: sp.importance_level,
    start_time: sp.start_time,
    end_time: sp.end_time,
    limit: LIMIT,
    offset,
  });

  // 透传给分页的筛选条件（去掉 page 自身）
  const query: Record<string, string> = {};
  if (sp.event_type) query.event_type = sp.event_type;
  if (sp.importance_level) query.importance_level = sp.importance_level;
  if (sp.start_time) query.start_time = sp.start_time;
  if (sp.end_time) query.end_time = sp.end_time;

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-fg)]">
            事件库
          </h1>
          <p className="mt-1 text-sm text-[var(--color-fg-muted)]">
            全部结构化事件 · 支持按类型 / 等级 / 时间筛选
          </p>
        </div>
      </header>

      <FilterBar
        currentType={sp.event_type}
        currentLevel={sp.importance_level}
        currentStart={sp.start_time}
        currentEnd={sp.end_time}
      />

      {events.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] py-16 text-center">
          <Inbox className="mx-auto mb-3 h-10 w-10 text-[var(--color-fg-subtle)]" />
          <p className="text-sm text-[var(--color-fg-muted)]">没有符合条件的事件</p>
          <p className="mt-1 text-xs text-[var(--color-fg-subtle)]">试试调整筛选条件或重置</p>
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((e, i) => (
            <EventListItem key={e.id} event={e} index={i} />
          ))}
        </div>
      )}

      <Pagination page={page} hasNext={events.length === LIMIT} basePath="/events" query={query} />
    </div>
  );
}
