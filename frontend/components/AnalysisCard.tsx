/** 分析卡片：详情页核心。analysis 为 null 时降级为 EmptyAnalysis。
 *
 * 图表化重构：ImportanceGauge 仪表盘 + 影响行业/资产标签云 + CausalChain 流程图 +
 * FactorCompare 正负面对比条形 + 醒目风险提示。
 */

import { AlertTriangle, Building, Briefcase, Cpu } from "lucide-react";

import type { AnalysisOut } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { CausalChain } from "./CausalChain";
import { EmptyAnalysis } from "./EmptyAnalysis";
import { ImportanceBadge } from "./ImportanceBadge";
import { ImportanceGauge } from "./charts/ImportanceGauge";
import { FactorCompare } from "./charts/FactorCompare";

/** 影响行业/资产标签云：图标 + 文本，渐入。 */
function TagCloud({
  items,
  icon: Icon,
  emptyText,
}: {
  items: string[];
  icon: React.ComponentType<{ className?: string }>;
  emptyText: string;
}) {
  if (!items.length) {
    return <p className="text-xs text-[var(--color-fg-subtle)]">{emptyText}</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((t, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-[var(--color-fg-muted)] transition hover:border-indigo-400/30 hover:bg-indigo-500/10 hover:text-indigo-200"
        >
          <Icon className="h-3 w-3 text-[var(--color-fg-subtle)]" />
          {t}
        </span>
      ))}
    </div>
  );
}

export function AnalysisCard({ analysis }: { analysis: AnalysisOut | null }) {
  if (!analysis) {
    return <EmptyAnalysis />;
  }

  return (
    <div className="space-y-4">
      {/* ===== 重要性仪表盘 + 等级 ===== */}
      <Card variant="glass">
        <CardContent className="pt-5">
          <div className="grid gap-4 sm:grid-cols-[200px_1fr] sm:items-center">
            <ImportanceGauge
              level={analysis.importance_level}
              score={analysis.importance_score}
            />
            <div className="space-y-3 sm:pl-2">
              <div className="flex flex-wrap items-center gap-2">
                <ImportanceBadge
                  level={analysis.importance_level}
                  score={analysis.importance_score}
                  size="lg"
                  glow={analysis.importance_level === "S"}
                />
              </div>
              <p className="text-sm text-[var(--color-fg-muted)]">
                重要性评分 <span className="tabular font-bold text-[var(--color-fg)]">{analysis.importance_score}</span> / 5
                ，等级 <span className="font-bold text-[var(--color-fg)]">{analysis.importance_level}</span>
                。该评分由 LLM 基于事件影响范围、资产相关性与时效性综合判定。
              </p>
              {analysis.model_version && (
                <p className="text-xs text-[var(--color-fg-subtle)]">
                  分析模型：{analysis.model_version}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ===== 影响行业 / 资产 ===== */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-4 w-4 text-violet-300" />
              影响行业 · {analysis.affected_industries.length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TagCloud
              items={analysis.affected_industries}
              icon={Building}
              emptyText="暂无影响行业"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-cyan-300" />
              影响资产 · {analysis.affected_assets.length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TagCloud
              items={analysis.affected_assets}
              icon={Briefcase}
              emptyText="暂无影响资产"
            />
          </CardContent>
        </Card>
      </div>

      {/* ===== 因果链流程图 ===== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-300" />
            因果传导链
            <span className="text-xs font-normal text-[var(--color-fg-subtle)]">
              事件 → 传导 → 市场影响
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CausalChain steps={analysis.causal_chain} />
        </CardContent>
      </Card>

      {/* ===== 正负面对比 ===== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-300" />
            影响因素对比
            <span className="text-xs font-normal text-[var(--color-fg-subtle)]">
              可能受益 vs 可能承压
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FactorCompare
            positive={analysis.positive_factors}
            negative={analysis.negative_factors}
          />
        </CardContent>
      </Card>

      {/* ===== 风险提示（醒目）===== */}
      {analysis.risk_warning && (
        <div className="relative overflow-hidden rounded-2xl border border-amber-400/25 bg-gradient-to-r from-amber-500/12 via-orange-500/8 to-amber-500/12 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" strokeWidth={2} />
            <div className="text-sm leading-relaxed text-amber-100/90">
              <span className="font-semibold text-amber-300">风险提示：</span>
              {analysis.risk_warning}
            </div>
          </div>
          <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-amber-400/10 blur-2xl" />
        </div>
      )}
    </div>
  );
}
