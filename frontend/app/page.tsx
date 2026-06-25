/** 事件列表页（根路径 /）。
 *
 * Next 15：searchParams 是 Promise，必须 await。
 * Server Component，cache: no-store 保证最新（见 lib/api.ts）。
 */

import { fetchEvents } from "@/lib/api";
import { EventListItem } from "@/components/EventListItem";
import { FilterBar } from "@/components/FilterBar";
import { Pagination } from "@/components/Pagination";

const LIMIT = 20;

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{
    event_type?: string;
    importance_level?: string;
    page?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, parseInt(sp.page ?? "1", 10) || 1);
  const offset = (page - 1) * LIMIT;

  const events = await fetchEvents({
    event_type: sp.event_type,
    importance_level: sp.importance_level,
    limit: LIMIT,
    offset,
  });

  // 透传给分页的筛选条件（去掉 page 自身）
  const query: Record<string, string> = {};
  if (sp.event_type) query.event_type = sp.event_type;
  if (sp.importance_level) query.importance_level = sp.importance_level;

  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <header className="mb-5">
        <h1 className="text-2xl font-bold text-gray-900">EventAlpha 热点事件</h1>
        <p className="mt-1 text-sm text-gray-500">热点事件驱动的投资研究</p>
      </header>

      <div className="mb-5">
        <FilterBar currentType={sp.event_type} currentLevel={sp.importance_level} />
      </div>

      {events.length === 0 ? (
        <p className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
          暂无事件
        </p>
      ) : (
        <div className="space-y-3">
          {events.map((e) => (
            <EventListItem key={e.id} event={e} />
          ))}
        </div>
      )}

      <Pagination
        page={page}
        hasNext={events.length === LIMIT}
        basePath="/"
        query={query}
      />
    </main>
  );
}
