"""知识图谱标签页：pyvis 交互式实体关系可视化。"""
from __future__ import annotations

import os

import networkx as nx
import streamlit as st

import config
from src.ui.components import render_knowledge_graph


def render_graph_tab() -> None:
    st.markdown("### 🕸️ 医学实体关系图谱")
    st.markdown(
        '<p style="opacity:0.55;font-size:0.88rem;margin-bottom:0.8rem;">'
        '可拖拽节点 / 滚轮缩放 / 悬停查看标签 '
        '· 由 LightRAG 在录入阶段自动抽取实体与关系'
        '</p>',
        unsafe_allow_html=True,
    )

    # ── 工具栏 ──
    tool_col1, tool_col2, tool_col3 = st.columns([1, 1, 6])
    with tool_col1:
        if st.button("🔄 刷新图谱", width="stretch"):
            st.rerun()
    with tool_col2:
        height_choice = st.selectbox(
            "图谱高度",
            options=["520px", "640px", "780px"],
            index=1,
            label_visibility="collapsed",
        )

    graph_path = os.path.join(config.WORKING_DIR, "graph_chunk_entity_relation.graphml")
    if os.path.exists(graph_path):
        try:
            graph = nx.read_graphml(graph_path)
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("实体", graph.number_of_nodes())
            s2.metric("关系", graph.number_of_edges())
            s3.metric("图密度", f"{nx.density(graph):.4f}")
            s4.metric("视图高度", height_choice)
        except Exception:
            pass

    st.divider()
    render_knowledge_graph(height=height_choice, show_metrics=False)

    st.caption(
        "节点颜色：🟢 高连接度（>3）  🔵 中等连接（2-3）  ⚪ 低连接（1）。"
        "节点大小与连接度成正比。"
    )
