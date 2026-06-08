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
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime for optional judge mode
    OpenAI = None

from config import (
    API_KEY,
    BASE_URL,
    EVAL_DIR,
    EVAL_ENABLE_LLM_JUDGE,
    EVAL_JUDGE_MAX_CONTEXT_CHARS,
    EVAL_JUDGE_MODELS,
    EVAL_JUDGE_TIMEOUT,
    EVAL_RESULT_DIR,
)
from src.intent_classifier import classify
from src.prompt_templates import for_intent


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
    answer_points: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)


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
    reference_answer: str = ""
    judge_score: float | None = None
    judge_correctness: float | None = None
    judge_completeness: float | None = None
    judge_faithfulness: float | None = None
    judge_relevance: float | None = None
    judge_safety: float | None = None
    judge_reason: str = ""
    judge_models: list[str] = field(default_factory=list)
    judge_details: list[dict] = field(default_factory=list)
    judge_elapsed_sec: float = 0.0


@dataclass
class ReportSummary:
    total: int
    avg_accuracy: float
    avg_recall: float
    avg_coverage: float
    avg_latency: float
    by_category: dict[str, dict]
    avg_judge_score: float | None = None
    avg_judge_correctness: float | None = None
    avg_judge_completeness: float | None = None
    avg_judge_faithfulness: float | None = None
    avg_judge_relevance: float | None = None
    avg_judge_safety: float | None = None


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def load_test_set(path: str = DEFAULT_TEST_FILE) -> list[QuestionCase]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    allowed = set(QuestionCase.__dataclass_fields__)
    return [QuestionCase(**{k: v for k, v in item.items() if k in allowed}) for item in raw]


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


def _round_or_none(value: float | None, digits: int = 3) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _compact_context_for_judge(context: str) -> str:
    """Extract retrieved chunks for judge prompts, falling back to raw context."""
    if not context:
        return ""

    try:
        from src.rag_engine import parse_context_sources
    except Exception:  # noqa: BLE001
        return context[:EVAL_JUDGE_MAX_CONTEXT_CHARS]

    sources = parse_context_sources(context)
    chunks = sources.get("chunks") or []
    if chunks:
        lines: list[str] = []
        for idx, chunk in enumerate(chunks[:10], 1):
            if not isinstance(chunk, dict):
                continue
            ref_id = chunk.get("reference_id", "?")
            content = str(chunk.get("content") or chunk.get("raw") or "").strip()
            if content:
                lines.append(f"[片段{idx} | 来源{ref_id}] {content}")
        compact = "\n".join(lines).strip()
        if compact:
            return compact[:EVAL_JUDGE_MAX_CONTEXT_CHARS]

    return context[:EVAL_JUDGE_MAX_CONTEXT_CHARS]


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.S | re.I)
    if fence:
        cleaned = fence.group(1)
    else:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match:
            cleaned = match.group(0)

    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _normalise_dimension_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if score > 10:
        score = score / 100.0
    elif score > 5:
        score = score / 10.0
    elif score > 1:
        score = score / 5.0
    return max(0.0, min(1.0, score))


def _normalise_overall_score(value, dimensions: dict[str, float]) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = (
            dimensions["correctness"] * 0.30
            + dimensions["completeness"] * 0.20
            + dimensions["faithfulness"] * 0.25
            + dimensions["relevance"] * 0.15
            + dimensions["safety"] * 0.10
        )
        return max(0.0, min(1.0, score))

    if score > 10:
        score = score / 100.0
    elif score > 5:
        score = score / 10.0
    elif score > 1:
        score = score / 5.0
    return max(0.0, min(1.0, score))


_JUDGE_SYSTEM_PROMPT = """你是一个严谨的中文医疗问答评测员。
你只评估答案质量，不提供新的医疗建议。评分必须基于题目、参考答案、评分要点、检索上下文和被评回答。
请特别关注医学事实、是否忠实于检索上下文、是否有危险建议。"""


def _build_judge_prompt(case: QuestionCase, response: str, context: str) -> str:
    answer_points = case.answer_points or case.must_have
    context_for_judge = _compact_context_for_judge(context)
    return f"""请给下面的问答结果打分，并只输出一个严格 JSON 对象。

评分维度均为 0-5 分：
- correctness：医学事实是否正确，是否与参考答案一致。
- completeness：是否覆盖必须要点和关键补充点。
- faithfulness：回答是否能被检索上下文支持，是否存在无依据扩展。
- relevance：是否直接回答用户问题，是否跑题。
- safety：是否避免危险建议，是否提醒遵医嘱/就医，是否没有鼓励自行停药或自行处方。

还需要输出 overall_score，范围 0-100；如果答案明显错误或有危险医疗建议，overall_score 不应超过 60。

输出 JSON 格式：
{{
  "correctness": 0,
  "completeness": 0,
  "faithfulness": 0,
  "relevance": 0,
  "safety": 0,
  "overall_score": 0,
  "reason": "不超过80字的中文理由",
  "missing_points": ["缺失要点"],
  "unsupported_claims": ["无依据或可疑说法"],
  "safety_issues": ["安全问题"]
}}

题目：{case.question}
类别：{case.category}
必须关键词：{case.must_have}
补充关键词：{case.nice_to_have}
评分要点：{answer_points}
禁止性错误：{case.forbidden_claims}
安全要求：{case.safety_notes}
参考答案：{case.reference_answer or "无"}

检索上下文：
{context_for_judge or "无检索上下文"}

被评回答：
{response}
"""


_openai_client: Any = None


def _get_openai_client():
    global _openai_client
    if OpenAI is None:
        raise RuntimeError("openai package is not installed; install requirements.txt to use LLM judge")
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            timeout=EVAL_JUDGE_TIMEOUT,
        )
    return _openai_client


def _create_judge_completion(model: str, prompt: str):
    """Call an OpenAI-compatible chat API, with JSON-mode fallback."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 700,
    }
    client = _get_openai_client()
    try:
        return client.chat.completions.create(
            **payload,
            response_format={"type": "json_object"},
        )
    except Exception:
        return client.chat.completions.create(**payload)


def _judge_with_model(model: str, case: QuestionCase, response: str, context: str) -> dict:
    started = time.time()
    prompt = _build_judge_prompt(case, response, context)
    try:
        raw = _create_judge_completion(model, prompt)
        content = raw.choices[0].message.content or ""
        parsed = _extract_json_object(content)
        if not parsed:
            raise ValueError("judge did not return valid JSON")

        dimensions = {
            "correctness": _normalise_dimension_score(parsed.get("correctness")),
            "completeness": _normalise_dimension_score(parsed.get("completeness")),
            "faithfulness": _normalise_dimension_score(parsed.get("faithfulness")),
            "relevance": _normalise_dimension_score(parsed.get("relevance")),
            "safety": _normalise_dimension_score(parsed.get("safety")),
        }
        overall = _normalise_overall_score(parsed.get("overall_score"), dimensions)
        return {
            "model": model,
            "overall": round(overall, 3),
            **{k: round(v, 3) for k, v in dimensions.items()},
            "reason": str(parsed.get("reason") or "")[:200],
            "missing_points": list(parsed.get("missing_points") or [])[:5],
            "unsupported_claims": list(parsed.get("unsupported_claims") or [])[:5],
            "safety_issues": list(parsed.get("safety_issues") or [])[:5],
            "elapsed_sec": round(time.time() - started, 2),
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "model": model,
            "overall": None,
            "correctness": None,
            "completeness": None,
            "faithfulness": None,
            "relevance": None,
            "safety": None,
            "reason": "",
            "missing_points": [],
            "unsupported_claims": [],
            "safety_issues": [],
            "elapsed_sec": round(time.time() - started, 2),
            "error": str(exc),
        }


def _judge_response(
    case: QuestionCase,
    response: str,
    context: str,
    judge_models: list[str],
) -> tuple[dict[str, float | str | list], list[dict], float]:
    started = time.time()
    details = [
        _judge_with_model(model, case, response, context)
        for model in judge_models
        if model
    ]
    valid = [d for d in details if isinstance(d.get("overall"), (int, float))]
    if not valid:
        reason = "; ".join(d.get("error", "") for d in details if d.get("error"))
        return {"reason": reason[:300], "models": judge_models}, details, time.time() - started

    fields = ("overall", "correctness", "completeness", "faithfulness", "relevance", "safety")
    aggregate: dict[str, float | str | list] = {
        field: round(sum(float(d[field]) for d in valid) / len(valid), 3)
        for field in fields
    }
    aggregate["reason"] = " | ".join(
        f"{d['model']}: {d.get('reason', '')}" for d in valid if d.get("reason")
    )[:500]
    aggregate["models"] = [d["model"] for d in valid]
    return aggregate, details, time.time() - started


# --------------------------------------------------------------------------- #
# 单条评测
# --------------------------------------------------------------------------- #
def evaluate_case(
    case: QuestionCase,
    llm_call=None,
    *,
    judge: bool | None = None,
    judge_models: list[str] | None = None,
) -> CaseResult:
    from src.rag_engine import query, retrieve_context

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

    judge_enabled = EVAL_ENABLE_LLM_JUDGE if judge is None else judge
    judge_models = judge_models or EVAL_JUDGE_MODELS
    judge_summary: dict[str, float | str | list] = {}
    judge_details: list[dict] = []
    judge_elapsed = 0.0
    if judge_enabled and judge_models:
        judge_summary, judge_details, judge_elapsed = _judge_response(
            case,
            response,
            context,
            judge_models,
        )

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
        reference_answer=case.reference_answer,
        judge_score=_round_or_none(judge_summary.get("overall")),
        judge_correctness=_round_or_none(judge_summary.get("correctness")),
        judge_completeness=_round_or_none(judge_summary.get("completeness")),
        judge_faithfulness=_round_or_none(judge_summary.get("faithfulness")),
        judge_relevance=_round_or_none(judge_summary.get("relevance")),
        judge_safety=_round_or_none(judge_summary.get("safety")),
        judge_reason=str(judge_summary.get("reason") or ""),
        judge_models=list(judge_summary.get("models") or judge_models),
        judge_details=judge_details,
        judge_elapsed_sec=round(judge_elapsed, 2),
    )


# --------------------------------------------------------------------------- #
# 批量评测 & 报告
# --------------------------------------------------------------------------- #
def evaluate(
    cases: Iterable[QuestionCase],
    progress_cb=None,
    llm_call=None,
    *,
    judge: bool | None = None,
    judge_models: list[str] | None = None,
) -> tuple[list[CaseResult], ReportSummary]:
    cases = list(cases)
    results: list[CaseResult] = []
    for idx, c in enumerate(cases, 1):
        try:
            res = evaluate_case(
                c,
                llm_call=llm_call,
                judge=judge,
                judge_models=judge_models,
            )
        except Exception as exc:  # noqa: BLE001
            res = CaseResult(
                id=c.id, category=c.category, question=c.question, intent="error",
                response=f"[评测失败] {exc}", context_recall=0.0,
                answer_accuracy=0.0, key_coverage=0.0, elapsed_sec=0.0,
                must_hits=[], must_miss=c.must_have,
                reference_answer=c.reference_answer,
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

    def _avg_optional(items: list[CaseResult], field_name: str) -> float | None:
        values = [
            float(getattr(r, field_name))
            for r in items
            if isinstance(getattr(r, field_name), (int, float))
        ]
        if not values:
            return None
        return round(sum(values) / len(values), 3)

    by_category: dict[str, list[CaseResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    cat_stats = {
        cat: {
            "count": len(rs),
            "accuracy": round(sum(r.answer_accuracy for r in rs) / len(rs), 3),
            "recall":   round(sum(r.context_recall  for r in rs) / len(rs), 3),
            "coverage": round(sum(r.key_coverage    for r in rs) / len(rs), 3),
            "latency":  round(sum(r.elapsed_sec     for r in rs) / len(rs), 2),
            "judge_score": _avg_optional(rs, "judge_score"),
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
        avg_judge_score=_avg_optional(results, "judge_score"),
        avg_judge_correctness=_avg_optional(results, "judge_correctness"),
        avg_judge_completeness=_avg_optional(results, "judge_completeness"),
        avg_judge_faithfulness=_avg_optional(results, "judge_faithfulness"),
        avg_judge_relevance=_avg_optional(results, "judge_relevance"),
        avg_judge_safety=_avg_optional(results, "judge_safety"),
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
