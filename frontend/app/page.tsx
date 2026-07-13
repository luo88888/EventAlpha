/** 首页 / = Dashboard 控制台。
 *
 * Server Component：fetchStats() 一次取齐聚合数据，传给客户端图表/卡片组件。
 * 布局：标题区 → KPI 行 → 图表区 → 重要事件流 → 合规横幅。
 */

import Link from "next/link";
import {
  ArrowRight,
  Flame,
  Newspaper,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { fetchStats } from "@/lib/api";
import { getTypeMeta, getLevelMeta } from "@/lib/constants";
import { cn, formatRelative, isToday } from "@/lib/utils";
import { StatCard } from "@/components/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { CollectButton } from "@/components/CollectButton";
import { EventTypeTag } from "@/components/EventTypeTag";
import { ImportanceBadge } from "@/components/ImportanceBadge";
import { ComplianceBanner } from "@/components/ComplianceBanner";
import { TypeDonut } from "@/components/charts/TypeDonut";
import { LevelBar } from "@/components/charts/LevelBar";
import { TrendLine } from "@/components/charts/TrendLine";

export default async function DashboardPage() {
  const stats = await fetchStats();

  const totalEvents = stats.totals.events ?? 0;
  const importantCount =
    (stats.level_distribution.find((l) => l.level === "S")?.count ?? 0) +
    (stats.level_distribution.find((l) => l.level === "A")?.count ?? 0);
  const todayPoint = stats.trend.slice(-1)[0];
  const todayCount = todayPoint?.count ?? 0;
  const todayDate = todayPoint?.date; // YYYY-MM-DD，用于"今日新增"跳转筛选
  const sourceCount = stats.source_distribution.length;

  return (
    <div className="space-y-8">
      {/* ===== 标题区 ===== */}
      <section className="relative overflow-hidden rounded-3xl border border-white/8 gradient-flow p-6 sm:p-8">
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--color-fg-muted)]">
              <Sparkles className="h-3.5 w-3.5 text-cyan-300" />
              事件驱动投研控制台
            </div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              <span className="text-gradient">EventAlpha</span>
              <span className="ml-2 text-[var(--color-fg)]">热点事件雷达</span>
            </h1>
            <p className="mt-2 max-w-xl text-sm text-[var(--color-fg-muted)]">
              持续采集财经新闻 → LLM 抽取结构化事件 → 推理分析投资影响。让事件产生投资洞见。
            </p>
          </div>
          <div className="flex items-center gap-2">
            <CollectButton />
            <Link
              href="/events"
              className="group inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-[var(--color-fg)] transition hover:border-indigo-400/40 hover:bg-white/10"
            >
              查看全部事件
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
        {/* 装饰光斑 */}
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 left-1/3 h-40 w-40 rounded-full bg-cyan-500/10 blur-3xl" />
      </section>

      {/* ===== KPI 行 ===== */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="事件总数"
          value={totalEvents}
          iconName="Activity"
          accent="indigo"
          hint={<span>结构化事件库</span>}
          delay={0}
          href="/events"
        />
        <StatCard
          label="S · A 级重要事件"
          value={importantCount}
          iconName="Flame"
          accent="rose"
          hint={<span>需重点跟踪</span>}
          delay={0.06}
          href="/events?importance_level=S"
        />
        <StatCard
          label="今日新增"
          value={todayCount}
          iconName="TrendingUp"
          accent="emerald"
          hint={<span>最近 24 小时</span>}
          delay={0.12}
          href={todayDate ? `/events?start_time=${todayDate}` : "/events"}
        />
        <StatCard
          label="覆盖新闻源"
          value={sourceCount}
          iconName="Radio"
          accent="cyan"
          hint={<span>RSS 持续采集中</span>}
          delay={0.18}
        />
      </section>

      {/* ===== 图表区 ===== */}
      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Newspaper className="h-4 w-4 text-indigo-300" />
              事件类型分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TypeDonut data={stats.type_distribution} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-4 w-4 text-rose-300" />
              重要性等级分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <LevelBar data={stats.level_distribution} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-cyan-300" />
              近 14 天事件趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TrendLine data={stats.trend} />
          </CardContent>
        </Card>
      </section>

      {/* ===== 重要事件流 ===== */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Flame className="h-5 w-5 text-rose-400" />
            重要事件流
            <span className="text-sm font-normal text-[var(--color-fg-subtle)]">
              S · A 级 · 按重要性排序
            </span>
          </h2>
          <Link
            href="/events?importance_level=S"
            className="text-sm text-[var(--color-fg-muted)] transition hover:text-[var(--color-fg)]"
          >
            查看更多 →
          </Link>
        </div>

        {stats.top_events.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-[var(--color-fg-subtle)]">
              暂无 S · A 级重要事件
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {stats.top_events.map((e, i) => {
              const levelMeta = getLevelMeta(e.importance_level);
              const isS = e.importance_level === "S";
              return (
                <Link
                  key={e.id}
                  href={`/events/${e.id}`}
                  className={cn(
                    "group relative overflow-hidden rounded-xl border border-white/8 bg-[var(--color-panel)]/70 p-4 pl-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-white/15",
                    isS && "animate-[glow_2.4s_ease-in-out_infinite]",
                  )}
                >
                  {/* 等级色条 */}
                  <span
                    className={cn("absolute inset-y-0 left-0 w-1 bg-gradient-to-b", levelMeta.bar)}
                  />
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="mb-2 flex items-center gap-2">
                        <EventTypeTag type={e.event_type} size="sm" />
                        {e.importance_level && (
                          <ImportanceBadge
                            level={e.importance_level}
                            score={e.importance_score}
                            size="sm"
                            glow={isS}
                          />
                        )}
                      </div>
                      <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-[var(--color-fg)] transition-colors group-hover:text-white">
                        {e.event_title}
                      </h3>
                      <p className="mt-1.5 text-xs text-[var(--color-fg-subtle)]">
                        {isToday(e.created_at) ? "今日" : formatRelative(e.created_at)} ·{" "}
                        {e.event_id}
                      </p>
                    </div>
                    <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-[var(--color-fg-subtle)] opacity-0 transition group-hover:translate-x-0.5 group-hover:text-[var(--color-accent-3)] group-hover:opacity-100" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>

      {/* ===== 页内合规横幅 ===== */}
      <ComplianceBanner />
    </div>
  );
}
