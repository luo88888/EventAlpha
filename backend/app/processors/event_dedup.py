"""事件去重合并：基于标题字符 bigram 覆盖度的规则判定。

设计说明：
- 合并键 = event_type 相同 + 标题字符 bigram 覆盖度 ≥ THRESHOLD。
- 用字符级 bigram（不引分词依赖），对中英文都鲁棒：英文按字符对，中文按相邻字符对，
  均能捕捉"谁做了什么"的相似性。
- 相似度用「双向覆盖度最大值」max(|A∩B|/|A|, |A∩B|/|B|) 而非 Jaccard：
  真实新闻标题常一长一短（详略不同），Jaccard 的分母被长串拉大、对长度差敏感；
  覆盖度衡量"短串的核心 bigram 是否都在长串里"，对同一事件不同详略更鲁棒。
- 偏激进合并：宁可并多一点，避免重复生成大量相似事件卡片（呼应计划 4.2 节）。
- event_subject 不作合并键：LLM 对主体命名不稳定（"中国" vs "中国政府"会漏合并）。
"""

from __future__ import annotations

# 合并相似度阈值：标题字符 bigram Jaccard ≥ 该值视为同一事件
MERGE_THRESHOLD = 0.6


def _char_bigrams(text: str) -> set[str]:
    """生成字符级 bigram 集合。

    先归一化（去空白、转小写），再取相邻字符对。
    长度 < 2 的文本返回包含原串的单元素集合，避免短标题相似度恒为 0。

    Args:
        text: 待处理文本（标题）。

    Returns:
        bigram 字符串集合。
    """
    s = "".join(text.split()).lower()
    if len(s) < 2:
        return {s} if s else set()
    return {s[i : i + 2] for i in range(len(s) - 1)}


def title_similarity(a: str, b: str) -> float:
    """计算两个标题的字符 bigram 双向覆盖度。

    覆盖度 = max(|A∩B|/|A|, |A∩B|/|B|)：取"短串被长串包含"与"长串覆盖短串"的较大者。
    相比 Jaccard 对长度差更鲁棒，适合"同一事件、详略不同"的真实新闻标题。

    Args:
        a, b: 两个标题字符串。

    Returns:
        相似度，取值 [0.0, 1.0]；任一为空返回 0.0。
    """
    sa, sb = _char_bigrams(a), _char_bigrams(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    return max(inter / len(sa), inter / len(sb))


class MergeCandidate:
    """合并候选：既有 Event 或本批次已生成事件，提供标题与类型供判定。

    用轻量协议而非直接依赖 ORM 模型，便于在内存池（本批次新建事件）与
    DB 查询结果（既有 Event）间统一处理。
    """

    __slots__ = ("id", "event_title", "event_type")

    def __init__(self, id: int | None, event_title: str, event_type: str) -> None:
        self.id = id
        self.event_title = event_title
        self.event_type = event_type


def find_mergeable(
    title: str,
    event_type: str,
    candidates: list[MergeCandidate],
    threshold: float = MERGE_THRESHOLD,
) -> MergeCandidate | None:
    """在候选池中找可合并的事件。

    规则：event_type 相同 且 title_similarity ≥ threshold 的候选中取相似度最高者。
    遍历候选池（先本批次已生成，再 DB 既有），保留最高分命中。

    Args:
        title: 待判定事件的标题。
        event_type: 待判定事件的类型。
        candidates: 合并候选池（既有事件 + 本批次已生成事件）。
        threshold: 相似度阈值，默认 MERGE_THRESHOLD。

    Returns:
        命中的候选；无命中返回 None。
    """
    best: MergeCandidate | None = None
    best_score = threshold
    for cand in candidates:
        if cand.event_type != event_type:
            continue
        score = title_similarity(title, cand.event_title)
        if score >= best_score:
            best_score = score
            best = cand
    return best
