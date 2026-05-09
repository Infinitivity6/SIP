"""意图理解模块。

策略：先做规则关键词匹配（速度快、对小样本足够稳），匹配不到时再回退给
LLM 兜底。每个意图都对应一种检索/生成策略，供下游 prompt_templates 使用。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable


# --------------------------------------------------------------------------- #
# 意图定义
# --------------------------------------------------------------------------- #
INTENT_LABELS = [
    "definition",      # 概念解释/疾病定义
    "diet",            # 饮食建议
    "medicine",        # 用药咨询
    "exercise",        # 运动建议
    "monitor",         # 监测/化验指标
    "complication",    # 并发症
    "lifestyle",       # 生活作息
    "general",         # 综合咨询/兜底
]

INTENT_DISPLAY = {
    "definition":   "🩺 概念解释",
    "diet":         "🥦 饮食建议",
    "medicine":     "💊 用药咨询",
    "exercise":     "🏃 运动指导",
    "monitor":      "📈 监测指标",
    "complication": "⚠️ 并发症风险",
    "lifestyle":    "🌙 生活作息",
    "general":      "💬 综合咨询",
}

# 关键词词典（粗暴但有效，覆盖常见问法）
KEYWORD_RULES: dict[str, list[str]] = {
    "definition":   ["是什么", "什么是", "定义", "概念", "病因", "为什么会", "原理"],
    "diet":         ["吃什么", "饮食", "食物", "食谱", "禁忌", "能吃", "不能吃", "营养", "盐", "甜食", "添加糖", "油炸", "腌制"],
    "medicine":     ["药", "用药", "服药", "降压", "降糖", "降脂", "副作用", "处方", "ACEI", "ARB", "他汀", "胰岛素"],
    "exercise":     ["运动", "锻炼", "跑步", "跑", "走路", "散步", "健身", "训练", "强度", "有氧"],
    "monitor":      ["指标", "化验", "体检", "测量", "正常值", "正常范围", "参考值", "多少正常", "数值", "mmHg", "mmol"],
    "complication": ["并发症", "风险", "诱发", "导致", "心脑血管", "肾", "眼", "中风", "心梗", "动脉粥样硬化"],
    "lifestyle":    ["作息", "睡眠", "熬夜", "压力", "情绪", "戒烟", "戒酒", "习惯"],
}


@dataclass
class IntentResult:
    label: str
    confidence: float
    keywords: list[str]
    method: str          # "rule" 或 "llm"

    @property
    def display(self) -> str:
        return INTENT_DISPLAY.get(self.label, self.label)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "display": self.display,
            "confidence": round(self.confidence, 3),
            "keywords": self.keywords,
            "method": self.method,
        }


# --------------------------------------------------------------------------- #
# 1. 规则识别
# --------------------------------------------------------------------------- #
# 当多个意图命中数相同时的优先级（数值越大越优先）
_TIE_BREAK_PRIORITY = {
    "complication": 6,
    "medicine":     5,
    "diet":         5,
    "exercise":     4,
    "lifestyle":    4,
    "monitor":      3,
    "definition":   2,
    "general":      0,
}


def _rule_classify(question: str) -> IntentResult | None:
    hits: dict[str, list[str]] = {}
    for label, kws in KEYWORD_RULES.items():
        matched = [k for k in kws if k in question]
        if matched:
            hits[label] = matched

    if not hits:
        return None

    # 先按命中数量降序，命中数相同时按优先级降序
    best_label = max(
        hits,
        key=lambda k: (len(hits[k]), _TIE_BREAK_PRIORITY.get(k, 0)),
    )
    matched_kws = hits[best_label]
    # 信心度：命中关键词数 / 该标签关键词总数，限制在 [0.3, 0.95]
    raw = len(matched_kws) / max(1, len(KEYWORD_RULES[best_label]))
    confidence = max(0.3, min(0.95, raw + 0.4))
    return IntentResult(best_label, confidence, matched_kws, method="rule")


# --------------------------------------------------------------------------- #
# 2. LLM 兜底分类
# --------------------------------------------------------------------------- #
_LLM_PROMPT = """你是医疗问答系统的意图分类器。请把用户问题分类到以下标签之一：
{labels}

要求：
1. 只输出严格的 JSON，不要任何额外文字。
2. 字段：label（取上述标签之一）、confidence（0~1 浮点数）、keywords（最多 5 个关键词字符串）。

用户问题：{question}
"""


def _safe_json(text: str) -> dict | None:
    """尝试从 LLM 输出中抽取第一个 JSON 对象。"""
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _llm_classify(question: str, llm_call) -> IntentResult:
    prompt = _LLM_PROMPT.format(
        labels="、".join(INTENT_LABELS),
        question=question,
    )
    raw = llm_call(prompt)
    parsed = _safe_json(raw) if isinstance(raw, str) else None
    if parsed and parsed.get("label") in INTENT_LABELS:
        return IntentResult(
            label=parsed["label"],
            confidence=float(parsed.get("confidence", 0.6)),
            keywords=list(parsed.get("keywords") or [])[:5],
            method="llm",
        )
    return IntentResult("general", 0.4, [], method="llm")


# --------------------------------------------------------------------------- #
# 3. 对外 API
# --------------------------------------------------------------------------- #
def classify(question: str, llm_call=None) -> IntentResult:
    """优先规则识别，失败时调用 LLM。

    llm_call 是一个签名为 (prompt: str) -> str 的可调用对象，
    传 None 时直接走兜底 general 标签。
    """
    if not question or not question.strip():
        return IntentResult("general", 0.0, [], method="rule")

    rule_hit = _rule_classify(question)
    if rule_hit is not None:
        return rule_hit

    if llm_call is None:
        return IntentResult("general", 0.4, [], method="rule")

    return _llm_classify(question, llm_call)


def extract_diseases(question: str) -> list[str]:
    """识别问题中提到的三高疾病，用于检索时加权。"""
    aliases = {
        "高血压": ["高血压", "hypertension", "血压高"],
        "高血糖": ["高血糖", "糖尿病", "hyperglycemia", "血糖高"],
        "高血脂": ["高血脂", "高血脂症", "hyperlipidemia", "血脂高", "胆固醇"],
    }
    found = []
    for canonical, words in aliases.items():
        if any(w in question for w in words):
            found.append(canonical)
    return found
