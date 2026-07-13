"use client";

/** 全局顶部导航:品牌 logo + 导航 + 登录态 + 实时状态指示。
 *
 * 客户端组件:用 usePathname 高亮当前页;useEffect 挂载时调 fetchMe() 获取登录态,
 * 监听自定义 "auth-change" 事件(login/register/logout 后 dispatch)重取登录态。
 * sticky 吸顶 + 毛玻璃。loaded 标志避免 SSR/CSR 闪烁。
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Radar, User as UserIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchMe, logout } from "@/lib/api";
import type { User } from "@/lib/types";

const NAV = [
  { href: "/", label: "控制台" },
  { href: "/events", label: "事件库" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const [user, setUser] = useState<User | null>(null);
  const [loaded, setLoaded] = useState(false);

  // 挂载时取登录态
  useEffect(() => {
    let alive = true;
    (async () => {
      const u = await fetchMe();
      if (alive) {
        setUser(u);
        setLoaded(true);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // 监听 auth-change 事件,login/register/logout 后重取登录态
  useEffect(() => {
    const handler = async () => {
      setUser(await fetchMe());
    };
    window.addEventListener("auth-change", handler);
    return () => window.removeEventListener("auth-change", handler);
  }, []);

  async function handleLogout() {
    await logout();
    setUser(null);
    window.dispatchEvent(new Event("auth-change"));
    // 整页刷新确保 cookie 丢弃 + 重置所有 client state
    window.location.href = "/";
  }

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 glass-strong">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 sm:px-6">
        {/* 品牌 */}
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-500 shadow-lg shadow-indigo-500/30 transition-transform group-hover:scale-105">
            <Radar className="h-5 w-5 text-white" strokeWidth={2.2} />
            <span className="absolute inset-0 rounded-xl ring-1 ring-white/20" />
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-base font-bold tracking-tight text-gradient">
              EventAlpha
            </span>
            <span className="text-[10px] text-[var(--color-fg-subtle)]">
              事件驱动投研
            </span>
          </span>
        </Link>

        {/* 导航 */}
        <nav className="flex items-center gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors",
                isActive(item.href)
                  ? "text-[var(--color-fg)]"
                  : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]",
              )}
            >
              {item.label}
              {isActive(item.href) && (
                <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-gradient-to-r from-indigo-400 to-cyan-400" />
              )}
            </Link>
          ))}
        </nav>

        {/* 右侧:登录态 + 实时状态 */}
        <div className="ml-auto flex items-center gap-3">
          {/* 登录态:loaded 后渲染,避免 SSR/CSR 闪烁 */}
          {loaded &&
            (user ? (
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--color-fg-muted)]">
                  <UserIcon className="h-3.5 w-3.5 text-indigo-400" />
                  {user.username}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  title="登出"
                  className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-[var(--color-fg-muted)] transition hover:border-rose-400/40 hover:text-rose-300"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  登出
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-medium text-[var(--color-fg-muted)] transition hover:border-indigo-400/40 hover:text-[var(--color-fg)]"
              >
                登录
              </Link>
            ))}

          {/* 实时状态:sm 以上显示,登录态存在时缩小 */}
          <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 sm:flex">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-xs text-[var(--color-fg-muted)]">实时监控中</span>
          </span>
        </div>
      </div>
    </header>
  );
}