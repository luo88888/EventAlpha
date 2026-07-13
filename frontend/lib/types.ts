/** 前端 TypeScript 类型，对齐后端 Pydantic schema（字段名逐字一致）。
 *
 * 来源：backend/app/schemas/event.py
 * 后端时间字段为 UTC naive datetime，序列化为无时区后缀的 ISO 串（如 2026-06-24T12:01:33）。
 */

// GET /api/events 单条事件
export interface EventOut {
  id: number;
  event_id: string; // 展示码 EVT_20260624_001
  event_title: string;
  event_type: string; // policy/trade/rate/tech/company/disaster/geopolitical/other
  event_subject: string | null;
  event_time: string | null; // ISO 8601
  summary: string | null;
  source_count: number;
  status: string;
  created_at: string; // ISO 8601
  // 列表端点 LEFT JOIN event_analysis 填充（无分析时 null），供列表卡片展示等级
  importance_level: string | null; // S/A/B/C
  importance_score: number | null;
}

// 事件来源项（跨表：source_name 来自 event_sources，其余来自 raw_news）
export interface EventSourceOut {
  source_name: string | null;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
}

// 分析块（详情页可空：null 表示事件尚未生成分析）
export interface AnalysisOut {
  importance_score: number;
  importance_level: string; // S/A/B/C
  affected_industries: string[];
  affected_assets: string[];
  causal_chain: string[];
  positive_factors: string[];
  negative_factors: string[];
  risk_warning: string | null;
  model_version: string | null;
  created_at: string;
}

// GET /api/events/{id} 详情
export interface EventDetail extends EventOut {
  sources: EventSourceOut[];
  analysis: AnalysisOut | null;
}

// GET /api/events/{id}/card 卡片（扁平，title←event_title，无分析时降级）
export interface EventCard {
  event_id: string;
  title: string;
  event_type: string;
  summary: string | null;
  source_count: number;
  importance_level: string | null;
  importance_score: number | null;
  affected_industries: string[];
  affected_assets: string[];
  causal_chain: string[];
  positive_factors: string[];
  negative_factors: string[];
  risk_warning: string | null;
}

// 列表查询参数
export interface EventListParams {
  event_type?: string;
  importance_level?: string; // S/A/B/C
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}

// ===== GET /api/stats Dashboard 聚合统计（对齐 backend/app/schemas/stats.py）=====

export interface TypeCount {
  type: string;
  count: number;
}

export interface LevelCount {
  level: string; // S/A/B/C/none（none=尚未分析）
  count: number;
}

export interface TrendPoint {
  date: string; // YYYY-MM-DD
  count: number;
}

export interface SourceCount {
  source: string;
  count: number;
}

export interface TopEvent {
  id: number;
  event_id: string;
  event_title: string;
  event_type: string;
  importance_level: string | null;
  importance_score: number | null;
  created_at: string; // ISO 8601
}

export interface StatsOut {
  totals: Record<string, number>; // events / analyzed / sources / raw_news
  type_distribution: TypeCount[];
  level_distribution: LevelCount[];
  trend: TrendPoint[];
  source_distribution: SourceCount[];
  top_events: TopEvent[];
}

// event_type 枚举全集（由后端 Prompt 约束），筛选器下拉用
export const EVENT_TYPES = [
  "policy",
  "trade",
  "rate",
  "tech",
  "company",
  "disaster",
  "geopolitical",
  "other",
] as const;
export type EventType = (typeof EVENT_TYPES)[number];

// importance_level 等级
export const IMPORTANCE_LEVELS = ["S", "A", "B", "C"] as const;
export type ImportanceLevel = (typeof IMPORTANCE_LEVELS)[number];

// ===== POST /api/jobs/collect 采集响应（对齐 backend/app/schemas/raw_news.py）=====

export interface CollectResult {
  source: string;
  fetched: number;
  new: number;
  skipped: number;
}

export interface CollectResponse {
  results: CollectResult[];
  total_fetched: number;
  total_new: number;
  total_skipped: number;
}

// ===== 鉴权（对齐 backend/app/schemas/auth.py）=====

export interface User {
  id: number;
  username: string;
  email: string | null;
  created_at: string; // ISO 8601
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  user: User;
  token: string;
}
