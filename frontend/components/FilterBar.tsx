/** 列表页筛选器：原生 form GET 提交，改 URL searchParams 触发 Server 重渲染。
 *
 * 纯 Server Component（无 use client）：浏览器原生表单 GET 把 select/date 值拼到 URL。
 * 暗色控件 + lucide 图标 + 已选筛选标签可清除。
 */

import Link from "next/link";
import { Filter, RotateCcw, Search, X } from "lucide-react";

import { EVENT_TYPES, IMPORTANCE_LEVELS } from "@/lib/types";
import { getTypeMeta, getLevelMeta } from "@/lib/constants";
import { Button } from "./ui/Button";

const LEVEL_LABEL: Record<string, string> = {
  S: "S 级",
  A: "A 级",
  B: "B 级",
  C: "C 级",
};

// select 的 option 在某些 Windows 浏览器展开时默认黑字深底看不清，
// 显式同时设背景与文字色保证对比；input 不需要 option 样式。
const inputCls =
  "rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-[var(--color-fg)] outline-none transition focus:border-indigo-400/50 focus:bg-white/8";
const selectCls =
  "rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-[var(--color-fg)] outline-none transition focus:border-indigo-400/50 focus:bg-white/8 [&>option]:bg-[var(--color-panel)] [&>option]:text-[var(--color-fg)] [&>option]:px-2 [&>option]:py-1";

export function FilterBar({
  currentType,
  currentLevel,
  currentStart,
  currentEnd,
}: {
  currentType?: string;
  currentLevel?: string;
  currentStart?: string;
  currentEnd?: string;
}) {
  const hasFilter = Boolean(currentType || currentLevel || currentStart || currentEnd);

  return (
    <div className="rounded-2xl border border-white/8 bg-[var(--color-panel)]/60 p-4 backdrop-blur-sm">
      <form method="get" className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-[var(--color-fg-muted)]">
          事件类型
          <select name="event_type" defaultValue={currentType ?? ""} className={selectCls}>
            <option value="">全部类型</option>
            {EVENT_TYPES.map((t) => {
              const m = getTypeMeta(t);
              return (
                <option key={t} value={t}>
                  {m.label}
                </option>
              );
            })}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-[var(--color-fg-muted)]">
          重要性
          <select
            name="importance_level"
            defaultValue={currentLevel ?? ""}
            className={selectCls}
          >
            <option value="">全部等级</option>
            {IMPORTANCE_LEVELS.map((l) => (
              <option key={l} value={l}>
                {LEVEL_LABEL[l] ?? l}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-[var(--color-fg-muted)]">
          起始日期
          <input
            type="date"
            name="start_time"
            defaultValue={currentStart ?? ""}
            className={inputCls}
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-[var(--color-fg-muted)]">
          结束日期
          <input
            type="date"
            name="end_time"
            defaultValue={currentEnd ?? ""}
            className={inputCls}
          />
        </label>

        <Button type="submit" size="md">
          <Search className="h-4 w-4" />
          筛选
        </Button>

        {hasFilter && (
          <Link
            href="/events"
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-[var(--color-fg-muted)] transition hover:bg-white/5 hover:text-[var(--color-fg)]"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            重置
          </Link>
        )}
      </form>

      {/* 已选筛选标签 */}
      {hasFilter && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-white/5 pt-3">
          <span className="inline-flex items-center gap-1 text-xs text-[var(--color-fg-subtle)]">
            <Filter className="h-3 w-3" />
            已筛选：
          </span>
          {currentType && (
            <span
              className="rounded-full border px-2 py-0.5 text-xs"
              style={{
                borderColor: `${getTypeMeta(currentType).color}40`,
                color: getTypeMeta(currentType).color,
                background: `${getTypeMeta(currentType).color}14`,
              }}
            >
              {getTypeMeta(currentType).label}
            </span>
          )}
          {currentLevel && (
            <span
              className="rounded-full border px-2 py-0.5 text-xs font-semibold"
              style={{
                borderColor: `${getLevelMeta(currentLevel).color}40`,
                color: getLevelMeta(currentLevel).color,
                background: `${getLevelMeta(currentLevel).color}14`,
              }}
            >
              {LEVEL_LABEL[currentLevel] ?? currentLevel}
            </span>
          )}
          {currentStart && (
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-[var(--color-fg-muted)]">
              起 {currentStart}
            </span>
          )}
          {currentEnd && (
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-[var(--color-fg-muted)]">
              止 {currentEnd}
            </span>
          )}
          <Link
            href="/events"
            className="inline-flex items-center gap-0.5 text-xs text-[var(--color-fg-subtle)] transition hover:text-rose-400"
          >
            <X className="h-3 w-3" />
            清除
          </Link>
        </div>
      )}
    </div>
  );
}
