/** 全局错误边界：必须是 Client Component，接收 error + reset。
 * 后端 5xx / 网络断开 / fetch 抛错时展示。 */

"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <h2 className="text-lg font-semibold text-red-700">加载出错了</h2>
        <p className="mt-2 break-words text-sm text-red-600">{error.message}</p>
        <p className="mt-1 text-xs text-red-400">
          请确认后端服务已启动（localhost:8000）。
        </p>
        <div className="mt-4 flex justify-center gap-3">
          <button
            onClick={reset}
            className="rounded bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            重试
          </button>
          <Link
            href="/"
            className="rounded border border-red-300 px-4 py-1.5 text-sm text-red-600 hover:bg-red-100"
          >
            返回首页
          </Link>
        </div>
      </div>
    </main>
  );
}
