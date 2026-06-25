/** 正面/负面因素列表（复用，variant 控制配色）。 */

export function FactorList({
  items,
  variant,
  title,
}: {
  items: string[];
  variant: "positive" | "negative";
  title: string;
}) {
  if (!items.length) return null;
  const dot = variant === "positive" ? "bg-green-500" : "bg-red-500";
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-gray-700">{title}</h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
