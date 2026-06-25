/** 简单分页：上一页 / 下一页，page 写在 searchParams。
 *
 * 后端不返回 total，MVP 不算总页数——下一页在「本页满 limit 条」时显示（启发式）。
 * query 透传当前筛选条件，保证翻页时筛选不丢。
 */

import Link from "next/link";

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

  return (
    <nav className="flex items-center justify-center gap-4 py-4">
      {hasPrev ? (
        <Link
          href={pageUrl(page - 1)}
          className="rounded border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          上一页
        </Link>
      ) : (
        <span className="rounded border border-gray-200 px-4 py-1.5 text-sm text-gray-300">
          上一页
        </span>
      )}
      <span className="text-sm text-gray-500">第 {page} 页</span>
      {hasNext ? (
        <Link
          href={pageUrl(page + 1)}
          className="rounded border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          下一页
        </Link>
      ) : (
        <span className="rounded border border-gray-200 px-4 py-1.5 text-sm text-gray-300">
          下一页
        </span>
      )}
    </nav>
  );
}
