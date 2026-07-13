"use client";

/** 重要性等级分布柱状图（recharts BarChart）。
 *
 * S/A/B/C/none 各色，柱顶显示数量。暗色网格。
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
} from "recharts";

import type { LevelCount } from "@/lib/types";
import { getLevelMeta } from "@/lib/constants";

export function LevelBar({ data }: { data: LevelCount[] }) {
  const chartData = data.map((d) => ({
    level: getLevelMeta(d.level).label,
    count: d.count,
    fill: getLevelMeta(d.level).color,
  }));

  if (!chartData.length) {
    return (
      <div className="flex h-[260px] items-center justify-center text-sm text-[var(--color-fg-subtle)]">
        暂无数据
      </div>
    );
  }

  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 16, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="level"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            formatter={(value) => [`${value} 条`, "事件数"]}
          />
          <Bar dataKey="count" radius={[6, 6, 0, 0]} animationDuration={900} maxBarSize={48}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} fillOpacity={0.88} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
