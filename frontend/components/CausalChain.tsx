/** 因果链：竖向编号步骤（左边框 + 圆形序号）。 */

export function CausalChain({ steps }: { steps: string[] }) {
  if (!steps.length) {
    return <p className="text-sm text-gray-500">暂无因果链</p>;
  }
  return (
    <ol className="space-y-3 border-l-2 border-blue-200 pl-5">
      {steps.map((s, i) => (
        <li key={i} className="relative text-sm text-gray-800">
          <span className="absolute -left-[1.6rem] flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white">
            {i + 1}
          </span>
          {s}
        </li>
      ))}
    </ol>
  );
}
