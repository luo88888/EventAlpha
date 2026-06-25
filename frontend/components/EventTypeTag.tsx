/** 事件类型配色标签。未命中的 type 走灰色兜底。 */

import type { EventType } from "@/lib/types";

const TYPE_STYLE: Record<string, string> = {
  policy: "bg-purple-100 text-purple-700",
  trade: "bg-orange-100 text-orange-700",
  rate: "bg-green-100 text-green-700",
  tech: "bg-blue-100 text-blue-700",
  company: "bg-cyan-100 text-cyan-700",
  disaster: "bg-red-100 text-red-700",
  geopolitical: "bg-amber-100 text-amber-700",
  other: "bg-gray-100 text-gray-600",
};

const TYPE_LABEL: Record<string, string> = {
  policy: "政策",
  trade: "贸易",
  rate: "利率",
  tech: "科技",
  company: "公司",
  disaster: "灾害",
  geopolitical: "地缘",
  other: "其他",
};

export function EventTypeTag({ type }: { type: EventType | string }) {
  const cls = TYPE_STYLE[type] ?? TYPE_STYLE.other;
  const label = TYPE_LABEL[type] ?? type;
  return (
    <span className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}
