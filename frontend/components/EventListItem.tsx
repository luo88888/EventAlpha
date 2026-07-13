"use client";

/** 列表项卡片：暗色毛玻璃 + 左侧等级色条 + 入场动画 + hover 抬升。
 *
 * 客户端组件：framer-motion 需客户端。点击整卡跳详情 /events/{id}。
 */

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, Clock, Layers } from "lucide-react";

import type { EventOut } from "@/lib/types";
import { getTypeMeta, getLevelMeta } from "@/lib/constants";
import { cn, formatRelative, formatDateTime } from "@/lib/utils";
import { EventTypeTag } from "./EventTypeTag";
import { ImportanceBadge } from "./ImportanceBadge";

export function EventListItem({ event, index = 0 }: { event: EventOut; index?: number }) {
  const typeMeta = getTypeMeta(event.event_type);
  const levelMeta = getLevelMeta(event.importance_level);
  const isImportant = event.importance_level === "S" || event.importance_level === "A";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.04, 0.4), ease: "easeOut" }}
    >
      <Link
        href={`/events/${event.id}`}
        className={cn(
          "group relative block overflow-hidden rounded-xl border border-white/8 bg-[var(--color-panel)]/80 p-4 pl-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-white/15 hover:bg-[var(--color-panel-soft)]",
          isImportant && event.importance_level === "S" && "hover:shadow-lg hover:shadow-rose-500/10",
          isImportant && event.importance_level === "A" && "hover:shadow-lg hover:shadow-orange-500/10",
        )}
      >
        {/* 左侧等级色条 */}
        <span
          className={cn(
            "absolute inset-y-0 left-0 w-1 bg-gradient-to-b",
            levelMeta.bar,
            !event.importance_level && "opacity-30",
          )}
        />

        <div className="flex items-start justify-between gap-3">
          <h3 className="line-clamp-2 flex-1 text-base font-semibold leading-snug text-[var(--color-fg)] transition-colors group-hover:text-white">
            {event.event_title}
          </h3>
          <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-fg-subtle)] opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-[var(--color-accent-3)] group-hover:opacity-100" />
        </div>

        {/* 标签行 */}
        <div className="mt-2.5 flex flex-wrap items-center gap-2">
          <EventTypeTag type={event.event_type} size="sm" />
          {event.importance_level && (
            <ImportanceBadge
              level={event.importance_level}
              score={event.importance_score}
              size="sm"
              glow={event.importance_level === "S"}
            />
          )}
        </div>

        {event.summary && (
          <p className="mt-2.5 line-clamp-2 text-sm leading-relaxed text-[var(--color-fg-muted)]">
            {event.summary}
          </p>
        )}

        {/* 元数据行 */}
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-fg-subtle)]">
          <span className="inline-flex items-center gap-1" title={formatDateTime(event.created_at)}>
            <Clock className="h-3 w-3" />
            {formatRelative(event.created_at)}
          </span>
          <span className="inline-flex items-center gap-1">
            <Layers className="h-3 w-3" />
            {event.source_count} 个来源
          </span>
          {event.event_subject && (
            <span className="inline-flex items-center gap-1">
              <typeMeta.icon className="h-3 w-3" />
              {event.event_subject}
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  );
}
