/** 空分析占位：暗色虚线卡片 + 图标提示。 */

import { BrainCog } from "lucide-react";

export function EmptyAnalysis() {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] py-12 text-center">
      <BrainCog className="mx-auto mb-3 h-10 w-10 text-[var(--color-fg-subtle)]" />
      <p className="text-sm font-medium text-[var(--color-fg-muted)]">
        该事件尚未生成分析
      </p>
      <p className="mt-1 text-xs text-[var(--color-fg-subtle)]">
        分析由定时任务或手动触发生成，稍后可刷新查看
      </p>
    </div>
  );
}
