/** 简单分页：上一页 / 下一页 + 页码，page 写在 searchParams。
 *
 * 后端不返回 total，MVP 不算总页数——下一页在「本页满 limit 条」时显示（启发式）。
 * query 透传当前筛选条件，保证翻页时筛选不丢。暗色控件。
 */

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

export function Pagination({
  page,
  hasNext,
  basePath,
  query,
}: {
  page: number;
  hasNext: boolean;
  basePath: string;
  query: Record<string, string>;
}) {
  /** 拼带筛选条件的分页 URL。 */
  const pageUrl = (p: number): string => {
    const qs = new URLSearchParams({ ...query, page: String(p) });
    return `${basePath}?${qs.toString()}`;
  };

  const hasPrev = page > 1;
  if (!hasPrev && !hasNext) return null;

  const btnCls = (active: boolean) =>
    cn(
      "inline-flex items-center gap-1 rounded-lg border px-3.5 py-1.5 text-sm transition",
      active
        ? "border-white/10 bg-white/5 text-[var(--color-fg-muted)] hover:bg-white/10 hover:text-[var(--color-fg)]"
        : "border-white/5 text-[var(--color-fg-subtle)]/50 cursor-default",
    );

  return (
    <nav className="flex items-center justify-center gap-3 py-6">
      {hasPrev ? (
        <Link href={pageUrl(page - 1)} className={btnCls(true)}>
          <ChevronLeft className="h-4 w-4" />
          上一页
        </Link>
      ) : (
        <span className={btnCls(false)}>
          <ChevronLeft className="h-4 w-4" />
          上一页
        </span>
      )}

      <span className="tabular rounded-lg border border-white/8 bg-white/5 px-3 py-1.5 text-sm text-[var(--color-fg-muted)]">
        第 <span className="text-[var(--color-fg)]">{page}</span> 页
      </span>

      {hasNext ? (
        <Link href={pageUrl(page + 1)} className={btnCls(true)}>
          下一页
          <ChevronRight className="h-4 w-4" />
        </Link>
      ) : (
        <span className={btnCls(false)}>
          下一页
          <ChevronRight className="h-4 w-4" />
        </span>
      )}
    </nav>
  );
}
