/** 全局 404 兜底。 */

import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[50vh] max-w-4xl flex-col items-center justify-center px-4 text-center">
      <h1 className="text-3xl font-bold text-gray-800">404</h1>
      <p className="mt-2 text-gray-600">页面不存在</p>
      <Link
        href="/"
        className="mt-4 rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
      >
        返回首页
      </Link>
    </main>
  );
}
