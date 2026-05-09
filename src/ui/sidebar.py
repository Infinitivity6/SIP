"""侧边栏渲染：系统信息卡片、知识库文献列表、图谱统计。"""
from __future__ import annotations

import os
import time

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

import config
from src import data_loader
from src.rag_engine import list_documents
from src.ui.theme import render_microcopy


_BOT_HTML = r"""
<div class="sip-bot">
  <svg viewBox="0 0 210 170" role="img" aria-label="SIP assistant">
    <defs>
      <linearGradient id="botBody" x1="0" x2="1" y1="0" y2="1">
        <stop stop-color="#f8f3e6" offset="0"/>
        <stop stop-color="#bdd8c9" offset="0.58"/>
        <stop stop-color="#789e91" offset="1"/>
      </linearGradient>
      <linearGradient id="botScreen" x1="0" x2="1">
        <stop stop-color="#16201d" offset="0"/>
        <stop stop-color="#22332e" offset="1"/>
      </linearGradient>
      <filter id="softShadow" x="-30%" y="-30%" width="160%" height="160%">
        <feDropShadow dx="0" dy="10" stdDeviation="8" flood-color="#000" flood-opacity="0.32"/>
      </filter>
    </defs>

    <ellipse class="shadow" cx="105" cy="151" rx="54" ry="10"/>
    <g class="float">
      <path class="halo" d="M52 28 C78 2, 139 5, 161 32"/>
      <circle class="pulse" cx="105" cy="18" r="7"/>
      <line x1="105" y1="25" x2="105" y2="39" class="antenna"/>

      <rect x="45" y="38" width="120" height="82" rx="28" fill="url(#botBody)" filter="url(#softShadow)"/>
      <rect x="59" y="52" width="92" height="40" rx="18" fill="url(#botScreen)"/>

      <g class="eyes">
        <circle class="eye" cx="86" cy="72" r="8"/>
        <circle class="eye" cx="124" cy="72" r="8"/>
        <circle class="spark" cx="82" cy="68" r="2.2"/>
        <circle class="spark" cx="120" cy="68" r="2.2"/>
      </g>
      <path class="smile" d="M88 85 Q105 97 122 85"/>

      <rect x="76" y="101" width="58" height="31" rx="8" fill="#22332e"/>
      <path d="M86 113 h38 M86 123 h26" class="bookLine"/>
      <path d="M111 108 v18 M102 117 h18" class="cross"/>

      <path class="arm left" d="M45 82 C25 88 24 116 43 125"/>
      <path class="arm right" d="M165 82 C188 88 188 116 168 125"/>
      <circle cx="42" cy="125" r="8" fill="#bdd8c9"/>
      <circle cx="168" cy="125" r="8" fill="#bdd8c9"/>
    </g>
  </svg>
  <div class="bot-copy">
    <strong>SIP Assistant</strong>
    <span>ready for grounded answers</span>
  </div>
</div>

<style>
  html, body { margin:0; background:transparent; overflow:hidden; }
  .sip-bot {
    height: 170px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(155,215,180,.24);
    border-radius: 14px;
    background:
      radial-gradient(circle at 50% 6%, rgba(155,215,180,.18), transparent 65%),
      linear-gradient(180deg, rgba(155,215,180,.10), rgba(159,200,212,.045));
    box-shadow: 0 14px 30px rgba(0,0,0,.20);
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #f2f0e7;
  }
  svg { width: 190px; height: 142px; overflow: visible; }
  .float { animation: float 4.6s ease-in-out infinite; transform-origin: 105px 85px; }
  .shadow { fill: rgba(0,0,0,.24); animation: shadow 4.6s ease-in-out infinite; }
  .halo { fill:none; stroke:rgba(155,215,180,.38); stroke-width:2; stroke-linecap:round; }
  .pulse { fill:#9bd7b4; animation: pulse 1.8s ease-in-out infinite; }
  .antenna { stroke:#9bd7b4; stroke-width:4; stroke-linecap:round; }
  .eye { fill:#9bd7b4; animation: blink 6.5s ease-in-out infinite; transform-origin:center; }
  .spark { fill:#f8f3e6; opacity:.9; }
  .smile { fill:none; stroke:#9bd7b4; stroke-width:3; stroke-linecap:round; }
  .bookLine { fill:none; stroke:#f8f3e6; stroke-width:2.4; stroke-linecap:round; opacity:.78; }
  .cross { fill:none; stroke:#e1b16d; stroke-width:4; stroke-linecap:round; animation: cross 2.2s ease-in-out infinite; }
  .arm { fill:none; stroke:#bdd8c9; stroke-width:11; stroke-linecap:round; }
  .left { animation: waveL 5.5s ease-in-out infinite; transform-origin:45px 82px; }
  .right { animation: waveR 5.5s ease-in-out infinite; transform-origin:165px 82px; }
  .bot-copy { margin-top:-4px; text-align:center; line-height:1.15; }
  .bot-copy strong { display:block; font-size:13px; letter-spacing:.02em; }
  .bot-copy span { display:block; font-size:10px; color:rgba(242,240,231,.58); }
  @keyframes float { 0%,100%{transform:translateY(0) rotate(-.5deg)} 50%{transform:translateY(-8px) rotate(1deg)} }
  @keyframes shadow { 0%,100%{transform:scaleX(.92); opacity:.22} 50%{transform:scaleX(1.08); opacity:.13} }
  @keyframes pulse { 0%,100%{r:7; opacity:1} 50%{r:10; opacity:.55} }
  @keyframes blink { 0%, 88%, 94%, 100%{ transform:scaleY(1) } 90%, 92%{ transform:scaleY(.12) } }
  @keyframes cross { 0%,100%{opacity:.78} 50%{opacity:1} }
  @keyframes waveL { 0%,100%{transform:rotate(0)} 50%{transform:rotate(-7deg)} }
  @keyframes waveR { 0%,100%{transform:rotate(0)} 50%{transform:rotate(7deg)} }
</style>
"""


def render_sidebar() -> None:
    with st.sidebar:
        components.html(_BOT_HTML, height=178)

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
