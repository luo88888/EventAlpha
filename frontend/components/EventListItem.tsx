/** 列表项卡片：点击跳详情页 /events/{id}。 */

import Link from "next/link";

import type { EventOut } from "@/lib/types";
import { EventTypeTag } from "./EventTypeTag";

/** 后端时间为 UTC naive ISO 串，按本地时区解析展示日期。MVP 不纠结时区。 */
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

export function EventListItem({ event }: { event: EventOut }) {
  return (
    <Link
      href={`/events/${event.id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-blue-400 hover:shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="line-clamp-2 flex-1 text-base font-semibold text-gray-900">
          {event.event_title}
        </h3>
        <EventTypeTag type={event.event_type} />
      </div>
      {event.summary && (
        <p className="mt-2 line-clamp-2 text-sm text-gray-600">{event.summary}</p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
        <span>{formatDate(event.created_at)}</span>
        <span>{event.source_count} 个来源</span>
        {event.event_subject && <span>主体：{event.event_subject}</span>}
      </div>
    </Link>
  );
}
