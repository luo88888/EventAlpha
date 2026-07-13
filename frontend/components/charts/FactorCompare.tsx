"use client";

/** 正负面因素对比条形图：每条「标签在上 + 强度条在下」。
 *
 * 详情页用：正面因素绿条向右生长，负面因素红条向左生长。标签完整显示不截断
 * （旧的同行布局会被 truncate 切掉长文本）。framer-motion 入场展开。
 */

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";

import { cn } from "@/lib/utils";

/** 文本长度映射条宽（35%-100%），保证短文本也有可见长度。 */
function widthFor(text: string, max: number): number {
  const ratio = Math.min(text.length / Math.max(max, 16), 1);
  return 35 + ratio * 65;
}

function FactorRow({
  text,
  side,
  widthPct,
  delay,
}: {
  text: string;
  side: "positive" | "negative";
  widthPct: number;
  delay: number;
}) {
  const isPos = side === "positive";
  return (
    <div className="space-y-1">
      {/* 标签完整显示，不截断 */}
      <p
        className={cn(
          "text-sm leading-snug text-[var(--color-fg-muted)]",
          !isPos && "text-right",
        )}
      >
        {text}
      </p>
      {/* 强度条：正面靠左生长，负面靠右生长 */}
      <div className={cn("flex", isPos ? "justify-start" : "justify-end")}>
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: `${widthPct}%`, opacity: 1 }}
          transition={{ duration: 0.6, delay, ease: "easeOut" }}
          className={cn(
            "h-1.5 rounded-full border",
            isPos
              ? "border-emerald-400/20 bg-gradient-to-r from-emerald-500/40 to-emerald-400/15"
              : "border-rose-400/20 bg-gradient-to-l from-rose-500/40 to-rose-400/15",
          )}
        />
      </div>
    </div>
  );
}

export function FactorCompare({
  positive,
  negative,
}: {
  positive: string[];
  negative: string[];
}) {
  const maxLen = Math.max(
    ...positive.map((s) => s.length),
    ...negative.map((s) => s.length),
    16,
  );

  if (!positive.length && !negative.length) {
    return (
      <p className="py-4 text-center text-sm text-[var(--color-fg-subtle)]">
        暂无影响因素
      </p>
    );
  }

  return (
    <div className="space-y-5">
      {/* 正面 */}
      <div>
        <div className="mb-2.5 flex items-center gap-1.5 text-xs font-semibold text-emerald-300">
          <TrendingUp className="h-3.5 w-3.5" />
          可能受益 · {positive.length}
        </div>
        <div className="space-y-3">
          {positive.map((f, i) => (
            <FactorRow
              key={i}
              text={f}
              side="positive"
              widthPct={widthFor(f, maxLen)}
              delay={i * 0.08}
            />
          ))}
          {!positive.length && (
            <p className="text-xs text-[var(--color-fg-subtle)]">无</p>
          )}
        </div>
      </div>

      {/* 分隔中线 */}
      <div className="border-t border-white/5" />

      {/* 负面 */}
      <div>
        <div className="mb-2.5 flex items-center gap-1.5 text-xs font-semibold text-rose-300">
          <TrendingDown className="h-3.5 w-3.5" />
          可能承压 · {negative.length}
        </div>
        <div className="space-y-3">
          {negative.map((f, i) => (
            <FactorRow
              key={i}
              text={f}
              side="negative"
              widthPct={widthFor(f, maxLen)}
              delay={i * 0.08}
            />
          ))}
          {!negative.length && (
            <p className="text-xs text-[var(--color-fg-subtle)]">无</p>
          )}
        </div>
      </div>
    </div>
  );
}
