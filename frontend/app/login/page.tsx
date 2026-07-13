"use client";

/** 登录页:用户名 + 密码,成功后 Set-Cookie 自动登录态,跳转首页。
 *
 * 客户端表单:复用 ui/Button、ui/Card,手写 input(复用 FilterBar 暗色 inputCls)。
 * 状态机 idle/loading/error(成功直接跳转无需 success 态)。无 toast 库,内联反馈。
 * 成功后 dispatchEvent("auth-change") 通知 SiteHeader 重取登录态。
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LogIn } from "lucide-react";

import { login } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const inputCls =
  "w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-fg)] outline-none transition focus:border-indigo-400/50 focus:bg-white/8 placeholder:text-[var(--color-fg-subtle)]";

type Phase = "idle" | "loading" | "error";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (phase === "loading") return;
    setPhase("loading");
    setError("");
    try {
      await login({ username, password });
      // 通知 SiteHeader 重取登录态
      window.dispatchEvent(new Event("auth-change"));
      router.push("/");
      router.refresh();
    } catch (err) {
      setPhase("error");
      const status = (err as Error & { status?: number }).status;
      setError(status === 401 ? "用户名或密码错误" : err instanceof Error ? err.message : "登录失败");
    }
  }

  return (
    <div className="mx-auto max-w-md py-12">
      <Card variant="glass" className="border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-[var(--color-fg)]">
            <LogIn className="h-5 w-5 text-indigo-400" />
            登录 EventAlpha
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1.5 text-xs text-[var(--color-fg-muted)]">
              用户名
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={inputCls}
                placeholder="请输入用户名"
                autoComplete="username"
                required
                minLength={1}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-xs text-[var(--color-fg-muted)]">
              密码
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                placeholder="请输入密码"
                autoComplete="current-password"
                required
                minLength={1}
              />
            </label>
            {phase === "error" && (
              <p className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                {error}
              </p>
            )}
            <Button type="submit" size="md" disabled={phase === "loading"}>
              {phase === "loading" ? "登录中..." : "登录"}
            </Button>
            <p className="text-center text-xs text-[var(--color-fg-subtle)]">
              还没有账号?{" "}
              <Link href="/register" className="text-indigo-400 transition hover:text-indigo-300">
                去注册
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}