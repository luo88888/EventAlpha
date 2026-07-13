/** 设计系统常量：事件类型 / 重要性等级的元数据（中文名 + 颜色 + lucide 图标）。
 *
 * 统一 Eliminate 各组件里重复的 TYPE_LABEL / TYPE_STYLE / LEVEL_STYLE 映射表。
 * 暗色低饱和配色，配合 globals.css 的设计 token。
 */

import {
  Activity,
  Banknote,
  Building2,
  CircleEllipsis,
  Cpu,
  Factory,
  Gauge,
  Globe2,
  Landmark,
  Percent,
  Radar,
  Ship,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
  type LucideIcon,
} from "lucide-react";

/** 事件类型元数据。key 与后端 event_type 枚举逐字对齐。 */
export interface TypeMeta {
  label: string;
  /** 主色（hex），用于图表与色条 */
  color: string;
  /** 暗色标签 class：背景/文字/边框（低饱和） */
  chip: string;
  /** 色条/描边渐变（左侧等级条用） */
  glow: string;
  icon: LucideIcon;
}

export const TYPE_META: Record<string, TypeMeta> = {
  policy: {
    label: "政策",
    color: "#a78bfa",
    chip: "bg-violet-500/10 text-violet-300 border-violet-400/20",
    glow: "from-violet-500 to-purple-500",
    icon: Landmark,
  },
  trade: {
    label: "贸易",
    color: "#fb923c",
    chip: "bg-orange-500/10 text-orange-300 border-orange-400/20",
    glow: "from-orange-500 to-amber-500",
    icon: Ship,
  },
  rate: {
    label: "利率",
    color: "#34d399",
    chip: "bg-emerald-500/10 text-emerald-300 border-emerald-400/20",
    glow: "from-emerald-500 to-teal-500",
    icon: Percent,
  },
  tech: {
    label: "科技",
    color: "#60a5fa",
    chip: "bg-blue-500/10 text-blue-300 border-blue-400/20",
    glow: "from-blue-500 to-indigo-500",
    icon: Cpu,
  },
  company: {
    label: "公司",
    color: "#22d3ee",
    chip: "bg-cyan-500/10 text-cyan-300 border-cyan-400/20",
    glow: "from-cyan-500 to-sky-500",
    icon: Building2,
  },
  disaster: {
    label: "灾害",
    color: "#f43f5e",
    chip: "bg-rose-500/10 text-rose-300 border-rose-400/20",
    glow: "from-rose-500 to-red-500",
    icon: Zap,
  },
  geopolitical: {
    label: "地缘",
    color: "#fbbf24",
    chip: "bg-amber-500/10 text-amber-300 border-amber-400/20",
    glow: "from-amber-500 to-yellow-500",
    icon: Globe2,
  },
  other: {
    label: "其他",
    color: "#94a3b8",
    chip: "bg-slate-500/10 text-slate-300 border-slate-400/20",
    glow: "from-slate-500 to-gray-500",
    icon: CircleEllipsis,
  },
};

/** 重要性等级元数据。S/A/B/C + none（未分析）。 */
export interface LevelMeta {
  label: string;
  color: string;
  /** 徽章 class */
  badge: string;
  /** 色条渐变 */
  bar: string;
  /** 文字描述（处置建议，来自 docs）*/
  hint: string;
}

export const LEVEL_META: Record<string, LevelMeta> = {
  S: {
    label: "S 级",
    color: "#f43f5e",
    badge: "bg-gradient-to-r from-rose-500 to-orange-500 text-white border-rose-400/40",
    bar: "from-rose-500 to-orange-500",
    hint: "立即推送 · 高频追踪",
  },
  A: {
    label: "A 级",
    color: "#f97316",
    badge: "bg-gradient-to-r from-orange-500 to-amber-500 text-white border-orange-400/40",
    bar: "from-orange-500 to-amber-500",
    hint: "重点推送 · 持续跟踪",
  },
  B: {
    label: "B 级",
    color: "#3b82f6",
    badge: "bg-blue-500/15 text-blue-300 border-blue-400/30",
    bar: "from-blue-500 to-indigo-500",
    hint: "纳入日报 · 低频跟踪",
  },
  C: {
    label: "C 级",
    color: "#64748b",
    badge: "bg-slate-500/15 text-slate-300 border-slate-400/30",
    bar: "from-slate-500 to-gray-500",
    hint: "入库 · 不主动推送",
  },
  none: {
    label: "未分析",
    color: "#475569",
    badge: "bg-slate-700/30 text-slate-400 border-slate-600/30",
    bar: "from-slate-700 to-slate-600",
    hint: "分析生成中",
  },
};

/** 通用图标导出，供组件按需引用。 */
export const ICONS = {
  Activity,
  Radar,
  Gauge,
  Target,
  Sparkles,
  TrendingUp,
  Factory,
  Banknote,
  Briefcase: Building2,
  Coins: Banknote,
};

/** 安全取类型元数据，未命中走 other 兜底。 */
export function getTypeMeta(type: string): TypeMeta {
  return TYPE_META[type] ?? TYPE_META.other;
}

/** 安全取等级元数据，未命中走 none 兜底。 */
export function getLevelMeta(level: string | null | undefined): LevelMeta {
  if (!level) return LEVEL_META.none;
  return LEVEL_META[level] ?? LEVEL_META.none;
}
