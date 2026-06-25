/** 无分析占位：事件尚未生成分析时（Day 4 推理分析层产物）显示。 */

export function EmptyAnalysis() {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center">
      <p className="text-base font-medium text-gray-600">该事件暂未生成分析</p>
      <p className="mt-2 text-sm text-gray-400">
        分析由推理分析层生成，事件入库后稍后自动补充。
      </p>
    </div>
  );
}
