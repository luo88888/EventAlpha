"use client";

/** KPI 统计卡片：渐变描边 + 图标 + 数字滚入动画。
 *
 * 客户端组件：framer-motion 数字滚入需客户端。用于 Dashboard 顶栏 KPI 行。
 * 注意：icon 接收图标名（字符串）而非组件，避免 Server→Client 传函数违反 RSC 序列化。
 * 可选 href：传入则整卡可点击跳转（用 next/link 包裹），右下角显示跳转箭头。
 */

import Link from "next/link";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, type ReactNode } from "react";
import {
  Activity,
  ArrowUpRight,
  Flame,
  TrendingUp,
  Radio,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

/** 可用图标白名单（按名字从 client 侧取，不跨 RSC 边界传组件）。 */
const ICONS: Record<string, LucideIcon> = {
  Activity,
  Flame,
  TrendingUp,
  Radio,
};

/** 数字滚入：从 0 动画到 value。 */
function AnimatedNumber({ value }: { value: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v).toLocaleString("en-US"));
  useEffect(() => {
    const controls = animate(count, value, { duration: 1.1, ease: "easeOut" });
    return controls.stop;
  }, [count, value]);
  return <motion.span className="tabular">{rounded}</motion.span>;
}

export function StatCard({
  label,
  value,
  iconName,
  accent = "indigo",
  hint,
  delay = 0,
  href,
}: {
  label: string;
  value: number;
  iconName: keyof typeof ICONS;
  accent?: "indigo" | "rose" | "cyan" | "amber" | "emerald";
  hint?: ReactNode;
  delay?: number;
  href?: string;
}) {
  const Icon = ICONS[iconName] ?? Activity;
  const accentMap: Record<string, { iconBg: string; glow: string }> = {
    indigo: { iconBg: "from-indigo-500 to-violet-500", glow: "shadow-indigo-500/20" },
    rose: { iconBg: "from-rose-500 to-orange-500", glow: "shadow-rose-500/20" },
    cyan: { iconBg: "from-cyan-500 to-sky-500", glow: "shadow-cyan-500/20" },
    amber: { iconBg: "from-amber-500 to-orange-500", glow: "shadow-amber-500/20" },
    emerald: { iconBg: "from-emerald-500 to-teal-500", glow: "shadow-emerald-500/20" },
  };
  const a = accentMap[accent];

  const inner = (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      className={cn(
        "ring-gradient relative overflow-hidden rounded-2xl bg-[var(--color-panel)]/70 p-5 backdrop-blur-md transition-all duration-300",
        a.glow,
        href && "cursor-pointer hover:-translate-y-1 hover:bg-[var(--color-panel)]/90 hover:shadow-xl",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium tracking-wide text-[var(--color-fg-muted)]">
            {label}
          </p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-[var(--color-fg)]">
            <AnimatedNumber value={value} />
          </p>
          {hint && (
            <div className="mt-1.5 text-xs text-[var(--color-fg-subtle)]">{hint}</div>
          )}
        </div>
        <span
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg",
            a.iconBg,
            a.glow,
          )}
        >
          <Icon className="h-5 w-5 text-white" strokeWidth={2.2} />
        </span>
      </div>
      {/* 可点击时的跳转箭头提示 */}
      {href && (
        <span className="absolute bottom-3 right-3 inline-flex items-center gap-0.5 text-[10px] font-medium text-[var(--color-fg-subtle)] opacity-70 transition-opacity group-hover:opacity-100">
          查看
          <ArrowUpRight className="h-3 w-3" />
        </span>
      )}
      {/* 装饰光斑 */}
      <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full bg-white/5 blur-2xl" />
    </motion.div>
  );

  if (href) {
    return (
      <Link href={href} className="group block">
        {inner}
      </Link>
    );
  }
  return inner;
}

