/** 详情页 404：事件不存在或已被删除（后端 404 → notFound() 触发）。 */

import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <h2 className="text-lg font-semibold text-gray-700">事件不存在</h2>
        <p className="mt-2 text-sm text-gray-500">
          该事件可能已被删除，或 ID 有误。
        </p>
        <Link
          href="/"
          className="mt-4 inline-block rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          返回事件列表
        </Link>
      </div>
    </main>
  );
}
