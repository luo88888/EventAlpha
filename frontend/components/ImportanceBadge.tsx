/** 重要性等级徽章：S/A/B/C 配色，可选展示分数。
 *
 * 配色来自 lib/constants.ts 的 LEVEL_META，S/A 级用渐变高对比，B/C 级低饱和。
 * 可选 size 与 glow（S 级脉冲光晕）。
 */

import { getLevelMeta } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function ImportanceBadge({
  level,
  score,
  size = "md",
  glow = false,
  className,
}: {
  level: string | null | undefined;
  score?: number | null;
  size?: "sm" | "md" | "lg";
  glow?: boolean;
  className?: string;
}) {
  const meta = getLevelMeta(level);
  const sizeCls =
    size === "sm"
      ? "px-2 py-0.5 text-[11px]"
      : size === "lg"
        ? "px-3 py-1 text-base"
        : "px-2.5 py-0.5 text-xs";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-bold tracking-wide",
        meta.badge,
        sizeCls,
        glow && level === "S" && "animate-[glow_2.4s_ease-in-out_infinite]",
        className,
      )}
    >
      {meta.label}
      {score != null && (
        <span className="tabular opacity-90">· {score}分</span>
      )}
    </span>
  );
}
