/** 列表页筛选器：原生 form GET 提交，改 URL searchParams 触发 Server 重渲染。
 *
 * 纯 Server Component（无 use client）：浏览器原生表单 GET 把 select 值拼到 URL，
 * 整页导航到带 searchParams 的 URL。空 select 值由 api.ts 的 fetchEvents 过滤。
 */

import Link from "next/link";

import { EVENT_TYPES, IMPORTANCE_LEVELS } from "@/lib/types";

const TYPE_LABEL: Record<string, string> = {
  policy: "政策",
  trade: "贸易",
  rate: "利率",
  tech: "科技",
  company: "公司",
  disaster: "灾害",
  geopolitical: "地缘",
  other: "其他",
};

export function FilterBar({
  currentType,
  currentLevel,
}: {
  currentType?: string;
  currentLevel?: string;
}) {
  return (
    <form
      method="get"
      className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      <label className="flex flex-col gap-1 text-sm text-gray-600">
        事件类型
        <select
          name="event_type"
          defaultValue={currentType ?? ""}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">全部</option>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {TYPE_LABEL[t] ?? t}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm text-gray-600">
        重要性
        <select
          name="importance_level"
          defaultValue={currentLevel ?? ""}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">全部</option>
          {IMPORTANCE_LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}级
            </option>
          ))}
        </select>
      </label>

      <button
        type="submit"
        className="rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
      >
        筛选
      </button>
      <Link
        href="/"
        className="rounded border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
      >
        重置
      </Link>
    </form>
  );
}
