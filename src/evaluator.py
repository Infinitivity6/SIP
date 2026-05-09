"""问答系统评测模块。

评测维度：
    - **检索命中率（recall@k）**：检索片段是否覆盖期望关键词。
    - **生成准确率（accuracy）**：最终回答是否包含全部 must_have 关键词。
    - **生成查全率（key_coverage）**：回答覆盖到的关键词比例。
    - **响应时间**：每条问题的 query 总耗时，便于性能展示。

测试集格式见 ``eval/test_questions.json``。
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Iterable

from config import EVAL_DIR, EVAL_RESULT_DIR
from src.intent_classifier import classify
from src.prompt_templates import for_intent
from src.rag_engine import query, retrieve_context


DEFAULT_TEST_FILE = os.path.join(EVAL_DIR, "test_questions.json")


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #
@dataclass
class QuestionCase:
    id: str
    category: str
    question: str
    must_have: list[str]
    nice_to_have: list[str] = field(default_factory=list)
    reference_answer: str = ""


@dataclass
class CaseResult:
    id: str
    category: str
    question: str
    intent: str
    response: str
    context_recall: float
    answer_accuracy: float
    key_coverage: float
    elapsed_sec: float
    must_hits: list[str]
    must_miss: list[str]


@dataclass
class ReportSummary:
    total: int
    avg_accuracy: float
    avg_recall: float
    avg_coverage: float
    avg_latency: float
    by_category: dict[str, dict]


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def load_test_set(path: str = DEFAULT_TEST_FILE) -> list[QuestionCase]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [QuestionCase(**item) for item in raw]


def _hit_ratio(text: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    if not keywords:
        return 1.0, [], []
    hits, miss = [], []
    for kw in keywords:
        if kw and kw in text:
            hits.append(kw)
        else:
            miss.append(kw)
    return len(hits) / len(keywords), hits, miss


# --------------------------------------------------------------------------- #
# 单条评测
# --------------------------------------------------------------------------- #
def evaluate_case(case: QuestionCase, llm_call=None) -> CaseResult:
    intent = classify(case.question, llm_call=llm_call)
    strategy = for_intent(intent.label)

    t0 = time.time()
    response = query(
        case.question,
        mode=strategy.mode,
        top_k=strategy.top_k,
        chunk_top_k=strategy.chunk_top_k,
        user_prompt=strategy.user_prompt,
    )
    elapsed = time.time() - t0

    # 检索命中（拿原始上下文计算）
    try:
        context = retrieve_context(
            case.question,
            mode=strategy.mode,
            top_k=strategy.top_k,
            chunk_top_k=strategy.chunk_top_k,
        )
    except Exception:
        context = ""  # 无法获取上下文时置空，recall 自然为 0，不用净化后的 response 代替

    recall, _, _ = _hit_ratio(context, case.must_have + case.nice_to_have)
    accuracy, must_hits, must_miss = _hit_ratio(response, case.must_have)
    coverage, _, _ = _hit_ratio(response, case.must_have + case.nice_to_have)

    return CaseResult(
        id=case.id,
        category=case.category,
        question=case.question,
        intent=intent.label,
        response=response,
        context_recall=round(recall, 3),
        answer_accuracy=round(accuracy, 3),
        key_coverage=round(coverage, 3),
        elapsed_sec=round(elapsed, 2),
        must_hits=must_hits,
        must_miss=must_miss,
    )


# --------------------------------------------------------------------------- #
# 批量评测 & 报告
# --------------------------------------------------------------------------- #
def evaluate(cases: Iterable[QuestionCase], progress_cb=None, llm_call=None) -> tuple[list[CaseResult], ReportSummary]:
    cases = list(cases)
    results: list[CaseResult] = []
    for idx, c in enumerate(cases, 1):
        try:
            res = evaluate_case(c, llm_call=llm_call)
        except Exception as exc:  # noqa: BLE001
            res = CaseResult(
                id=c.id, category=c.category, question=c.question, intent="error",
                response=f"[评测失败] {exc}", context_recall=0.0,
                answer_accuracy=0.0, key_coverage=0.0, elapsed_sec=0.0,
                must_hits=[], must_miss=c.must_have,
            )
        results.append(res)
        if progress_cb:
            progress_cb(idx, len(cases), res)

    summary = _summarise(results)
    return results, summary


def _summarise(results: list[CaseResult]) -> ReportSummary:
    if not results:
        return ReportSummary(0, 0.0, 0.0, 0.0, 0.0, {})

    def _avg(field_name: str) -> float:
        return round(sum(getattr(r, field_name) for r in results) / len(results), 3)

    by_category: dict[str, list[CaseResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    cat_stats = {
        cat: {
            "count": len(rs),
            "accuracy": round(sum(r.answer_accuracy for r in rs) / len(rs), 3),
            "recall":   round(sum(r.context_recall  for r in rs) / len(rs), 3),
            "latency":  round(sum(r.elapsed_sec     for r in rs) / len(rs), 2),
        }
        for cat, rs in by_category.items()
    }

    return ReportSummary(
        total=len(results),
        avg_accuracy=_avg("answer_accuracy"),
        avg_recall=_avg("context_recall"),
        avg_coverage=_avg("key_coverage"),
        avg_latency=_avg("elapsed_sec"),
        by_category=cat_stats,
    )


def save_report(results: list[CaseResult], summary: ReportSummary, out_dir: str = EVAL_RESULT_DIR) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"eval_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": asdict(summary),
                "details": [asdict(r) for r in results],
                "generated_at": ts,
            },
            f, ensure_ascii=False, indent=2,
        )
    return out_path
