/** 来源列表：暗色卡片 + 来源图标 + 外链箭头 + 发布时间。 */

import Link from "next/link";
import { ExternalLink, FileText } from "lucide-react";

import type { EventSourceOut } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function SourceList({ sources }: { sources: EventSourceOut[] }) {
  if (!sources.length) {
    return (
      <p className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] py-6 text-center text-sm text-[var(--color-fg-subtle)]">
        暂无来源
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {sources.map((s, i) => (
        <li key={i}>
          <a
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-start gap-3 rounded-xl border border-white/8 bg-[var(--color-panel)]/60 p-3 transition hover:border-white/15 hover:bg-[var(--color-panel-soft)]"
          >
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/5 text-[var(--color-fg-muted)]">
              <FileText className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-[var(--color-fg)] transition-colors group-hover:text-cyan-300">
                {s.title}
              </p>
              <div className="mt-1 flex items-center gap-3 text-xs text-[var(--color-fg-subtle)]">
                <span>{s.source_name ?? s.source}</span>
                <span>{formatDate(s.published_at)}</span>
              </div>
            </div>
            <ExternalLink className="mt-1 h-4 w-4 shrink-0 text-[var(--color-fg-subtle)] opacity-0 transition group-hover:text-cyan-300 group-hover:opacity-100" />
          </a>
        </li>
      ))}
    </ul>
  );
}
