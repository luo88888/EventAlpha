import type { Metadata } from "next";
import "./globals.css";

import { SiteHeader } from "@/components/SiteHeader";
import { ComplianceBanner } from "@/components/ComplianceBanner";

export const metadata: Metadata = {
  title: "EventAlpha · 事件驱动投研控制台",
  description: "热点事件驱动的投资研究辅助决策平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen bg-[var(--color-bg)] text-[var(--color-fg)] antialiased">
        <SiteHeader />
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">{children}</main>
        <footer className="mx-auto max-w-7xl px-4 pb-8 sm:px-6">
          <ComplianceBanner />
          <p className="mt-4 text-center text-xs text-[var(--color-fg-subtle)]">
            EventAlpha · 热点事件驱动投资研究 MVP · 仅供事件研究，不构成投资建议
          </p>
        </footer>
      </body>
    </html>
  );
}
