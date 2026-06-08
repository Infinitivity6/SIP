"""系统评测标签页：召回率 / 准确率 / 覆盖率 / 延迟 + 报告导出。"""
from __future__ import annotations

import io as _io
import json as _json
import os
import urllib.error as _urlerror
import urllib.request as _urlrequest
from dataclasses import asdict

import pandas as pd
import streamlit as st

from config import (
    API_KEY,
    BASE_URL,
    EVAL_ENABLE_LLM_JUDGE,
    EVAL_JUDGE_CANDIDATE_MODELS,
    EVAL_JUDGE_MODELS,
    LLM_MODEL,
)
from src.evaluator import evaluate, load_test_set, save_report


def _color_accuracy(val):
    """根据数值返回颜色样式（绿/黄/红）。"""
    if isinstance(val, (int, float)):
        if val >= 0.8:
            return "background-color: #065f46; color: #d1fae5"
        elif val >= 0.5:
            return "background-color: #7a6a00; color: #fef3c7"
        else:
            return "background-color: #7f1d1d; color: #fecaca"
    return ""


def _metric_delta(val: float) -> str:
    """根据指标值返回带颜色的 delta 标记。"""
    if val is None:
        return "—"
    if val >= 0.8:
        return "🟢"
    elif val >= 0.5:
        return "🟡"
    return "🔴"


def _unique_models(models: list[str]) -> list[str]:
    seen = set()
    out = []
    for model in models:
        model = (model or "").strip()
        if model and model not in seen:
            seen.add(model)
            out.append(model)
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_platform_chat_models(api_key: str, base_url: str) -> tuple[list[str], str]:
    """Fetch current chat model ids from an OpenAI-compatible /models endpoint."""
    if not api_key:
        return [], "未配置 API Key"

    url = f"{base_url.rstrip('/')}/models?type=text&sub_type=chat"
    req = _urlrequest.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with _urlrequest.urlopen(req, timeout=8) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
    except (_urlerror.URLError, TimeoutError, OSError, ValueError) as exc:
        return [], str(exc)

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return [], "模型接口返回格式异常"

    models = [
        item.get("id", "").strip()
        for item in data
        if isinstance(item, dict) and item.get("id")
    ]
    return _unique_models(models), ""


def render_eval_tab() -> None:
    st.markdown("### 📊 自动化评测")
    st.caption(
        "评测维度：检索召回率 · 关键词准确率 · 关键词覆盖率 · LLM语义评审 · 平均响应时间。"
        "测试集覆盖 8 个意图类别，共 26 道题。"
    )

    try:
        cases = load_test_set()
    except Exception as exc:
        st.error(f"加载测试集失败：{exc}")
        cases = []

    if not cases:
        return

    cat_counts: dict = {}
    for c in cases:
        cat_counts[c.category] = cat_counts.get(c.category, 0) + 1
    cat_df = pd.DataFrame(
        {"类别": list(cat_counts.keys()), "题数": list(cat_counts.values())}
    )

    eval_col1, eval_col2 = st.columns([2, 1])
    with eval_col1:
        st.write(
            f"已加载 **{len(cases)}** 道测试题，覆盖 **{len(cat_counts)}** 个类别。"
        )
        with st.expander("📋 查看测试题样例与分布", expanded=False):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.json([asdict(c) for c in cases[:3]])
            with c2:
                st.bar_chart(cat_df.set_index("类别"), width="stretch")
    with eval_col2:
        st.markdown("")
        st.markdown("")
        enable_judge = st.checkbox(
            "启用 LLM 语义评审",
            value=EVAL_ENABLE_LLM_JUDGE,
            help="保留关键词 baseline，并额外用 Judge 模型评估正确性、完整性、忠实性、相关性和医学安全性。",
        )
        st.caption(f"主问答/抽取模型：`{LLM_MODEL}`")
        refresh_platform_models = st.checkbox(
            "读取平台可用模型",
            value=False,
            disabled=not enable_judge,
            help="调用当前 BASE_URL 的 /models 接口获取可见 chat 模型；失败时仍使用内置候选。",
        )
        platform_models: list[str] = []
        if enable_judge and refresh_platform_models:
            platform_models, fetch_error = _fetch_platform_chat_models(API_KEY, BASE_URL)
            if fetch_error:
                st.caption(f"平台模型列表读取失败：{fetch_error}")

        judge_options = _unique_models(
            EVAL_JUDGE_MODELS
            + EVAL_JUDGE_CANDIDATE_MODELS
            + platform_models
            + [LLM_MODEL]
        )
        default_judges = [m for m in EVAL_JUDGE_MODELS if m in judge_options]
        selected_judge_models = st.multiselect(
            "Judge 模型（可多选）",
            options=judge_options,
            default=default_judges,
            disabled=not enable_judge,
            help="建议选择与主问答模型不同、能力更强或模型家族不同的 judge。",
        )
        custom_judge_model_text = st.text_input(
            "自定义 Judge 模型",
            value="",
            disabled=not enable_judge,
            placeholder="例如：deepseek-ai/DeepSeek-V3.1, Qwen/Qwen3-235B-A22B",
            help="候选列表没有的模型可在这里补充，多个模型用英文逗号分隔。",
        )
        run_eval = st.button("⚡ 一键跑全套评测", type="primary", width="stretch")

    if run_eval and cases:
        custom_judge_models = [
            m.strip() for m in custom_judge_model_text.split(",") if m.strip()
        ]
        judge_models = _unique_models(selected_judge_models + custom_judge_models)
        if enable_judge and not judge_models:
            st.warning("已启用 LLM 语义评审，请至少选择或填写一个 Judge 模型。")
            return
        if enable_judge and LLM_MODEL in judge_models:
            st.warning("当前 Judge 列表包含主问答模型，建议至少再选择一个不同模型做交叉评审。")
        progress = st.progress(0.0)
        live_table_box = st.empty()
        live_rows: list[dict] = []

        def _cb(done: int, total: int, last_result):
            progress.progress(done / total)
            live_rows.append(
                {
                    "id": last_result.id,
                    "类别": last_result.category,
                    "意图": last_result.intent,
                    "准确率": last_result.answer_accuracy,
                    "覆盖率": last_result.key_coverage,
                    "召回率": last_result.context_recall,
                    "语义分": last_result.judge_score,
                    "耗时(s)": last_result.elapsed_sec,
                    "评审(s)": last_result.judge_elapsed_sec,
                }
            )
            live_table_box.dataframe(live_rows, width="stretch")

        with st.spinner("正在执行批量评测，请耐心等待（每题需生成回答，启用后还会调用 Judge）..."):
            results, summary = evaluate(
                cases,
                progress_cb=_cb,
                judge=enable_judge,
                judge_models=judge_models,
            )
        progress.progress(1.0)

        st.success("✅ 评测完毕！")

        # ── 四维指标卡片（带颜色标记） ──
        metric_cols = st.columns(5 if summary.avg_judge_score is not None else 4)
        acc = summary.avg_accuracy
        rec = summary.avg_recall
        cov = summary.avg_coverage
        lat = summary.avg_latency
        judge_score = summary.avg_judge_score

        with metric_cols[0]:
            st.metric(
                "📈 平均准确率",
                f"{acc * 100:.1f}%",
                delta=_metric_delta(acc),
                delta_color="off",
            )
        with metric_cols[1]:
            st.metric(
                "🎯 平均召回率",
                f"{rec * 100:.1f}%",
                delta=_metric_delta(rec),
                delta_color="off",
            )
        with metric_cols[2]:
            st.metric(
                "📚 平均覆盖率",
                f"{cov * 100:.1f}%",
                delta=_metric_delta(cov),
                delta_color="off",
            )
        next_col = 3
        if judge_score is not None:
            with metric_cols[next_col]:
                st.metric(
                    "🧠 语义评审",
                    f"{judge_score * 100:.1f}%",
                    delta=_metric_delta(judge_score),
                    delta_color="off",
                )
            next_col += 1
        with metric_cols[next_col]:
            st.metric(
                "⏱️ 平均延迟",
                f"{lat:.2f}s",
                delta="⚡" if lat < 5 else ("🐢" if lat > 10 else "⏱️"),
                delta_color="off",
            )

        # ── 各类别表现 ──
        st.markdown("#### 📂 各类别表现")
        cat_rows = [
            {"类别": cat, **stats} for cat, stats in summary.by_category.items()
        ]
        if cat_rows:
            cat_df2 = pd.DataFrame(cat_rows)
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.dataframe(cat_df2, width="stretch", hide_index=True)
            with chart_col2:
                chart_cols = ["accuracy", "recall"]
                if "judge_score" in cat_df2.columns and cat_df2["judge_score"].notna().any():
                    chart_cols.append("judge_score")
                chart_data = cat_df2.set_index("类别")[chart_cols]
                st.bar_chart(chart_data, width="stretch")

        # ── 单题详情（带颜色标注） ──
        st.markdown("#### 🔬 单题详情")
        detail_df = pd.DataFrame(
            [
                {
                    "id": r.id,
                    "类别": r.category,
                    "意图": r.intent,
                    "准确率": r.answer_accuracy,
                    "覆盖率": r.key_coverage,
                    "召回率": r.context_recall,
                    "语义分": r.judge_score,
                    "事实": r.judge_correctness,
                    "完整": r.judge_completeness,
                    "忠实": r.judge_faithfulness,
                    "相关": r.judge_relevance,
                    "安全": r.judge_safety,
                    "耗时(s)": r.elapsed_sec,
                    "评审耗时(s)": r.judge_elapsed_sec,
                    "缺失关键词": "/".join(r.must_miss),
                    "评审理由": r.judge_reason,
                    "回答片段": r.response[:120]
                    + ("..." if len(r.response) > 120 else ""),
                }
                for r in results
            ]
        )

        score_cols = [
            col for col in ["准确率", "覆盖率", "召回率", "语义分", "事实", "完整", "忠实", "相关", "安全"]
            if col in detail_df.columns
        ]
        st.dataframe(
            detail_df.style.applymap(_color_accuracy, subset=score_cols),
            width="stretch",
        )

        # ── 报告下载 ──
        report_path = save_report(results, summary)
        st.info(f"💾 报告已保存到：`{report_path}`")

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            with open(report_path, "rb") as f:
                st.download_button(
                    "⬇️ 下载评测报告 JSON",
                    data=f.read(),
                    file_name=os.path.basename(report_path),
                    mime="application/json",
                    width="stretch",
                )
        with dl_col2:
            csv_buf = _io.StringIO()
            detail_df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
            st.download_button(
                "📥 导出结果 CSV",
                data=csv_buf.getvalue(),
                file_name=f"eval_{report_path.split('_')[-1].replace('.json', '.csv')}",
                mime="text/csv",
                width="stretch",
            )
