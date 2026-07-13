"use client";

/** 事件类型分布环形图（recharts PieChart donut）。
 *
 * 中心显示总数，扇区用 TYPE_META 配色，hover 高亮。无数据时降级提示。
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

import type { TypeCount } from "@/lib/types";
import { getTypeMeta } from "@/lib/constants";

export function TypeDonut({ data }: { data: TypeCount[] }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const chartData = data.map((d) => ({
    name: getTypeMeta(d.type).label,
    value: d.count,
    color: getTypeMeta(d.type).color,
    type: d.type,
  }));

  if (!chartData.length) {
    return (
      <div className="flex h-[260px] items-center justify-center text-sm text-[var(--color-fg-subtle)]">
        暂无数据
      </div>
    );
  }

  return (
    <div className="relative h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={68}
            outerRadius={100}
            paddingAngle={3}
            stroke="none"
            animationDuration={900}
          >
            {chartData.map((entry) => (
              <Cell key={entry.type} fill={entry.color} fillOpacity={0.85} />
            ))}
          </Pie>
          <Tooltip
            cursor={false}
            formatter={(value, _name, item) => {
              const v = Number(value) || 0;
              const pct = total ? ((v / total) * 100).toFixed(1) : "0";
              const label = (item?.payload as { name?: string })?.name ?? "";
              return [`${v} 条 · ${pct}%`, label];
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      {/* 中心总数 */}
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular text-3xl font-bold text-[var(--color-fg)]">{total}</span>
        <span className="mt-0.5 text-xs text-[var(--color-fg-muted)]">事件总数</span>
      </div>
    </div>
  );
}
