/** 重要性等级徽章：S/A/B/C 配色，可选展示分数。 */

const LEVEL_STYLE: Record<string, string> = {
  S: "bg-red-100 text-red-700 border-red-300",
  A: "bg-orange-100 text-orange-700 border-orange-300",
  B: "bg-blue-100 text-blue-700 border-blue-300",
  C: "bg-gray-100 text-gray-600 border-gray-300",
};

export function ImportanceBadge({
  level,
  score,
}: {
  level: string;
  score?: number | null;
}) {
  const cls = LEVEL_STYLE[level] ?? LEVEL_STYLE.C;
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-sm font-semibold ${cls}`}
    >
      {level}级{score != null ? ` · ${score}分` : ""}
    </span>
  );
}
