"use client";

/** 重要性仪表盘（recharts RadialBarChart 半圆）。
 *
 * 详情页用：importance_score 1-5 映射到 0-100% 填充。颜色随等级。
 * 中心大字显示等级 + 分数。
 */

import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";

import { getLevelMeta } from "@/lib/constants";

export function ImportanceGauge({
  level,
  score,
}: {
  level: string;
  score: number;
}) {
  const meta = getLevelMeta(level);
  // score 1-5 → 填充百分比 20-100
  const pct = Math.min(Math.max(score, 1), 5) * 20;
  const data = [{ name: "score", value: pct, fill: meta.color }];

  return (
    <div className="relative h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          data={data}
          startAngle={90}
          endAngle={-270}
          innerRadius="72%"
          outerRadius="100%"
          barSize={14}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: "rgba(255,255,255,0.05)" }}
            dataKey="value"
            cornerRadius={10}
            animationDuration={1000}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      {/* 中心等级 + 分数 */}
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-2xl font-extrabold tracking-tight"
          style={{ color: meta.color }}
        >
          {meta.label}
        </span>
        <span className="tabular mt-1 text-sm text-[var(--color-fg-muted)]">
          {score} / 5 分
        </span>
      </div>
    </div>
  );
}
