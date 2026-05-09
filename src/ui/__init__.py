"""UI 渲染模块。

将各标签页与公用组件拆分为独立文件，避免 main.py 过长。
所有全局样式集中在 theme.py，通过 apply_theme() 注入。
"""
from src.ui.components import render_knowledge_graph, render_typewriter
from src.ui.sidebar import render_sidebar
from src.ui.chat_tab import render_chat_tab
from src.ui.graph_tab import render_graph_tab
from src.ui.ingest_tab import render_ingest_tab
from src.ui.eval_tab import render_eval_tab
from src.ui.theme import apply_theme

__all__ = [
    "apply_theme",
    "render_typewriter",
    "render_knowledge_graph",
    "render_sidebar",
    "render_chat_tab",
    "render_graph_tab",
    "render_ingest_tab",
    "render_eval_tab",
]
