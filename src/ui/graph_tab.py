"""知识图谱标签页：pyvis 交互式实体关系可视化。"""
from __future__ import annotations

import streamlit as st

from src.ui.components import render_knowledge_graph
from src.ui.theme import render_section


def render_graph_tab() -> None:
    render_section(
        "医学实体关系图谱",
        "可拖拽节点、滚轮缩放、悬停查看标签。实体与关系由 LightRAG 在录入阶段抽取。",
        "Graph",
    )

    # ── 工具栏 ──
    tool_col1, tool_col2, tool_col3 = st.columns([1, 1, 6])
    with tool_col1:
        if st.button("刷新图谱", width="stretch"):
            st.rerun()
    with tool_col2:
        height_choice = st.selectbox(
            "图谱高度",
            options=["520px", "640px", "780px"],
            index=1,
            label_visibility="collapsed",
        )

    st.divider()
    render_knowledge_graph(height=height_choice)

    st.caption(
        "节点颜色：高连接度（>3）/ 中等连接（2-3）/ 低连接（1）。"
        "节点大小与连接度成正比。"
    )
