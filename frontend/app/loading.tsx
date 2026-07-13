/** 全局加载骨架屏：暗色卡片流光占位。
 *
 * 列表页/详情页通用骨架。Server Component（loading.tsx 无需客户端）。
 */

import { Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="space-y-6">
      {/* 标题骨架 */}
      <div className="flex items-end justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-32 rounded-xl" />
      </div>

      {/* 筛选器骨架 */}
      <Skeleton className="h-20 w-full rounded-2xl" />

      {/* 列表骨架 */}
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-xl" />
        ))}
      </div>

      {/* 分页骨架 */}
      <div className="flex justify-center py-4">
        <Skeleton className="h-10 w-64 rounded-lg" />
      </div>
    </div>
  );
}
