"use client";

/** 手动触发 RSS 采集按钮（客户端组件）。

 * 放在 Dashboard 标题区"查看全部事件"旁。点击调 POST /api/jobs/collect，
 * 内联反馈 idle/loading/success/error 四态（不引入 toast 库，符合 MVP 轻量风格）。
 * 成功后 router.refresh() 让 Server Component 重取 fetchStats 刷新 KPI。
 */

import { useRouter } from "next/navigation";
import { useState } from "react";
import { RefreshCw, Zap } from "lucide-react";

import { triggerCollect } from "@/lib/api";
import { cn } from "@/lib/utils";

type Phase = "idle" | "loading" | "success" | "error";

export function CollectButton() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState<string>("");

  async function handleClick() {
    if (phase === "loading") return;
    setPhase("loading");
    setMessage("采集中...");
    try {
      const res = await triggerCollect();
      setPhase("success");
      setMessage(`采集完成：入库 ${res.total_new} 条`);
      // 让 Server Component 重新执行，刷新 KPI/图表数据
      router.refresh();
    } catch (e) {
      setPhase("error");
      setMessage(`采集失败：${e instanceof Error ? e.message : "未知错误"}`);
    }
    // 3 秒后回 idle（无论成功/失败）
    setTimeout(() => {
      setPhase("idle");
      setMessage("");
    }, 3000);
  }

  const isSuccess = phase === "success";
  const isError = phase === "error";

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={phase === "loading"}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-sm font-medium transition-all duration-200",
        "disabled:cursor-not-allowed disabled:opacity-50",
        // 默认 outline 风格，匹配旁边"查看全部事件"Link
        phase === "idle" &&
          "border-white/10 bg-white/5 text-[var(--color-fg)] hover:border-indigo-400/40 hover:bg-white/10",
        phase === "loading" && "border-white/10 bg-white/5 text-[var(--color-fg-muted)]",
        isSuccess && "border-emerald-400/40 bg-emerald-500/10 text-emerald-300",
        isError && "border-rose-400/40 bg-rose-500/10 text-rose-300",
      )}
    >
      {phase === "loading" ? (
        <RefreshCw className="h-4 w-4 animate-spin" />
      ) : (
        <Zap className={cn("h-4 w-4", phase === "idle" && "text-cyan-300")} />
      )}
      <span>{message || "手动采集"}</span>
    </button>
  );
}
