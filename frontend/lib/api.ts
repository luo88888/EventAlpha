/** API 客户端：封装后端三个事件接口的 fetch。
 *
 * Server Component 在 Node 端 fetch 必须用绝对 URL（相对路径 /api/... 无法解析），
 * 故服务端直连后端 BACKEND_URL；客户端（若有）走同源 /api/... 由 next.config.mjs
 * rewrites 代理。cache: "no-store" 保证每次请求打后端，避免陈旧数据。
 */

import type {
  EventCard,
  EventDetail,
  EventListParams,
  EventOut,
} from "./types";

// 服务端用绝对后端地址（Node fetch 需要）；客户端用同源相对路径走 rewrites 代理
const API_BASE =
  typeof window === "undefined"
    ? `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api`
    : "/api";

/** 统一 GET：非 2xx 抛错并附带 status，404 由调用方按需转 notFound()。 */
async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`API ${path} 返回 ${res.status}: ${text}`);
    (err as Error & { status?: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<T>;
}

/** GET /api/events 事件列表（支持筛选 + 分页）。 */
export function fetchEvents(params: EventListParams = {}): Promise<EventOut[]> {
  const qs = new URLSearchParams();
  if (params.event_type) qs.set("event_type", params.event_type);
  if (params.importance_level) qs.set("importance_level", params.importance_level);
  if (params.start_time) qs.set("start_time", params.start_time);
  if (params.end_time) qs.set("end_time", params.end_time);
  qs.set("limit", String(params.limit ?? 20));
  qs.set("offset", String(params.offset ?? 0));
  return getJson<EventOut[]>(`/events?${qs.toString()}`);
}

/** GET /api/events/{id} 事件详情（含 sources + analysis）。 */
export function fetchEventDetail(id: number): Promise<EventDetail> {
  return getJson<EventDetail>(`/events/${id}`);
}

/** GET /api/events/{id}/card 事件卡片（扁平降级视图）。
 * 详情页用 fetchEventDetail 已含 analysis，本函数保留供纯卡片视图/调试。 */
export function fetchEventCard(id: number): Promise<EventCard> {
  return getJson<EventCard>(`/events/${id}/card`);
}
