/** API 客户端：封装后端三个事件接口的 fetch。
 *
 * Server Component 在 Node 端 fetch 必须用绝对 URL（相对路径 /api/... 无法解析），
 * 故服务端直连后端 BACKEND_URL；客户端（若有）走同源 /api/... 由 next.config.mjs
 * rewrites 代理。cache: "no-store" 保证每次请求打后端，避免陈旧数据。
 */

import type {
  CollectResponse,
  EventCard,
  EventDetail,
  EventListParams,
  EventOut,
  LoginRequest,
  RegisterRequest,
  StatsOut,
  TokenResponse,
  User,
} from "./types";

// auth cookie 名：与 backend/config/security.yaml 的 cookie_name 对齐
const AUTH_COOKIE_NAME = "ea_auth_token";

// 服务端用绝对后端地址（Node fetch 需要）；客户端用同源相对路径走 rewrites 代理
const API_BASE =
  typeof window === "undefined"
    ? `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api`
    : "/api";

/** 统一 GET：非 2xx 抛错并附带 status，404 由调用方按需转 notFound()。
 *  credentials: "include" 让浏览器在同源 /api 请求中带上 httpOnly auth cookie。 */
async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", credentials: "include" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`API ${path} 返回 ${res.status}: ${text}`);
    (err as Error & { status?: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<T>;
}

/** 统一 POST：可选 body，非 2xx 抛错并附带 status。
 *  credentials: "include" 确保跨域/同源请求都带 cookie；有 body 时设 JSON 头。 */
async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    cache: "no-store",
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`API ${path} 返回 ${res.status}: ${text}`);
    (err as Error & { status?: number }).status = res.status;
    throw err;
  }
  // 204 No Content（如 logout）无响应体，避免 res.json() 报错
  if (res.status === 204) return undefined as T;
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

/** GET /api/stats Dashboard 聚合统计（totals + 分布 + 趋势 + 重要事件流）。 */
export function fetchStats(): Promise<StatsOut> {
  return getJson<StatsOut>(`/stats`);
}

/** POST /api/jobs/collect 手动触发 RSS 采集（返回每个源的采集统计）。 */
export function triggerCollect(): Promise<CollectResponse> {
  return postJson<CollectResponse>(`/jobs/collect`);
}

// ===== 鉴权接口 =====

/** POST /api/auth/register 注册（成功后后端 Set-Cookie 自动登录）。 */
export function register(req: RegisterRequest): Promise<TokenResponse> {
  return postJson<TokenResponse>("/auth/register", req);
}

/** POST /api/auth/login 登录（后端 Set-Cookie）。 */
export function login(req: LoginRequest): Promise<TokenResponse> {
  return postJson<TokenResponse>("/auth/login", req);
}

/** POST /api/auth/logout 登出（清 cookie，无响应体返回 204）。 */
export async function logout(): Promise<void> {
  await postJson<void>("/auth/logout");
}

/** GET /api/auth/me 获取当前登录用户（客户端用）。
 *  走 /api 代理，浏览器自动带 cookie。未登录返回 null（吞 401，不抛错）。 */
export async function fetchMe(): Promise<User | null> {
  try {
    return await getJson<User>("/auth/me");
  } catch (e) {
    const status = (e as Error & { status?: number }).status;
    if (status === 401) return null;
    throw e;
  }
}

/** 服务端获取当前用户（Server Component 用）。
 *
 *  从 next/headers 的 cookies() 读 auth cookie，手动设 Cookie 头转发给后端绝对地址
 *  （Server Component 的 fetch 不会自动带浏览器 cookie，需显式转发）。未登录返回 null。
 *  动态 import next/headers 隔离客户端环境（客户端组件不触发此 import）。 */
export async function fetchMeServer(): Promise<User | null> {
  const { cookies } = await import("next/headers");
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  if (!token) return null;
  const backend = process.env.BACKEND_URL ?? "http://localhost:8000";
  const res = await fetch(`${backend}/api/auth/me`, {
    headers: { Cookie: `${AUTH_COOKIE_NAME}=${token}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json() as Promise<User>;
}
