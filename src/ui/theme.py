"""全局 CSS 主题与样式常量。

所有 UI 样式集中在此模块，通过 apply_theme() 注入。其他 UI 文件不应内联 CSS。
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

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
  background:
    radial-gradient(circle at 12% -10%, rgba(16,185,129,0.12), transparent 24rem),
    radial-gradient(circle at 88% 2%, rgba(59,130,246,0.045), transparent 30rem),
    #0e1117 !important;
}

section[data-testid="stMain"] {
  background:
    linear-gradient(90deg, rgba(14,17,23,0.98), rgba(14,17,23,0.94)),
    #0e1117 !important;
}

section[data-testid="stMain"] .block-container {
  max-width: 1360px;
  padding-top: 0.9rem;
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
  margin-top: 1rem;
  padding: 0.45rem 0.5rem 0;
  border: 1px solid rgba(16,185,129,0.16);
  border-radius: 16px 16px 0 0;
  background:
    linear-gradient(135deg, rgba(16,185,129,0.10), rgba(59,130,246,0.055)),
    rgba(255,255,255,0.026);
  box-shadow: 0 16px 38px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.04);
}
section[data-testid="stTabs"] div[data-baseweb="tab-list"] {
  gap: 0.35rem;
}
section[data-testid="stTabs"] button[data-baseweb="tab"] {
  font-size: 1.08rem;
  font-weight: 800;
  padding: 0.9rem 1.75rem;
  min-height: 3.7rem;
  border-radius: 12px 12px 0 0;
  border: 1px solid rgba(255,255,255,0.075);
  margin-right: 0.25rem;
  transition: all 0.2s ease;
  background: rgba(255,255,255,0.035);
}
section[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
  background: rgba(16, 185, 129, 0.12);
  color: var(--medical-300);
  transform: translateY(-1px);
}
section[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(16,185,129,0.22), rgba(59,130,246,0.16));
  color: var(--medical-400);
  border-color: rgba(16,185,129,0.32);
  border-bottom: 3px solid var(--medical-500);
  box-shadow: 0 6px 18px rgba(16,185,129,0.12);
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
div[data-testid="stButton"] button {
  min-height: 2.65rem;
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
  border-right: 1px solid rgba(255,255,255,0.07);
  background:
    radial-gradient(circle at 50% 0%, rgba(16,185,129,0.08), transparent 16rem),
    rgba(14,17,23,0.98) !important;
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
button[title^="点击提问"] {
  min-height: 3.25rem !important;
  white-space: normal !important;
  background: linear-gradient(135deg, rgba(16,185,129,0.11), rgba(59,130,246,0.055)) !important;
  border-color: rgba(16,185,129,0.22) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.035);
}
button[title^="点击提问"]:hover {
  background: rgba(16,185,129,0.15) !important;
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
  gap: 0.8rem;
  justify-content: center;
  align-items: center;
  font-size: 0.88rem;
  padding: 0.95rem 0 0.4rem;
  flex-wrap: wrap;
}
.sip-steps__item {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  white-space: nowrap;
  border: 1px solid rgba(16,185,129,0.24);
  background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(59,130,246,0.06));
  border-radius: 999px;
  padding: 0.48rem 0.82rem;
  color: rgba(255,255,255,0.88);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}
.sip-steps__item strong {
  font-weight: 800;
  color: var(--medical-200);
}
.sip-steps__arrow {
  color: var(--medical-400);
  opacity: 0.78;
  font-weight: 800;
  transform: translateY(-1px);
}
@media (max-width: 760px) {
  .sip-steps {
    justify-content: flex-start;
  }
  .sip-steps__arrow {
    display: none;
  }
}

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
  background: linear-gradient(180deg, rgba(14,17,23,0), #0e1117 28%) !important;
  padding-top: 0.9rem !important;
  padding-bottom: 0.7rem !important;
}
section[data-testid="stMain"] .stChatMessage {
  overflow-y: visible;
}
/* ── 聊天消息气泡微调 ── */
section[data-testid="stMain"] [data-testid="stChatMessage"] {
  padding: 0.62rem 0.85rem;
  border-radius: 12px;
  margin-bottom: 0.45rem;
  border: 1px solid rgba(255,255,255,0.055);
  background: rgba(255,255,255,0.026);
}
section[data-testid="stMain"] [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  border-color: rgba(59,130,246,0.16);
  background: linear-gradient(135deg, rgba(59,130,246,0.10), rgba(16,185,129,0.045));
}
section[data-testid="stMain"] [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  border-color: rgba(16,185,129,0.12);
  background: rgba(255,255,255,0.03);
}
section[data-testid="stMain"] [data-testid="stChatInput"] {
  border: 1px solid rgba(16,185,129,0.30);
  border-radius: 16px;
  background: rgba(12,16,23,0.96);
  box-shadow: 0 14px 34px rgba(0,0,0,0.32), 0 0 0 1px rgba(59,130,246,0.10);
}
section[data-testid="stMain"] [data-testid="stChatInput"] textarea {
  background: transparent !important;
  min-height: 3rem !important;
  font-size: 0.98rem !important;
}
"""

_SIDEBAR_DEFAULT_OPEN_HTML = """\
<script>
(function () {
  var USER_COLLAPSED_KEY = "sip_sidebar_user_collapsed";
  var autoOpening = false;
  var seenExpanded = false;
  try {
    window.sessionStorage.removeItem("sip_sidebar_default_open_checked");
  } catch (e) {}

  function getDoc() {
    return window.parent && window.parent.document;
  }

  function sidebarWidth(doc) {
    var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
    return sidebar ? sidebar.getBoundingClientRect().width : 0;
  }

  function openIfNeeded() {
    var doc = window.parent && window.parent.document;
    if (!doc) return false;

    var width = sidebarWidth(doc);
    if (width >= 160) {
      seenExpanded = true;
      try {
        window.sessionStorage.removeItem(USER_COLLAPSED_KEY);
      } catch (e) {}
      return true;
    }

    try {
      if (window.sessionStorage.getItem(USER_COLLAPSED_KEY) === "1") return true;
    } catch (e) {}

    var openButton = doc.querySelector('button[data-testid="collapsedControl"]');
    if (openButton) {
      autoOpening = true;
      openButton.click();
      window.setTimeout(function () { autoOpening = false; }, 500);
      return true;
    }

    return false;
  }

  function monitorUserCollapse() {
    var doc = getDoc();
    if (!doc) return;
    var width = sidebarWidth(doc);

    if (width >= 160) {
      seenExpanded = true;
      try {
        window.sessionStorage.removeItem(USER_COLLAPSED_KEY);
      } catch (e) {}
      return;
    }

    if (seenExpanded && width < 120 && !autoOpening) {
      try {
        window.sessionStorage.setItem(USER_COLLAPSED_KEY, "1");
      } catch (e) {}
    }
  }

  var openAttempts = 0;
  var openTimer = window.setInterval(function () {
    openAttempts += 1;
    var done = openIfNeeded();
    if (done || openAttempts >= 40) window.clearInterval(openTimer);
  }, 150);

  window.setInterval(monitorUserCollapse, 400);
})();
</script>
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
    components.html(_SIDEBAR_DEFAULT_OPEN_HTML, height=0, width=0)
