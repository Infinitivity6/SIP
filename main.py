"""三高知识智能问答平台 —— 主入口（Streamlit）。

四个核心模块：
    1. 💬 智能问答 —— 意图识别 → GraphRAG 检索 → 提示工程 → 流式输出
    2. 🕸️ 知识图谱 —— pyvis 可视化实体关系
    3. 📚 知识录入 —— 上传文件 / 一键录入 data 目录 / 触发爬虫骨架
    4. 📊 系统评测 —— 准确率 / 召回率 / 平均延迟 + 报告导出

启动方式：
    streamlit run main.py
"""
from __future__ import annotations

import streamlit as st

from src.rag_engine import get_rag
from src.ui import (
    apply_theme,
    render_app_header,
    render_chat_tab,
    render_eval_tab,
    render_graph_tab,
    render_ingest_tab,
    render_sidebar,
)

# --------------------------------------------------------------------------- #
# 页面基础设置
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="三高知识智能问答平台",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# 引擎单例
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="🧠 正在唤醒三高知识大脑（首次启动稍慢）...")
def _bootstrap_engine():
    return get_rag()


_bootstrap_engine()

# --------------------------------------------------------------------------- #
# 主题 & 侧边栏
# --------------------------------------------------------------------------- #
apply_theme()
render_sidebar()

# --------------------------------------------------------------------------- #
# 主标题 & 标签页
# --------------------------------------------------------------------------- #
render_app_header()

tab_chat, tab_graph, tab_ingest, tab_eval = st.tabs(
    ["问答中心", "知识图谱", "知识录入", "系统评测"]
)

with tab_chat:
    render_chat_tab()

with tab_graph:
    render_graph_tab()

with tab_ingest:
    render_ingest_tab()

with tab_eval:
    render_eval_tab()
