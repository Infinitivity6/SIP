"""系统评测标签页：召回率 / 准确率 / 覆盖率 / 延迟 + 报告导出。"""
from __future__ import annotations

import io as _io
import os
from dataclasses import asdict

import pandas as pd
import streamlit as st

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
    if val >= 0.8:
        return "🟢"
    elif val >= 0.5:
        return "🟡"
    return "🔴"


def render_eval_tab() -> None:
    st.markdown("### 📊 自动化评测")
    st.caption(
        "评测维度：检索召回率 · 生成准确率 · 关键词覆盖率 · 平均响应时间。"
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
        run_eval = st.button("⚡ 一键跑全套评测", type="primary", width="stretch")

    if run_eval and cases:
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
                    "耗时(s)": last_result.elapsed_sec,
                }
            )
            live_table_box.dataframe(live_rows, width="stretch")

        with st.spinner("正在执行批量评测，请耐心等待（每题需调用 LLM）..."):
            results, summary = evaluate(cases, progress_cb=_cb)
        progress.progress(1.0)

        st.success("✅ 评测完毕！")

        # ── 四维指标卡片（带颜色标记） ──
        m1, m2, m3, m4 = st.columns(4)
        acc = summary.avg_accuracy
        rec = summary.avg_recall
        cov = summary.avg_coverage
        lat = summary.avg_latency

        with m1:
            st.metric(
                "📈 平均准确率",
                f"{acc * 100:.1f}%",
                delta=_metric_delta(acc),
                delta_color="off",
            )
        with m2:
            st.metric(
                "🎯 平均召回率",
                f"{rec * 100:.1f}%",
                delta=_metric_delta(rec),
                delta_color="off",
            )
        with m3:
            st.metric(
                "📚 平均覆盖率",
                f"{cov * 100:.1f}%",
                delta=_metric_delta(cov),
                delta_color="off",
            )
        with m4:
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
                chart_data = cat_df2.set_index("类别")[["accuracy", "recall"]]
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
                    "耗时(s)": r.elapsed_sec,
                    "缺失关键词": "/".join(r.must_miss),
                    "回答片段": r.response[:120]
                    + ("..." if len(r.response) > 120 else ""),
                }
                for r in results
            ]
        )

        st.dataframe(
            detail_df.style.applymap(
                _color_accuracy, subset=["准确率", "覆盖率", "召回率"]
            ),
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
