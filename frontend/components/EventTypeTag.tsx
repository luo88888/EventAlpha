/** 事件类型标签：图标 + 中文名，暗色低饱和配色。
 *
 * 配色与图标来自 lib/constants.ts 的 TYPE_META，未命中走 other 兜底。
 */

import { getTypeMeta } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function EventTypeTag({
  type,
  size = "md",
  withIcon = true,
  className,
}: {
  type: string;
  size?: "sm" | "md";
  withIcon?: boolean;
  className?: string;
}) {
  const meta = getTypeMeta(type);
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-medium",
        meta.chip,
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-0.5 text-xs",
        className,
      )}
    >
      {withIcon && <Icon className="h-3 w-3" strokeWidth={2.2} />}
      {meta.label}
    </span>
  );
}
