"""API 限流测试：并发打 N 个请求，统计成功/限流/失败数。

用法：
    python scripts/test_rate_limit.py --base-url https://api.deepseek.com/v1 \
        --api-key sk-xxx --model deepseek-chat --concurrency 5 --total 20

也支持小米等 OpenAI 兼容 API：
    python scripts/test_rate_limit.py --base-url https://api.mimo.xiaomi.com/v1 \
        --api-key sk-xxx --model MiMo --concurrency 3 --total 10
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx


def send_request(
    client: httpx.Client, base_url: str, api_key: str, model: str, idx: int
) -> dict:
    """发送单个请求，返回 {idx, status, elapsed}。"""
    start = time.monotonic()
    try:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "say ok"}],
                "max_tokens": 5,
            },
            timeout=30,
        )
        elapsed = time.monotonic() - start
        return {"idx": idx, "status": resp.status_code, "elapsed": round(elapsed, 2)}
    except Exception as e:
        elapsed = time.monotonic() - start
        return {"idx": idx, "status": "error", "elapsed": round(elapsed, 2), "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="API 限流测试")
    parser.add_argument("--base-url", required=True, help="API base URL (不含 /chat/completions)")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--model", required=True, help="模型名")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数 (默认 5)")
    parser.add_argument("--total", type=int, default=20, help="总请求数 (默认 20)")
    parser.add_argument("--interval", type=float, default=0, help="请求间隔秒数 (默认 0，即无间隔)")
    args = parser.parse_args()

    print(f"测试配置: {args.base_url} | model={args.model} | 并发={args.concurrency} | 总数={args.total}")
    print("-" * 60)

    results = []
    start_all = time.monotonic()

    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = []
            for i in range(args.total):
                futures.append(executor.submit(send_request, client, args.base_url, args.api_key, args.model, i))
                if args.interval > 0:
                    time.sleep(args.interval)

            for future in as_completed(futures):
                r = future.result()
                results.append(r)
                status = r["status"]
                mark = "✓" if status == 200 else "✗"
                print(f"  [{mark}] #{r['idx']:>3}  status={status}  {r['elapsed']}s")

    total_time = time.monotonic() - start_all

    # 统计
    ok = sum(1 for r in results if r["status"] == 200)
    rate_limited = sum(1 for r in results if r["status"] == 429)
    errors = sum(1 for r in results if r["status"] not in (200, 429))
    avg_latency = sum(r["elapsed"] for r in results) / len(results) if results else 0

    print("-" * 60)
    print(f"结果: 成功={ok}  限流(429)={rate_limited}  其他错误={errors}  总耗时={total_time:.1f}s")
    print(f"平均延迟: {avg_latency:.2f}s")
    if ok > 0:
        print(f"有效吞吐: {ok / total_time:.2f} req/s")


if __name__ == "__main__":
    main()
