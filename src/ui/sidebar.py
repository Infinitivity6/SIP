"""侧边栏渲染：系统信息卡片、知识库文献列表、图谱统计。"""
from __future__ import annotations

import os
import time

import networkx as nx
import streamlit as st

import config
from src import data_loader
from src.rag_engine import list_documents
from src.ui.theme import render_microcopy

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sip-sidebar-brand">
              <div class="sip-section-kicker">SIP v1</div>
              <div class="sip-sidebar-brand-title">三高知识工作台</div>
              <div class="sip-muted">检索、图谱、录入、评测</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 系统信息卡片 ──
        rerank_badge = (
            "已启用"
            if config.ENABLE_RERANK
            else "未启用"
        )
        st.markdown(f"""
        <div class="sip-sidebar-card">
            <div class="sip-panel-title"><strong>系统信息</strong></div>
            <div class="sip-sidebar-row"><span>领域</span><span>{config.DOMAIN_NAME}</span></div>
            <div class="sip-sidebar-row"><span>LLM</span><span><code>{config.LLM_MODEL}</code></span></div>
            <div class="sip-sidebar-row"><span>Embedding</span><span><code>{config.EMBED_MODEL}</code></span></div>
            <div class="sip-sidebar-row"><span>Reranker</span><span>{rerank_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── 知识库（卡片式布局） ──
        st.markdown("#### 知识库")

        docs = list_documents()
        if docs:
            total_chars = sum(d["length"] for d in docs)
            st.caption(f"共 **{len(docs)}** 篇文献 · **{total_chars:,}** 字符")

            doc_lines = []
            for d in docs:
                label = os.path.basename(d.get("file_path") or "") or d["doc_id"][:10]
                display_label = label[:30] + ("…" if len(label) > 30 else "")
                doc_lines.append(
                    f'<div class="sip-doc-item">'
                    f'<span class="sip-doc-name" title="{label}">{display_label}</span>'
                    f'<span class="sip-doc-size">{d["length"]:,} 字</span>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="sip-doc-list">{"".join(doc_lines)}</div>',
                unsafe_allow_html=True,
            )
            if st.button("刷新列表", width="stretch"):
                st.rerun()
        else:
            st.caption("知识库为空，请前往「知识录入」页面录入。")
            if st.button("一键初始化", type="primary", width="stretch"):
                with st.status("正在录入全部文献...", expanded=True) as _s:
                    try:
                        info = data_loader.ingest_folder()
                        _s.update(label=f"已录入 {info['files']} 篇 ({info['chars']} 字)", state="complete")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as exc:
                        _s.update(label="失败", state="error")
                        st.error(str(exc))

        # ── 图谱统计 ──
        graph_path = os.path.join(config.WORKING_DIR, "graph_chunk_entity_relation.graphml")
        if os.path.exists(graph_path):
            try:
                g = nx.read_graphml(graph_path)
                st.divider()
                st.markdown("#### 知识图谱")
                c1, c2 = st.columns(2)
                c1.metric("实体", g.number_of_nodes())
                c2.metric("关系", g.number_of_edges())
                st.caption(f"图密度：`{nx.density(g):.4f}`")
                if st.button("刷新统计", width="stretch"):
                    st.rerun()
            except Exception:
                pass

        st.divider()

        # ── 底部说明 ──
        render_microcopy(
            "核心架构：GraphRAG。医学文献被解析为实体-关系知识图谱，检索时结合向量语义匹配与图谱邻域信息。"
        )
