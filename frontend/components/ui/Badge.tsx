/** 徽章组件：暗色低饱和小标签，支持自定义 class 覆盖配色。 */

import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline" | "solid";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" && "bg-white/5 text-[var(--color-fg-muted)] border border-white/10",
        variant === "outline" && "border border-[var(--color-border-soft)] text-[var(--color-fg-muted)]",
        variant === "solid" && "bg-white/10 text-[var(--color-fg)]",
        className,
      )}
      {...props}
    />
  );
}
