/** 分析卡片：详情页核心。analysis 为 null 时降级为 EmptyAnalysis。 */

import type { AnalysisOut } from "@/lib/types";
import { CausalChain } from "./CausalChain";
import { EmptyAnalysis } from "./EmptyAnalysis";
import { FactorList } from "./FactorList";
import { ImportanceBadge } from "./ImportanceBadge";

function TagList({ items, title }: { items: string[]; title: string }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-gray-700">{title}</h4>
      <div className="flex flex-wrap gap-2">
        {items.map((t, i) => (
          <span
            key={i}
            className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

export function AnalysisCard({ analysis }: { analysis: AnalysisOut | null }) {
  if (!analysis) {
    return <EmptyAnalysis />;
  }
  return (
    <div className="space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <ImportanceBadge
          level={analysis.importance_level}
          score={analysis.importance_score}
        />
        {analysis.model_version && (
          <span className="text-xs text-gray-400">模型 {analysis.model_version}</span>
        )}
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <TagList items={analysis.affected_industries} title="影响行业" />
        <TagList items={analysis.affected_assets} title="影响资产" />
      </div>

      <div>
        <h4 className="mb-2 text-sm font-semibold text-gray-700">因果链</h4>
        <CausalChain steps={analysis.causal_chain} />
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <FactorList
          items={analysis.positive_factors}
          variant="positive"
          title="正面因素"
        />
        <FactorList
          items={analysis.negative_factors}
          variant="negative"
          title="负面因素"
        />
      </div>

      {analysis.risk_warning && (
        <div className="border-l-4 border-amber-400 bg-amber-50 p-3 text-sm text-amber-800">
          <span className="font-semibold">风险提示：</span>
          {analysis.risk_warning}
        </div>
      )}
    </div>
  );
}
