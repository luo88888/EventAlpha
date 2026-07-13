/** 详情页 404：事件不存在或已被删除（后端 404 → notFound() 触发）。 */

import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";

import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl">
      <div className="relative overflow-hidden rounded-2xl border border-white/8 bg-[var(--color-panel)]/60 p-8 text-center backdrop-blur-sm">
        <SearchX className="mx-auto mb-4 h-12 w-12 text-[var(--color-fg-subtle)]" strokeWidth={1.6} />
        <h2 className="text-xl font-bold text-[var(--color-fg)]">事件不存在</h2>
        <p className="mt-2 text-sm text-[var(--color-fg-muted)]">
          该事件可能已被删除，或 ID 有误。
        </p>
        <Link href="/events" className="mt-6 inline-block">
          <Button variant="secondary" size="md">
            <ArrowLeft className="h-4 w-4" />
            返回事件库
          </Button>
        </Link>
        <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-indigo-500/10 blur-3xl" />
      </div>
    </div>
  );
}
