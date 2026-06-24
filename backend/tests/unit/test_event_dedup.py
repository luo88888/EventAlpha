"""事件去重合并判定单测。

覆盖 processors/event_dedup.py 的 title_similarity 与 find_mergeable：
- 同类型高相似 → 合并
- 不同类型 → 不合并
- 低相似 → 不合并（新建）
- event_subject 不参与判定
"""

from __future__ import annotations

from app.processors.event_dedup import (
    MERGE_THRESHOLD,
    MergeCandidate,
    find_mergeable,
    title_similarity,
)


def test_similarity_identical() -> None:
    assert title_similarity("美联储宣布加息25个基点", "美联储宣布加息25个基点") == 1.0


def test_similarity_high_overlap() -> None:
    # 同一关税事件，两篇新闻标题措辞不同但高度重叠
    a = "美国宣布对华加征关税"
    b = "美国对华加征关税政策正式宣布"
    assert title_similarity(a, b) >= MERGE_THRESHOLD


def test_similarity_unrelated() -> None:
    assert title_similarity("美联储宣布加息25个基点", "某公司发布新款手机产品") < 0.3


def test_similarity_empty() -> None:
    assert title_similarity("", "任意标题") == 0.0
    assert title_similarity("任意标题", "") == 0.0


def test_find_mergeable_same_type_high_sim() -> None:
    candidates = [
        MergeCandidate(id=1, event_title="美国宣布对华加征关税", event_type="trade"),
    ]
    hit = find_mergeable("美国对华加征关税政策正式宣布", "trade", candidates)
    assert hit is not None
    assert hit.id == 1


def test_find_mergeable_different_type_no_merge() -> None:
    # 标题几乎相同但类型不同（trade vs policy），不应合并
    candidates = [
        MergeCandidate(id=1, event_title="美国宣布对华加征关税", event_type="policy"),
    ]
    assert find_mergeable("美国宣布对华加征关税", "trade", candidates) is None


def test_find_mergeable_low_sim_no_merge() -> None:
    candidates = [
        MergeCandidate(id=1, event_title="美联储宣布加息25个基点", event_type="rate"),
    ]
    assert find_mergeable("美联储主席发表讲话", "rate", candidates) is None


def test_find_mergeable_picks_best_among_multiple() -> None:
    # 候选池含一个中等相似、一个高相似，应命中高相似者
    candidates = [
        MergeCandidate(id=1, event_title="美国发布新能源补贴政策细则", event_type="policy"),
        MergeCandidate(id=2, event_title="美国新能源补贴政策正式发布", event_type="policy"),
    ]
    hit = find_mergeable("美国新能源补贴政策正式发布并实施", "policy", candidates)
    assert hit is not None
    assert hit.id == 2
