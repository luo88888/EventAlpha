/** 按钮组件：暗色，支持 asChild 风格的链接变体（直接传 as="a"/Link）。
 *
 * MVP 轻量实现：variant 控制外观，size 控制尺寸。原 FilterBar 的蓝色按钮统一改用此组件。
 */

import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline";
  size?: "sm" | "md";
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/60 disabled:cursor-not-allowed disabled:opacity-40",
        size === "sm" && "px-3 py-1 text-xs",
        size === "md" && "px-4 py-1.5 text-sm",
        variant === "primary" &&
          "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white hover:from-indigo-400 hover:to-cyan-400 shadow-lg shadow-indigo-500/20",
        variant === "secondary" &&
          "bg-white/5 text-[var(--color-fg)] border border-white/10 hover:bg-white/10",
        variant === "ghost" && "text-[var(--color-fg-muted)] hover:bg-white/5 hover:text-[var(--color-fg)]",
        variant === "outline" &&
          "border border-[var(--color-border-soft)] text-[var(--color-fg-muted)] hover:bg-white/5 hover:text-[var(--color-fg)]",
        className,
      )}
      {...props}
    />
  );
}
