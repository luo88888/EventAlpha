/** 醒目合规横幅：docs 明确要求风险提示不能藏成小字灰字。
 *
 * 渐变琥珀色 + 警告图标，置于页脚与详情页风险区。强调「研究辅助、不构成投资建议」。
 */

import { ShieldAlert } from "lucide-react";

import { cn } from "@/lib/utils";

export function ComplianceBanner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-amber-400/20 bg-gradient-to-r from-amber-500/10 via-orange-500/8 to-amber-500/10 px-4 py-3",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <ShieldAlert
          className="mt-0.5 h-5 w-5 shrink-0 text-amber-400"
          strokeWidth={2}
        />
        <div className="text-xs leading-relaxed text-amber-200/90">
          <span className="font-semibold text-amber-300">合规与风险提示：</span>
          本平台内容仅为基于公开新闻的事件研究辅助，<b className="text-amber-200">不构成任何投资建议</b>
          ，不输出买卖信号、目标价或收益承诺。市场有风险，决策需独立判断。
        </div>
      </div>
      {/* 装饰光晕 */}
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-amber-400/10 blur-2xl" />
    </div>
  );
}
