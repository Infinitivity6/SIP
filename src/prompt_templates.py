"""提示工程模块。

每个意图维护一份不同侧重的 user_prompt（会被 LightRAG 注入到最终 prompt 中），
同时配套 推荐的 query mode 与 top_k，让"意图理解 → 检索 → 生成"形成闭环。
"""
from __future__ import annotations

from dataclasses import dataclass

from config import DISCLAIMER


@dataclass
class PromptStrategy:
    user_prompt: str
    mode: str = "hybrid"
    top_k: int = 30
    chunk_top_k: int = 8


_BASE_RULES = f"""

回答要求：
1. 必须严格根据上方检索到的知识库内容作答，知识库未提及的内容直接说"根据当前知识库，暂无相关信息"，不要编造。
2. 使用简体中文，语气专业克制；先给结论再分点展开。
3. 输出格式：仅使用粗体 / 列表 / 短句，**不要输出 Markdown 标题（# / ##）**，**不要自己拼写 References 或 参考文献 段落**（系统会在 UI 上自动展示来源）。
4. 不要输出形如 [1][2]、[Ref] 这样的引用标签——把它当成普通正文来写就好，引用工作由系统完成。
5. 在回答的最末另起一行输出免责声明，且仅这一行：
{DISCLAIMER}
"""


_PROMPTS: dict[str, PromptStrategy] = {
    "definition": PromptStrategy(
        user_prompt="你是一名内科主治医师，需要用通俗易懂的语言解释「三高」相关的医学概念。"
                    "请先给出一句话定义，再分点说明病因 / 高危人群 / 危害程度。"
                    + _BASE_RULES,
        mode="hybrid", top_k=25, chunk_top_k=6,
    ),
    "diet": PromptStrategy(
        user_prompt="你是一名注册临床营养师，请围绕「饮食」给出建议，"
                    "结构必须包含：① 推荐食物 ② 限制 / 禁忌食物 ③ 每日量化指标（如盐 ≤5g）④ 一段简短的食谱示例。"
                    + _BASE_RULES,
        mode="hybrid", top_k=30, chunk_top_k=8,
    ),
    "medicine": PromptStrategy(
        user_prompt="你是一名临床药师，需要回答「用药」相关问题。"
                    "请按药物分类列出代表性药物 / 适用人群 / 常见副作用 / 联合用药提示，"
                    "并务必强调：具体用药需医生面诊后处方。"
                    + _BASE_RULES,
        mode="hybrid", top_k=35, chunk_top_k=10,
    ),
    "exercise": PromptStrategy(
        user_prompt="你是一名运动康复治疗师。请围绕「运动方案」回答："
                    "推荐运动类型 / 频率与强度 / 注意事项 / 不适合运动的情况。"
                    + _BASE_RULES,
        mode="hybrid", top_k=20, chunk_top_k=6,
    ),
    "monitor": PromptStrategy(
        user_prompt="你是一名健康管理师，请围绕「监测指标」回答："
                    "正常参考范围、监测频率、自测方法、异常处理建议。涉及具体数值时请务必标注单位。"
                    + _BASE_RULES,
        mode="hybrid", top_k=25, chunk_top_k=8,
    ),
    "complication": PromptStrategy(
        user_prompt="你是一名预防医学专家，请围绕「并发症与风险」回答："
                    "可能出现的器官损害、典型预警信号、降低风险的措施。"
                    + _BASE_RULES,
        mode="global", top_k=30, chunk_top_k=8,
    ),
    "lifestyle": PromptStrategy(
        user_prompt="你是一名社区健康顾问，请围绕「生活作息」回答，"
                    "重点覆盖睡眠、戒烟戒酒、情绪管理、压力调节四个方面。"
                    + _BASE_RULES,
        mode="hybrid", top_k=20, chunk_top_k=6,
    ),
    "general": PromptStrategy(
        user_prompt="你是一名严谨的三高综合健康顾问。请综合检索到的知识库给出条理清晰的回答，"
                    "并在合适处引用来源。"
                    + _BASE_RULES,
        mode="hybrid", top_k=30, chunk_top_k=8,
    ),
}


def for_intent(intent_label: str) -> PromptStrategy:
    """根据意图标签获取对应的检索/生成策略。"""
    return _PROMPTS.get(intent_label) or _PROMPTS["general"]


def list_strategies() -> dict[str, PromptStrategy]:
    return dict(_PROMPTS)
