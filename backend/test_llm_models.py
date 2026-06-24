"""LLM 模型测试脚本。

测试三种模型的聊天能力和结构化输出能力：
- deepseek: deepseek-v4-flash
- qwen: qwen-plus
- openai: gpt-5.4

用法：
    cd backend
    python test_llm_models.py

前提条件：
    .env 中已配置对应提供方的 API Key。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# 确保 backend/ 为工作目录，以便 config/ 与 .env 正确解析
BACKEND_DIR = Path(__file__).resolve().parent
if Path.cwd() != BACKEND_DIR:
    print(f"[信息] 切换工作目录至 {BACKEND_DIR}")
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.llm import create_model, create_structured_model


# ── 结构化输出 Schema ────────────────────────────────────────


class CompanyInfo(BaseModel):
    """用于测试结构化输出的 Pydantic 模型。"""

    name: str = Field(description="公司名称")
    industry: str = Field(description="所属行业")
    founded_year: int = Field(description="成立年份")
    is_public: bool = Field(description="是否已上市")
    key_products: list[str] = Field(description="核心产品 / 业务线（1–3 个）")


# ── 被测试模型列表 ───────────────────────────────────────────
#
# 说明：
#   deepseek-v4-flash 是推理模型，默认开启 thinking 模式。
#   thinking 模式下 DeepSeek API 不支持 tool_choice（结构化输出底层依赖 tool_choice），
#   因此需要通过 extra_body 传入 {"thinking": {"type": "disabled"}} 关闭思考模式。
#   extra_body 由 langchain_openai.BaseChatOpenAI 自动嵌套在请求体的 extra_body 字段中，
#   仅影响本次请求；普通聊天无需关闭 thinking。
#
#   ⚠ 注意：不能用 model_kwargs，它会把参数合并到 API 请求的顶层，
#   导致 Completions.create() 收到不认识的 thinking 参数而报错。
#
#   你的工作代码能通过是因为用了 deepseek-chat（非推理模型，无 thinking 模式）。

MODELS: list[dict[str, str]] = [
    {
        "provider": "deepseek",
        "model_name": "deepseek-v4-flash",
        # 推理模型需关闭 thinking 才能使用 structured output
        "structured_kwargs": {"extra_body": {"thinking": {"type": "disabled"}}},
    },
    {"provider": "qwen", "model_name": "qwen-plus"},
    {"provider": "openai", "model_name": "gpt-5.4"},
]

# ── 测试消息 ─────────────────────────────────────────────────

CHAT_MESSAGE = "用一句话介绍阿里巴巴这家公司。"
STRUCTURED_MESSAGE = "请用中文介绍阿里巴巴这家公司的基本信息。（name、industry、founded_year、is_public、key_products）"


# ── 辅助函数 ─────────────────────────────────────────────────


def print_header(text: str) -> None:
    """打印带分隔线的标题。"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_result(label: str, value: Any) -> None:
    """格式化打印结果。"""
    if isinstance(value, BaseModel):
        print(f"  ✅ {label}:")
        print(f"     {value.model_dump_json(indent=4, ensure_ascii=False)}")
    else:
        print(f"  ✅ {label}: {value}")


def print_error(label: str, error: Exception) -> None:
    """格式化打印错误。"""
    msg = str(error)
    # 截断过长的错误信息（如 API 返回的大段 HTML）
    if len(msg) > 300:
        msg = msg[:300] + "…(已截断)"
    print(f"  ❌ {label}: {type(error).__name__}: {msg}")


def test_chat(provider: str, model_name: str) -> str | None:
    """测试普通对话模型。

    Returns:
        模型返回的文本内容；失败返回 None。
    """
    label = f"{provider}/{model_name} 聊天"
    try:
        model = create_model(provider=provider, model_name=model_name, temperature=0.7)
        response = model.invoke(CHAT_MESSAGE)
        content = response.content if hasattr(response, "content") else str(response)
        print_result(label, content)
        return content
    except Exception as exc:
        print_error(label, exc)
        return None


def test_structured(provider: str, model_name: str, **extra_kwargs: Any) -> CompanyInfo | None:
    """测试结构化输出模型。

    Args:
        provider: 提供方。
        model_name: 模型名称。
        **extra_kwargs: 透传给 create_model 的额外参数（如 model_kwargs）。

    Returns:
        解析后的 CompanyInfo 实例；失败返回 None。
    """
    label = f"{provider}/{model_name} 结构化输出"
    try:
        structured_model = create_structured_model(
            CompanyInfo,
            provider=provider,
            model_name=model_name,
            temperature=0.3,
            **extra_kwargs,
        )
        result = structured_model.invoke(STRUCTURED_MESSAGE)
        print_result(label, result)
        return result
    except Exception as exc:
        print_error(label, exc)
        return None


# ── 主流程 ───────────────────────────────────────────────────


def main() -> None:
    print_header("LLM 模型测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"聊天消息: {CHAT_MESSAGE}")
    print(f"结构化消息: {STRUCTURED_MESSAGE}")

    summary: list[dict[str, Any]] = []

    for entry in MODELS:
        provider = entry["provider"]
        model_name = entry["model_name"]

        print_header(f"测试 {provider} / {model_name}")

        start = time.perf_counter()
        chat_result = test_chat(provider, model_name)
        chat_elapsed = time.perf_counter() - start

        start = time.perf_counter()
        structured_result = test_structured(
            provider, model_name, **entry.get("structured_kwargs", {})
        )
        structured_elapsed = time.perf_counter() - start

        summary.append(
            {
                "provider": provider,
                "model_name": model_name,
                "聊天": "✅" if chat_result else "❌",
                "聊天耗时": f"{chat_elapsed:.2f}s",
                "结构化输出": "✅" if structured_result else "❌",
                "结构化耗时": f"{structured_elapsed:.2f}s",
            }
        )

    # ── 汇总表格 ──────────────────────────────────────────────

    print_header("测试汇总")

    # 列宽
    col_widths = {
        "provider": 12,
        "model_name": 22,
        "聊天": 6,
        "聊天耗时": 10,
        "结构化输出": 10,
        "结构化耗时": 10,
    }

    # 表头
    header = (
        f"  {'提供方':<{col_widths['provider']}}"
        f"{'模型':<{col_widths['model_name']}}"
        f"{'聊天':<{col_widths['聊天']}}"
        f"{'聊天耗时':<{col_widths['聊天耗时']}}"
        f"{'结构化':<{col_widths['结构化输出']}}"
        f"{'结构化耗时':<{col_widths['结构化耗时']}}"
    )
    print(header)
    print(f"  {'-' * (sum(col_widths.values()) + 5)}")

    for row in summary:
        line = (
            f"  {row['provider']:<{col_widths['provider']}}"
            f"{row['model_name']:<{col_widths['model_name']}}"
            f"{row['聊天']:<{col_widths['聊天']}}"
            f"{row['聊天耗时']:<{col_widths['聊天耗时']}}"
            f"{row['结构化输出']:<{col_widths['结构化输出']}}"
            f"{row['结构化耗时']:<{col_widths['结构化耗时']}}"
        )
        print(line)

    # 统计
    chat_ok = sum(1 for r in summary if r["聊天"] == "✅")
    structured_ok = sum(1 for r in summary if r["结构化输出"] == "✅")
    total = len(summary)
    print(f"\n  聊天通过: {chat_ok}/{total}  |  结构化输出通过: {structured_ok}/{total}")

    if chat_ok + structured_ok == total * 2:
        print("\n🎉 全部测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查 API Key 配置和网络连接。")


if __name__ == "__main__":
    main()
