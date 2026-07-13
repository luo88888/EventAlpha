/** 全局错误边界：必须是 Client Component，接收 error + reset。
 * 后端 5xx / 网络断开 / fetch 抛错时展示。暗色风格。
 */

"use client";

import Link from "next/link";
import { AlertCircle, Home, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto max-w-xl">
      <div className="relative overflow-hidden rounded-2xl border border-rose-400/20 bg-gradient-to-br from-rose-500/10 to-orange-500/5 p-8 text-center">
        <AlertCircle className="mx-auto mb-4 h-12 w-12 text-rose-400" strokeWidth={1.8} />
        <h2 className="text-xl font-bold text-[var(--color-fg)]">加载出错了</h2>
        <p className="mt-3 break-words text-sm text-rose-200/80">{error.message}</p>
        <p className="mt-2 text-xs text-[var(--color-fg-subtle)]">
          请确认后端服务已启动（默认 http://localhost:8000）。
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Button onClick={reset} variant="primary" size="md">
            <RefreshCw className="h-4 w-4" />
            重试
          </Button>
          <Link href="/">
            <Button variant="secondary" size="md">
              <Home className="h-4 w-4" />
              返回首页
            </Button>
          </Link>
        </div>
        {error.digest && (
          <p className="mt-4 text-[10px] text-[var(--color-fg-subtle)]">
            错误编号 {error.digest}
          </p>
        )}
        <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-rose-500/10 blur-3xl" />
      </div>
    </div>
  );
}
