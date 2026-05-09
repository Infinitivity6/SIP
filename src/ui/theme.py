"""全局 CSS 主题与样式常量。

所有 UI 样式集中在此模块，通过 apply_theme() 注入。其他 UI 文件不应内联 CSS。
"""
from __future__ import annotations

import streamlit as st

# ── 设计令牌：色彩系统 ──────────────────────────────────────────────
_COLORS = {
    "medical-50":  "#ecfdf5",
    "medical-100": "#d1fae5",
    "medical-200": "#a7f3d0",
    "medical-300": "#6ee7b7",
    "medical-400": "#34d399",
    "medical-500": "#10b981",
    "medical-600": "#059669",
    "medical-700": "#047857",
    "medical-800": "#065f46",
    "medical-900": "#064e3b",
    "accent-blue":  "#3b82f6",
    "accent-amber": "#f59e0b",
    "accent-red":   "#ef4444",
    "surface-card": "rgba(255,255,255,0.035)",
    "border-subtle": "rgba(255,255,255,0.06)",
}

_GLOBAL_CSS = """\
/* ============================================================
   0. CSS 变量
   ============================================================ */
:root {
  --medical-50:  $$medical-50$$;
  --medical-100: $$medical-100$$;
  --medical-200: $$medical-200$$;
  --medical-300: $$medical-300$$;
  --medical-400: $$medical-400$$;
  --medical-500: $$medical-500$$;
  --medical-600: $$medical-600$$;
  --medical-700: $$medical-700$$;
  --medical-800: $$medical-800$$;
  --medical-900: $$medical-900$$;
  --accent-blue:  $$accent-blue$$;
  --accent-amber: $$accent-amber$$;
  --accent-red:   $$accent-red$$;
  --surface-card: $$surface-card$$;
  --border-subtle: $$border-subtle$$;
}

body, .stApp {
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC",
    -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ============================================================
   1. 主标题渐变
   ============================================================ */
h1 {
  background: linear-gradient(135deg, var(--medical-400), var(--accent-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
  padding-bottom: 0.1rem !important;
}

/* ============================================================
   2. 标签页导航
   ============================================================ */
section[data-testid="stTabs"] {
  margin-top: 0.6rem;
}
section[data-testid="stTabs"] button[data-baseweb="tab"] {
  font-size: 0.92rem;
  font-weight: 600;
  padding: 0.55rem 1.1rem;
  border-radius: 8px 8px 0 0;
  transition: all 0.2s ease;
}
section[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
  background: rgba(16, 185, 129, 0.08);
  color: var(--medical-300);
}
section[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(16, 185, 129, 0.12);
  color: var(--medical-400);
  border-bottom: 2px solid var(--medical-500);
}

/* ============================================================
   3. 按钮
   ============================================================ */
button[kind="primary"] {
  background: linear-gradient(135deg, var(--medical-600), var(--medical-500)) !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25) !important;
}
button[kind="primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4) !important;
}
button[kind="secondary"] {
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}

/* ============================================================
   4. 卡片
   ============================================================ */
.sip-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.7rem;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.sip-card:hover {
  border-color: rgba(16, 185, 129, 0.2);
  box-shadow: 0 2px 12px rgba(16, 185, 129, 0.06);
}

/* ============================================================
   5. 输入 / 选择控件
   ============================================================ */
div[data-baseweb="select"] > div {
  border-radius: 8px !important;
}
input[data-baseweb="input"], textarea[data-baseweb="textarea"] {
  border-radius: 8px !important;
}

/* ============================================================
   6. 侧边栏
   ============================================================ */
section[data-testid="stSidebar"] {
  border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stMetric {
  background: rgba(255,255,255,0.025);
  border-radius: 8px;
  padding: 0.5rem 0.7rem;
}

/* ============================================================
   7. Expander
   ============================================================ */
details[data-testid="stExpander"] {
  border-radius: 10px !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  transition: border-color 0.2s ease !important;
}
details[data-testid="stExpander"]:hover {
  border-color: rgba(16, 185, 129, 0.15) !important;
}

/* ============================================================
   8. Metric 指标卡
   ============================================================ */
div[data-testid="stMetric"] {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 0.7rem 1rem;
  transition: border-color 0.25s ease;
}
div[data-testid="stMetric"]:hover {
  border-color: rgba(16, 185, 129, 0.2);
}

/* ============================================================
   9. 滚动条
   ============================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }

/* ============================================================
   10. 状态 / 分割线
   ============================================================ */
div[data-testid="stStatus"] {
  border-radius: 10px !important;
}
hr {
  border-color: rgba(255,255,255,0.06) !important;
  margin: 0.8rem 0 !important;
}

/* ============================================================
   11. 快捷建议 chip
   ============================================================ */
.sip-chip {
  display: inline-block;
  padding: 0.45rem 1rem;
  margin: 0.25rem 0.35rem 0.25rem 0;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.18);
  border-radius: 20px;
  font-size: 0.85rem;
  color: var(--medical-300);
  cursor: pointer;
  transition: all 0.22s ease;
  white-space: nowrap;
}
.sip-chip:hover {
  background: rgba(16, 185, 129, 0.18);
  border-color: var(--medical-500);
  color: var(--medical-200);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

/* ============================================================
   12. 知识库文档条目
   ============================================================ */
.sip-doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  font-size: 0.83rem;
  transition: background 0.2s ease;
}
.sip-doc-item:hover { background: rgba(255,255,255,0.02); }
.sip-doc-name {
  font-family: "JetBrains Mono", "Cascadia Code", monospace;
  font-size: 0.78rem;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sip-doc-size {
  opacity: 0.4;
  font-size: 0.73rem;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

/* ============================================================
   13. 评测指标颜色
   ============================================================ */
.sip-metric-high { color: var(--medical-400); }
.sip-metric-mid  { color: var(--accent-amber); }
.sip-metric-low  { color: var(--accent-red); }

/* ============================================================
   14. 空状态占位
   ============================================================ */
.sip-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  color: rgba(255,255,255,0.3);
  text-align: center;
}
.sip-empty-icon { font-size: 3rem; margin-bottom: 0.8rem; }
.sip-empty-text { font-size: 0.9rem; max-width: 320px; line-height: 1.6; }

/* ============================================================
   15. 流程步骤条
   ============================================================ */
.sip-steps {
  display: flex;
  gap: 0.6rem;
  justify-content: center;
  opacity: 0.4;
  font-size: 0.78rem;
  padding: 0.5rem 0;
  flex-wrap: wrap;
}
.sip-steps span { white-space: nowrap; }

/* ============================================================
   16. 脉冲动画
   ============================================================ */
@keyframes sipPulse {
  0%, 100% { opacity: 0.6; }
  50%      { opacity: 1; }
}
.sip-loading { animation: sipPulse 1.6s ease-in-out infinite; }
"""

_CHAT_CSS = """\
/* ── 聊天页布局：消息区充盈视口 / 输入框固定底部 ── */
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
  background: #0e1117 !important;
  padding-top: 0.4rem !important;
  padding-bottom: 0.5rem !important;
}
section[data-testid="stMain"] .stChatMessage {
  overflow-y: visible;
}
/* ── 聊天消息气泡微调 ── */
section[data-testid="stMain"] [data-testid="stChatMessage"] {
  padding: 0.5rem 0.8rem;
  border-radius: 12px;
  margin-bottom: 0.3rem;
}
"""


def apply_theme(*, include_chat_layout: bool = False) -> None:
    """注入全局 CSS 主题。

    Args:
        include_chat_layout: 仅在聊天页设为 True，避免影响其他标签页的 flex 布局。
    """
    css = _GLOBAL_CSS
    for key, value in _COLORS.items():
        css = css.replace(f"$${key}$$", value)
    if include_chat_layout:
        css += _CHAT_CSS
    st.html(f"<style>{css}</style>")
