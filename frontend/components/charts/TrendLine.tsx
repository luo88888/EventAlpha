"use client";

/** 近 14 天事件趋势折线图（recharts AreaChart + 渐变填充）。
 *
 * 暗色网格，渐变 area 填充，hover 显示日期与数量。
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
} from "recharts";

import type { TrendPoint } from "@/lib/types";

export function TrendLine({ data }: { data: TrendPoint[] }) {
  // 横轴只显示 MM-DD
  const chartData = data.map((d) => ({
    ...d,
    short: d.date.slice(5),
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
        <AreaChart data={chartData} margin={{ top: 16, right: 12, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="trendStroke" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="short"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={18}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            cursor={{ stroke: "rgba(255,255,255,0.2)", strokeWidth: 1 }}
            formatter={(value) => [`${value} 条`, "新增事件"]}
            labelFormatter={(label) => `日期 ${label}`}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="url(#trendStroke)"
            strokeWidth={2.5}
            fill="url(#trendFill)"
            animationDuration={1000}
            dot={{ r: 2.5, fill: "#818cf8", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "#22d3ee", strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
