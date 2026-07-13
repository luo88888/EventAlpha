/** 基础容器组件：毛玻璃卡片，暗色设计系统。
 *
 * 复用 shadcn/ui 的 API 思路但轻量手写，避免引入完整 CLI。variant 控制视觉强度。
 */

import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glass" | "gradient";
}

export function Card({ className, variant = "default", ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl",
        variant === "default" && "bg-[var(--color-panel)] border border-[var(--color-border)]",
        variant === "glass" && "glass",
        variant === "gradient" && "glass-strong",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pt-5 pb-3", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-sm font-semibold tracking-wide text-[var(--color-fg-muted)]", className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pb-5", className)} {...props} />;
}
