"use client";

/** 因果链：纵向流程图，framer-motion 逐级展开 + 连接箭头。
 *
 * 末节点（市场影响）用 accent 渐变高亮。docs 提示因果链可分叉，但后端当前只存线性
 * list[str]，故先做带视觉层次的纵向流程；分叉留待后续 schema 扩展。
 */

import { motion } from "framer-motion";
import { ArrowDown, GitBranch, Zap } from "lucide-react";

import { cn } from "@/lib/utils";

export function CausalChain({ steps }: { steps: string[] }) {
  if (!steps.length) {
    return (
      <p className="py-4 text-center text-sm text-[var(--color-fg-subtle)]">
        暂无因果链
      </p>
    );
  }

  return (
    <ol className="relative space-y-1">
      {steps.map((s, i) => {
        const isLast = i === steps.length - 1;
        const isFirst = i === 0;
        return (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.15, ease: "easeOut" }}
            className="relative flex items-start gap-3"
          >
            {/* 节点圆 + 连接线 */}
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-bold tabular",
                  isLast
                    ? "border-transparent bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-500 text-white shadow-lg shadow-indigo-500/30"
                    : isFirst
                      ? "border-rose-400/40 bg-rose-500/15 text-rose-300"
                      : "border-white/10 bg-white/5 text-[var(--color-fg-muted)]",
                )}
              >
                {isLast ? <Zap className="h-4 w-4" /> : isFirst ? <GitBranch className="h-3.5 w-3.5" /> : i + 1}
              </span>
              {!isLast && (
                <span className="my-1 flex h-6 w-px flex-col items-center bg-gradient-to-b from-white/20 to-white/5">
                  <ArrowDown className="h-3 w-3 text-white/30" />
                </span>
              )}
            </div>

            {/* 文本 */}
            <div
              className={cn(
                "mb-2 flex-1 rounded-lg border px-3 py-2 text-sm leading-relaxed",
                isLast
                  ? "border-indigo-400/20 bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 font-medium text-[var(--color-fg)]"
                  : "border-white/8 bg-white/[0.03] text-[var(--color-fg-muted)]",
              )}
            >
              {s}
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
