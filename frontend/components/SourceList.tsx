/** 来源列表：每项标题外链 + 来源名 + 发布时间。空列表显示「暂无来源」。 */

import type { EventSourceOut } from "@/lib/types";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("zh-CN");
}

export function SourceList({ sources }: { sources: EventSourceOut[] }) {
  if (!sources.length) {
    return (
      <p className="text-sm text-gray-500">暂无来源</p>
    );
  }
  return (
    <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white">
      {sources.map((s, i) => (
        <li key={i} className="p-3">
          <a
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block truncate text-sm font-medium text-blue-600 hover:underline"
          >
            {s.title}
          </a>
          <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
            <span>{s.source_name ?? s.source}</span>
            <span>{formatDate(s.published_at)}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
