/** 全局 404 兜底。暗色霓虹风格。 */

import Link from "next/link";
import { Home, Radar } from "lucide-react";

import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-xl flex-col items-center justify-center text-center">
      <Radar className="mb-6 h-16 w-16 text-[var(--color-fg-subtle)] animate-[float_6s_ease-in-out_infinite]" strokeWidth={1.5} />
      <h1 className="text-gradient text-7xl font-extrabold tracking-tight">404</h1>
      <p className="mt-4 text-lg text-[var(--color-fg)]">页面不存在</p>
      <p className="mt-2 text-sm text-[var(--color-fg-muted)]">
        你访问的页面可能已被移除或链接有误
      </p>
      <Link href="/" className="mt-6">
        <Button variant="primary" size="md">
          <Home className="h-4 w-4" />
          返回控制台
        </Button>
      </Link>
    </div>
  );
}
