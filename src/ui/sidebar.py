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

# --------------------------------------------------------------------------- #
# 动态机器人吉祥物（SVG 动画 + JS 平滑眼球追踪）
# --------------------------------------------------------------------------- #
_ROBOT_HTML = r"""
<div id="rb-wrap" style="display:flex;justify-content:center;align-items:center;overflow:visible;
    background:linear-gradient(180deg, rgba(16,185,129,0.08) 0%, rgba(59,130,246,0.04) 100%);
    border-radius:16px; margin-bottom:0.5rem; padding:0.5rem 0;">
<svg width="110" height="138" viewBox="-14 -12 148 182" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
  <defs>
    <linearGradient id="mG" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f1f3f4"/>
      <stop offset="45%" stop-color="#d2d6db"/>
      <stop offset="100%" stop-color="#a8adb3"/>
    </linearGradient>
    <linearGradient id="mD" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#c4c9ce"/>
      <stop offset="100%" stop-color="#7d8288"/>
    </linearGradient>
    <filter id="rGlow">
      <feGaussianBlur stdDeviation="1.6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="dSh">
      <feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- ====== 身体组: 浮动 + 轻微摇摆 ====== -->
  <g>
    <animateTransform attributeName="transform" type="translate"
      values="0 0; 0 -8; 0 0; 0 -3; 0 0"
      dur="4s" repeatCount="indefinite" calcMode="spline"
      keyTimes="0; 0.3; 0.55; 0.75; 1"
      keySplines="0.4 0 0.6 1; 0.4 0 0.6 1; 0.4 0 0.6 1; 0.4 0 0.6 1"/>
    <g>
      <animateTransform attributeName="transform" type="rotate"
        values="0 60 90; 1.2 60 90; 0 60 90; -0.8 60 90; 0 60 90"
        dur="6s" repeatCount="indefinite" calcMode="spline"
        keyTimes="0; 0.25; 0.5; 0.75; 1"
        keySplines="0.4 0 0.6 1; 0.4 0 0.6 1; 0.4 0 0.6 1; 0.4 0 0.6 1"/>

      <!-- 地面阴影 -->
      <ellipse cx="60" cy="167" rx="32" ry="4" fill="rgba(16,185,129,0.18)">
        <animate attributeName="rx" values="32;37;34;37;32" dur="4s" repeatCount="indefinite"
          keyTimes="0;0.3;0.55;0.75;1" calcMode="spline"
          keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/>
        <animate attributeName="opacity" values="0.18;0.08;0.16;0.09;0.18" dur="4s" repeatCount="indefinite"
          keyTimes="0;0.3;0.55;0.75;1" calcMode="spline"
          keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/>
      </ellipse>

      <!-- 左腿 -->
      <rect x="42" y="130" width="7" height="24" rx="3.5" fill="url(#mD)"/>
      <rect x="38" y="151" width="15" height="6" rx="3" fill="#80868b"/>

      <!-- 右腿 -->
      <rect x="71" y="130" width="7" height="24" rx="3.5" fill="url(#mD)"/>
      <rect x="67" y="151" width="15" height="6" rx="3" fill="#80868b"/>

      <!-- 身体 -->
      <rect x="24" y="76" width="72" height="56" rx="15" fill="url(#mG)" filter="url(#dSh)"/>
      <rect x="28" y="80" width="64" height="18" rx="8" fill="rgba(255,255,255,0.28)"/>
      <!-- 身体底部微光 -->
      <rect x="28" y="112" width="64" height="4" rx="2" fill="rgba(255,255,255,0.06)"/>

      <!-- 胸口书本 + 红十字（心跳动画） -->
      <g class="hb-cross">
        <!-- 书本封面 -->
        <rect x="37" y="92" width="46" height="28" rx="3" fill="#3c4043"/>
        <!-- 书页 -->
        <rect x="39" y="94" width="42" height="24" rx="1.5" fill="#fafafa"/>
        <line x1="60" y1="94" x2="60" y2="118" stroke="#dde1e6" stroke-width="1"/>
        <!-- 左侧文字行 -->
        <line x1="43" y1="99" x2="57" y2="99" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="43" y1="103" x2="57" y2="103" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="43" y1="107" x2="57" y2="107" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="43" y1="111" x2="57" y2="111" stroke="#e8eaed" stroke-width="0.6"/>
        <!-- 右侧文字行 -->
        <line x1="63" y1="99" x2="77" y2="99" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="63" y1="103" x2="77" y2="103" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="63" y1="107" x2="77" y2="107" stroke="#e8eaed" stroke-width="0.6"/>
        <line x1="63" y1="111" x2="77" y2="111" stroke="#e8eaed" stroke-width="0.6"/>
        <!-- 红十字 -->
        <rect x="57.5" y="98" width="5" height="16" rx="2.2" fill="#e53935" filter="url(#rGlow)"/>
        <rect x="51" y="103.5" width="18" height="5" rx="2.2" fill="#e53935" filter="url(#rGlow)"/>
      </g>

      <!-- 左臂组 -->
      <g>
        <animateTransform attributeName="transform" type="rotate"
          values="0 24 86; -18 24 86; -4 24 86; 12 24 86; 0 24 86"
          dur="4.2s" repeatCount="indefinite" calcMode="spline"
          keyTimes="0; 0.28; 0.5; 0.72; 1"
          keySplines="0.38 0 0.62 1; 0.38 0 0.62 1; 0.38 0 0.62 1; 0.38 0 0.62 1"/>
        <line x1="24" y1="86" x2="5" y2="106" stroke="url(#mG)" stroke-width="10" stroke-linecap="round"/>
        <circle cx="5" cy="106" r="5" fill="#a8adb3"/>
        <line x1="5" y1="106" x2="0" y2="125" stroke="#c4c9ce" stroke-width="7" stroke-linecap="round"/>
        <circle cx="0" cy="126" r="5.5" fill="#9aa0a6"/>
      </g>

      <!-- 右臂组 -->
      <g>
        <animateTransform attributeName="transform" type="rotate"
          values="0 96 86; 12 96 86; 0 96 86; -16 96 86; 0 96 86"
          dur="4.2s" repeatCount="indefinite" calcMode="spline"
          keyTimes="0; 0.28; 0.5; 0.72; 1"
          keySplines="0.38 0 0.62 1; 0.38 0 0.62 1; 0.38 0 0.62 1; 0.38 0 0.62 1"/>
        <line x1="96" y1="86" x2="115" y2="106" stroke="url(#mG)" stroke-width="10" stroke-linecap="round"/>
        <circle cx="115" cy="106" r="5" fill="#a8adb3"/>
        <line x1="115" y1="106" x2="120" y2="125" stroke="#c4c9ce" stroke-width="7" stroke-linecap="round"/>
        <circle cx="120" cy="126" r="5.5" fill="#9aa0a6"/>
      </g>

      <!-- 脖子 -->
      <rect x="51" y="71" width="18" height="8" rx="3" fill="#9aa0a6"/>
      <line x1="55" y1="73" x2="55" y2="77" stroke="#7d8288" stroke-width="0.6"/>
      <line x1="60" y1="73" x2="60" y2="77" stroke="#7d8288" stroke-width="0.6"/>
      <line x1="65" y1="73" x2="65" y2="77" stroke="#7d8288" stroke-width="0.6"/>

      <!-- 头部 -->
      <rect x="26" y="11" width="68" height="62" rx="21" fill="url(#mG)" filter="url(#dSh)"/>
      <rect x="30" y="15" width="60" height="20" rx="10" fill="rgba(255,255,255,0.32)"/>

      <!-- 耳侧螺栓 -->
      <circle cx="27" cy="40" r="4" fill="#80868b"/>
      <circle cx="27" cy="40" r="2" fill="#5f6368"/>
      <circle cx="93" cy="40" r="4" fill="#80868b"/>
      <circle cx="93" cy="40" r="2" fill="#5f6368"/>

      <!-- ====== 左眼 ====== -->
      <g transform="translate(45,38)">
        <g>
          <animateTransform attributeName="transform" type="scale"
            values="1 1;1 1;1 0.06;1 1;1 1;1 0.05;1 1;1 1;1 0.06;1 1;1 1;1 0.05;1 1;1 1;1 0.06;1 1;1 1"
            keyTimes="0;0.15;0.17;0.19;0.34;0.36;0.38;0.52;0.54;0.56;0.70;0.715;0.72;0.85;0.87;0.89;1"
            dur="7s" repeatCount="indefinite"/>
          <circle cx="0" cy="0" r="8.5" fill="white" stroke="#5f6368" stroke-width="1.1"/>
          <circle id="pupL" cx="0" cy="0" r="4" fill="#1c1c2a"/>
          <circle cx="-3" cy="-3" r="1.4" fill="white" opacity="0.85"/>
        </g>
      </g>

      <!-- ====== 右眼 ====== -->
      <g transform="translate(75,38)">
        <g>
          <animateTransform attributeName="transform" type="scale"
            values="1 1;1 1;1 0.06;1 1;1 1;1 0.05;1 1;1 1;1 0.06;1 1;1 1;1 0.05;1 1;1 1;1 0.06;1 1;1 1"
            keyTimes="0;0.15;0.17;0.19;0.34;0.36;0.38;0.52;0.54;0.56;0.70;0.715;0.72;0.85;0.87;0.89;1"
            dur="7s" repeatCount="indefinite"/>
          <circle cx="0" cy="0" r="8.5" fill="white" stroke="#5f6368" stroke-width="1.1"/>
          <circle id="pupR" cx="0" cy="0" r="4" fill="#1c1c2a"/>
          <circle cx="-3" cy="-3" r="1.4" fill="white" opacity="0.85"/>
        </g>
      </g>

      <!-- 微笑 -->
      <path d="M49 56 Q60 63 71 56" fill="none" stroke="#80868b" stroke-width="2" stroke-linecap="round"/>

      <!-- 天线 -->
      <rect x="57" y="1" width="6" height="12" rx="3" fill="#9aa0a6"/>
      <circle cx="60" cy="0" r="4" fill="#10b981" opacity="0.95">
        <animate attributeName="r" values="4;5.5;4" dur="1.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.95;0.5;0.95" dur="1.6s" repeatCount="indefinite"/>
      </circle>
      <circle cx="60" cy="0" r="9" fill="#10b981" opacity="0.2">
        <animate attributeName="r" values="9;14;9" dur="1.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.2;0.04;0.2" dur="1.6s" repeatCount="indefinite"/>
      </circle>
    </g>
  </g>
</svg>
</div>

<style>
  html,body{margin:0;padding:0;width:100%;height:100%;background:transparent;overflow:hidden;}
  #rb-wrap{overflow:visible!important;}
  #rb-wrap svg{overflow:visible;transition:transform 0.35s cubic-bezier(0.34,1.56,0.64,1);cursor:pointer;}
  #rb-wrap:hover svg{transform:scale(1.10);}
  @keyframes pop{0%{transform:scale(1);}40%{transform:scale(1.14);}100%{transform:scale(1);}}
  #rb-wrap.pop svg{animation:pop 0.55s cubic-bezier(0.34,1.56,0.64,1);}
  @keyframes heartBeat{0%,100%{transform:scale(1);}8%{transform:scale(1.18);}16%{transform:scale(1);}24%{transform:scale(1.12);}32%{transform:scale(1);}}
  .hb-cross{transform-origin:60px 106px;animation:heartBeat 2.2s ease-in-out infinite;}
</style>

<script>
(function(){
  var wrap = document.getElementById('rb-wrap');
  var pL = document.getElementById('pupL');
  var pR = document.getElementById('pupR');
  if (!wrap || !pL || !pR) return;

  var tX = 0, tY = 0;
  var curLX = 0, curLY = 0, curRX = 0, curRY = 0;
  var maxOff = 3.0;
  var idleAngle = 0;
  var mouseActive = false;
  var idleTimer = null;

  var glanceTargetX = 0, glanceTargetY = 0;
  var glanceWeight = 0;
  var nextGlance = Date.now() + 4000 + Math.random()*5000;

  function setPupils(lx, ly, rx, ry) {
    pL.setAttribute('cx', lx); pL.setAttribute('cy', ly);
    pR.setAttribute('cx', rx); pR.setAttribute('cy', ry);
  }

  document.addEventListener('mousemove', function(e) {
    var svg = wrap.querySelector('svg');
    if (!svg) return;
    var r = svg.getBoundingClientRect();
    var mx = ((e.clientX - r.left) / r.width) * 148;
    var my = ((e.clientY - r.top) / r.height) * 182;
    var dx = mx - 45, dy = my - 38;
    var d = Math.sqrt(dx*dx + dy*dy);
    var s = Math.min(d / 50, 1) * maxOff;
    tX = d > 0 ? (dx/d) * s : 0;
    tY = d > 0 ? (dy/d) * s : 0;
    mouseActive = true; glanceWeight = 0;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function(){ mouseActive = false; }, 2200);
  });

  function idleDrift() {
    if (mouseActive) return;
    idleAngle += 0.013;

    var now = Date.now();
    if (now > nextGlance) {
      glanceTargetX = (Math.random() - 0.5) * 2.6;
      glanceTargetY = (Math.random() - 0.5) * 2.2;
      glanceWeight = 1.0;
      nextGlance = now + 4000 + Math.random() * 5000;
    }
    if (!mouseActive && glanceWeight > 0.001) {
      glanceWeight *= 0.995;
    }

    var driftX = Math.sin(idleAngle * 1.7) * 1.5;
    var driftY = Math.cos(idleAngle * 1.3) * 1.2;
    tX = driftX * (1 - glanceWeight) + glanceTargetX * glanceWeight;
    tY = driftY * (1 - glanceWeight) + glanceTargetY * glanceWeight;
  }

  wrap.addEventListener('click', function(){
    wrap.classList.remove('pop');
    void wrap.offsetWidth;
    wrap.classList.add('pop');
    maxOff = 4.5;
    setTimeout(function(){ maxOff = 3.0; }, 400);
  });

  function lerp() {
    idleDrift();
    var spd = mouseActive ? 0.11 : 0.07;
    curLX += (tX - curLX) * spd;
    curLY += (tY - curLY) * spd;
    curRX += (tX - curRX) * spd;
    curRY += (tY - curRY) * spd;
    setPupils(curLX, curLY, curRX, curRY);
    requestAnimationFrame(lerp);
  }
  lerp();
})();
</script>
"""


def render_sidebar() -> None:
    with st.sidebar:
        # ── 动态机器人吉祥物 ──
        components.html(_ROBOT_HTML, height=160)

        st.markdown("""
        <div style="text-align:center; margin-bottom:0.5rem;">
            <h3 style="margin:0; font-weight:700; letter-spacing:0.04em;
                background:linear-gradient(135deg, #34d399, #3b82f6);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            三高智能问答平台
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # ── 系统信息卡片 ──
        rerank_badge = (
            f'<span style="color:#34d399;font-weight:600;">✅ 已启用</span>'
            if config.ENABLE_RERANK
            else '<span style="opacity:0.45;">⚪ 未启用</span>'
        )
        st.markdown(f"""
        <div class="sip-card" style="font-size:0.83rem; line-height:2.1; padding:0.6rem 0.9rem;">
            <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;">
              <span style="font-size:1.1rem;">⚙️</span>
              <span style="font-weight:600;color:var(--medical-300);">系统信息</span>
            </div>
            <div><span style="opacity:0.45;">领域</span>&ensp;{config.DOMAIN_NAME}</div>
            <div><span style="opacity:0.45;">LLM</span>&ensp;<span style="font-family:monospace;font-size:0.78rem;">{config.LLM_MODEL}</span></div>
            <div><span style="opacity:0.45;">Embedding</span>&ensp;<span style="font-family:monospace;font-size:0.78rem;">{config.EMBED_MODEL}</span></div>
            <div><span style="opacity:0.45;">Reranker</span>&ensp;{rerank_badge}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── 知识库（卡片式布局） ──
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;">
          <span style="font-size:1rem;">📚</span>
          <span style="font-weight:700;font-size:0.95rem;">知识库</span>
        </div>
        """, unsafe_allow_html=True)

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
                    f'<span class="sip-doc-name" title="{label}">📄 {display_label}</span>'
                    f'<span class="sip-doc-size">{d["length"]:,} 字</span>'
                    f'</div>'
                )
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.025);border-radius:10px;'
                f'padding:0.2rem 0;margin-bottom:0.5rem;border:1px solid rgba(255,255,255,0.04);">'
                f'{"".join(doc_lines)}</div>',
                unsafe_allow_html=True,
            )
            if st.button("🔄 刷新列表", width="stretch"):
                st.rerun()
        else:
            st.caption("知识库为空，请前往「知识录入」页面录入。")
            if st.button("⚡ 一键初始化", type="primary", width="stretch"):
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
                st.markdown("""
                <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;">
                  <span style="font-size:1rem;">🕸️</span>
                  <span style="font-weight:700;font-size:0.95rem;">知识图谱</span>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.metric("🧩 实体", g.number_of_nodes())
                c2.metric("🔗 关系", g.number_of_edges())
                st.caption(f"图密度：`{nx.density(g):.4f}`")
                if st.button("🔄 刷新统计", width="stretch"):
                    st.rerun()
            except Exception:
                pass

        st.divider()

        # ── 底部说明 ──
        st.markdown("""
        <div style="font-size:0.78rem; opacity:0.5; line-height:1.7; padding:0.3rem 0;">
        <strong>核心架构</strong>：GraphRAG<br>
        将医学文献解析为实体-关系知识图谱，<br>
        检索时同时启用向量语义匹配<br>
        与图谱邻域游走，由 LLM 融合<br>
        图谱上下文与文本片段生成回答。
        </div>
        """, unsafe_allow_html=True)
