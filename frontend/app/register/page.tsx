"use client";

/** 注册页:用户名 + 密码 + 确认密码 + 可选邮箱,成功后自动登录跳首页。
 *
 * 客户端表单:复用 ui/Button、ui/Card,手写 input。前端基础校验
 * (用户名>=3、密码>=6、两次密码一致),后端做权威校验。
 * 状态机 idle/loading/error。成功后 dispatchEvent("auth-change") 通知 SiteHeader。
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { UserPlus } from "lucide-react";

import { register } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const inputCls =
  "w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-fg)] outline-none transition focus:border-indigo-400/50 focus:bg-white/8 placeholder:text-[var(--color-fg-subtle)]";

type Phase = "idle" | "loading" | "error";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (phase === "loading") return;
    // 前端基础校验
    if (username.trim().length < 3) {
      setPhase("error");
      setError("用户名至少 3 个字符");
      return;
    }
    if (password.length < 6) {
      setPhase("error");
      setError("密码至少 6 个字符");
      return;
    }
    if (password !== confirmPassword) {
      setPhase("error");
      setError("两次输入的密码不一致");
      return;
    }
    setPhase("loading");
    setError("");
    try {
      await register({
        username,
        password,
        email: email.trim() || undefined,
      });
      // 通知 SiteHeader 重取登录态
      window.dispatchEvent(new Event("auth-change"));
      router.push("/");
      router.refresh();
    } catch (err) {
      setPhase("error");
      const status = (err as Error & { status?: number }).status;
      if (status === 409) setError("用户名或邮箱已存在");
      else if (status === 422) setError("输入参数不合法");
      else setError(err instanceof Error ? err.message : "注册失败");
    }
  }

  return (
    <div className="mx-auto max-w-md py-12">
      <Card variant="glass" className="border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-[var(--color-fg)]">
            <UserPlus className="h-5 w-5 text-cyan-400" />
            注册 EventAlpha
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
                placeholder="3-64 个字符,不含空白"
                autoComplete="username"
                required
                minLength={3}
                maxLength={64}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-xs text-[var(--color-fg-muted)]">
              密码
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                placeholder="至少 6 个字符"
                autoComplete="new-password"
                required
                minLength={6}
                maxLength={128}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-xs text-[var(--color-fg-muted)]">
              确认密码
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={inputCls}
                placeholder="再次输入密码"
                autoComplete="new-password"
                required
                minLength={6}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-xs text-[var(--color-fg-muted)]">
              邮箱(可选)
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputCls}
                placeholder="选填,用于找回账号"
                autoComplete="email"
                maxLength={255}
              />
            </label>
            {phase === "error" && (
              <p className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                {error}
              </p>
            )}
            <Button type="submit" size="md" disabled={phase === "loading"}>
              {phase === "loading" ? "注册中..." : "注册并登录"}
            </Button>
            <p className="text-center text-xs text-[var(--color-fg-subtle)]">
              已有账号?{" "}
              <Link href="/login" className="text-indigo-400 transition hover:text-indigo-300">
                去登录
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}