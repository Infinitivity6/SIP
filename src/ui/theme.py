"""全局 UI 主题与小型语义组件。

样式集中在此模块，页面文件只表达结构与业务状态，避免把 CSS 散落在逻辑中。
"""
from __future__ import annotations

import html

import streamlit as st


_COLORS = {
    "bg": "#101413",
    "bg-soft": "#151a18",
    "panel": "rgba(244, 239, 226, 0.055)",
    "panel-strong": "rgba(244, 239, 226, 0.085)",
    "text": "#f0eadc",
    "muted": "rgba(240, 234, 220, 0.62)",
    "faint": "rgba(240, 234, 220, 0.38)",
    "line": "rgba(240, 234, 220, 0.12)",
    "line-strong": "rgba(240, 234, 220, 0.22)",
    "green": "#7fc7a4",
    "green-deep": "#2f6f59",
    "amber": "#d8a35d",
    "red": "#d36b62",
    "blue": "#8fb7c8",
    "ink": "#080b0a",
}

_GLOBAL_CSS = """\
:root {
  --sip-bg: $$bg$$;
  --sip-bg-soft: $$bg-soft$$;
  --sip-panel: $$panel$$;
  --sip-panel-strong: $$panel-strong$$;
  --sip-text: $$text$$;
  --sip-muted: $$muted$$;
  --sip-faint: $$faint$$;
  --sip-line: $$line$$;
  --sip-line-strong: $$line-strong$$;
  --sip-green: $$green$$;
  --sip-green-deep: $$green-deep$$;
  --sip-amber: $$amber$$;
  --sip-red: $$red$$;
  --sip-blue: $$blue$$;
  --sip-ink: $$ink$$;
  --sip-radius: 8px;
}

html, body, .stApp {
  color: var(--sip-text) !important;
  background:
    radial-gradient(circle at 15% -10%, rgba(127,199,164,0.10), transparent 28rem),
    linear-gradient(180deg, #111513 0%, #0d1110 55%, #0b0e0d 100%) !important;
  font-family: "Aptos", "Segoe UI", "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(240,234,220,0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(240,234,220,0.03) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(180deg, rgba(0,0,0,0.85), transparent 70%);
  z-index: 0;
}

section[data-testid="stMain"] .block-container {
  max-width: 1280px;
  padding-top: 1.6rem;
  padding-bottom: 2.2rem;
  position: relative;
  z-index: 1;
}

h1, h2, h3, h4 {
  color: var(--sip-text) !important;
  letter-spacing: 0 !important;
}

h1 {
  font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif !important;
  font-size: clamp(2.0rem, 3vw, 3.05rem) !important;
  font-weight: 600 !important;
  line-height: 1.05 !important;
  margin-bottom: 0.25rem !important;
}

h3 {
  font-size: 1.15rem !important;
}

p, li, label, [data-testid="stMarkdownContainer"] {
  line-height: 1.72;
}

a { color: var(--sip-green) !important; }

code {
  color: #e7d6ad !important;
  background: rgba(216,163,93,0.12) !important;
  border: 1px solid rgba(216,163,93,0.14);
  border-radius: 5px;
  padding: 0.05rem 0.28rem;
}

hr {
  border-color: var(--sip-line) !important;
  margin: 1rem 0 !important;
}

/* App header */
.sip-hero {
  border: 1px solid var(--sip-line);
  background:
    linear-gradient(135deg, rgba(244,239,226,0.08), rgba(244,239,226,0.025)),
    radial-gradient(circle at 88% 8%, rgba(127,199,164,0.12), transparent 18rem);
  border-radius: var(--sip-radius);
  padding: 1.35rem 1.45rem 1.25rem;
  margin-bottom: 1rem;
  box-shadow: 0 18px 45px rgba(0,0,0,0.22);
}
.sip-hero-kicker,
.sip-section-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--sip-green);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.sip-hero-title {
  font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
  font-size: clamp(2.0rem, 3vw, 3.0rem);
  line-height: 1.06;
  margin: 0.28rem 0 0.45rem;
}
.sip-hero-copy {
  max-width: 760px;
  color: var(--sip-muted);
  font-size: 0.98rem;
}
.sip-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.9rem;
}
.sip-pill {
  border: 1px solid var(--sip-line);
  color: rgba(240,234,220,0.78);
  background: rgba(0,0,0,0.12);
  border-radius: 999px;
  padding: 0.22rem 0.62rem;
  font-size: 0.78rem;
}

/* Navigation tabs */
section[data-testid="stTabs"] { margin-top: 0.4rem; }
section[data-testid="stTabs"] button[data-baseweb="tab"] {
  min-height: 2.65rem;
  padding: 0.45rem 1rem;
  border-radius: var(--sip-radius) var(--sip-radius) 0 0;
  color: var(--sip-muted);
  border: 1px solid transparent;
  font-weight: 650;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}
section[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
  background: rgba(244,239,226,0.045);
  color: var(--sip-text);
}
section[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(127,199,164,0.10);
  color: var(--sip-green);
  border-color: rgba(127,199,164,0.22);
}

/* Native controls */
button[kind="primary"] {
  background: var(--sip-green) !important;
  color: var(--sip-ink) !important;
  border: 1px solid rgba(127,199,164,0.55) !important;
  border-radius: var(--sip-radius) !important;
  font-weight: 750 !important;
  box-shadow: 0 10px 24px rgba(127,199,164,0.15) !important;
}
button[kind="secondary"] {
  background: rgba(244,239,226,0.045) !important;
  color: var(--sip-text) !important;
  border: 1px solid var(--sip-line) !important;
  border-radius: var(--sip-radius) !important;
  font-weight: 650 !important;
}
button:hover {
  transform: translateY(-1px);
  border-color: var(--sip-line-strong) !important;
}
div[data-baseweb="select"] > div,
input,
textarea,
[data-testid="stFileUploader"] section {
  border-radius: var(--sip-radius) !important;
  border-color: var(--sip-line) !important;
  background: rgba(244,239,226,0.04) !important;
}

/* Containers and cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--sip-line) !important;
  background: rgba(244,239,226,0.035) !important;
  border-radius: var(--sip-radius) !important;
}
.sip-panel-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.3rem;
}
.sip-panel-title strong {
  font-size: 1.02rem;
}
.sip-muted {
  color: var(--sip-muted);
  font-size: 0.88rem;
}
.sip-micro {
  color: var(--sip-faint);
  font-size: 0.75rem;
}
.sip-section {
  margin: 0.1rem 0 0.8rem;
}
.sip-section h3 {
  margin: 0.1rem 0 0.2rem !important;
}

/* Metrics, status, expanders */
div[data-testid="stMetric"] {
  background: rgba(244,239,226,0.04);
  border: 1px solid var(--sip-line);
  border-radius: var(--sip-radius);
  padding: 0.78rem 0.9rem;
}
div[data-testid="stMetricValue"] {
  color: var(--sip-text);
  font-family: "Georgia", "Times New Roman", serif;
}
details[data-testid="stExpander"],
div[data-testid="stStatus"] {
  border-color: var(--sip-line) !important;
  border-radius: var(--sip-radius) !important;
  background: rgba(244,239,226,0.035) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111614, #0d1110) !important;
  border-right: 1px solid var(--sip-line);
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
  font-size: 0.88rem;
}
.sip-sidebar-brand {
  border-bottom: 1px solid var(--sip-line);
  padding: 0.25rem 0 0.85rem;
  margin-bottom: 0.8rem;
}
.sip-sidebar-brand-title {
  font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
  font-size: 1.24rem;
  line-height: 1.15;
  margin: 0.2rem 0;
}
.sip-sidebar-card {
  border: 1px solid var(--sip-line);
  background: rgba(244,239,226,0.04);
  border-radius: var(--sip-radius);
  padding: 0.75rem 0.82rem;
  margin-bottom: 0.7rem;
}
.sip-sidebar-row {
  display: grid;
  grid-template-columns: 5.2rem minmax(0, 1fr);
  gap: 0.55rem;
  padding: 0.25rem 0;
}
.sip-sidebar-row span:first-child {
  color: var(--sip-faint);
}
.sip-sidebar-row span:last-child {
  overflow-wrap: anywhere;
}
.sip-doc-list {
  border: 1px solid var(--sip-line);
  border-radius: var(--sip-radius);
  overflow: hidden;
  background: rgba(0,0,0,0.10);
  margin: 0.45rem 0 0.65rem;
}
.sip-doc-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.7rem;
  padding: 0.48rem 0.62rem;
  border-bottom: 1px solid rgba(240,234,220,0.08);
}
.sip-doc-item:last-child { border-bottom: 0; }
.sip-doc-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.80rem;
}
.sip-doc-size {
  color: var(--sip-faint);
  font-size: 0.74rem;
  white-space: nowrap;
}

/* Chat */
[data-testid="stChatMessage"] {
  border: 1px solid rgba(240,234,220,0.09);
  background: rgba(244,239,226,0.035);
  border-radius: var(--sip-radius);
  margin-bottom: 0.55rem;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: rgba(127,199,164,0.07);
}
.sip-source-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--sip-muted);
  font-weight: 700;
  font-size: 0.84rem;
  margin-bottom: 0.45rem;
}
.sip-quote {
  margin: 0 0 0.48rem;
  padding: 0.48rem 0.75rem;
  border-left: 3px solid var(--sip-green);
  border-radius: 0 var(--sip-radius) var(--sip-radius) 0;
  background: rgba(127,199,164,0.055);
  color: rgba(240,234,220,0.78);
}

/* Process strip */
.sip-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 0.42rem;
  color: var(--sip-muted);
  font-size: 0.8rem;
}
.sip-steps span {
  border: 1px solid var(--sip-line);
  border-radius: 999px;
  padding: 0.22rem 0.58rem;
  background: rgba(244,239,226,0.035);
}

/* Dataframes and charts */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
  border: 1px solid var(--sip-line);
  border-radius: var(--sip-radius);
  overflow: hidden;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(240,234,220,0.16);
  border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(240,234,220,0.25); }
"""

_CHAT_CSS = """\
section[data-testid="stMain"] .block-container {
  display: flex !important;
  flex-direction: column !important;
  min-height: calc(100vh - 3.6rem) !important;
}
section[data-testid="stMain"] .block-container > div:has(.stChatInput) {
  margin-top: auto !important;
  position: sticky !important;
  bottom: 0 !important;
  z-index: 10 !important;
  background: linear-gradient(180deg, rgba(16,20,19,0), var(--sip-bg) 22%) !important;
  padding-top: 1rem !important;
  padding-bottom: 0.55rem !important;
}
"""


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def apply_theme(*, include_chat_layout: bool = False) -> None:
    """注入全局 CSS 主题。"""
    css = _GLOBAL_CSS
    for key, value in _COLORS.items():
        css = css.replace(f"$${key}$$", value)
    if include_chat_layout:
        css += _CHAT_CSS
    st.html(f"<style>{css}</style>")


def render_app_header() -> None:
    """渲染应用顶栏，替代默认大标题与说明文字。"""
    st.markdown(
        """
        <section class="sip-hero">
          <div class="sip-hero-kicker">GraphRAG clinical desk</div>
          <div class="sip-hero-title">三高知识智能问答平台</div>
          <div class="sip-hero-copy">
            面向高血压、高血糖、高血脂的课程级医学知识工作台。检索、来源、图谱与评测放在同一界面中，方便演示和复盘。
          </div>
          <div class="sip-hero-meta">
            <span class="sip-pill">LightRAG</span>
            <span class="sip-pill">知识图谱</span>
            <span class="sip-pill">来源可追溯</span>
            <span class="sip-pill">自动评测</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str, caption: str | None = None, kicker: str | None = None) -> None:
    """渲染页面内章节标题。"""
    safe_title = _escape(title)
    safe_caption = _escape(caption or "")
    safe_kicker = _escape(kicker or "Workspace")
    caption_html = f'<div class="sip-muted">{safe_caption}</div>' if caption else ""
    st.markdown(
        f"""
        <section class="sip-section">
          <div class="sip-section-kicker">{safe_kicker}</div>
          <h3>{safe_title}</h3>
          {caption_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_panel_title(title: str, caption: str | None = None) -> None:
    """渲染容器内部标题。"""
    safe_title = _escape(title)
    safe_caption = _escape(caption or "")
    caption_html = f'<div class="sip-muted">{safe_caption}</div>' if caption else ""
    st.markdown(
        f'<div class="sip-panel-title"><strong>{safe_title}</strong></div>{caption_html}',
        unsafe_allow_html=True,
    )


def render_microcopy(text: str) -> None:
    st.markdown(f'<div class="sip-micro">{_escape(text)}</div>', unsafe_allow_html=True)


def render_source_quote(text: str) -> None:
    st.markdown(f'<blockquote class="sip-quote">{_escape(text)}</blockquote>', unsafe_allow_html=True)
