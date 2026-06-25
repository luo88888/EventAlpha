/** 全局加载占位：Server Component fetch 期间由 Suspense 自动展示。 */

export default function Loading() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="flex items-center gap-3 text-gray-500">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500" />
        加载中…
      </div>
    </div>
  );
}
