"""智能问答标签页：意图识别 → GraphRAG 检索 → 打字机输出 → 参考文献展示。"""
from __future__ import annotations

import time

import streamlit as st

from src.intent_classifier import classify, extract_diseases
from src.prompt_templates import for_intent
from src.rag_engine import get_sync_llm, list_documents, query_with_sources
from src.ui.components import (
    build_ref_map,
    clean_chunk_preview,
    clean_desc,
    infer_entity_type,
    render_typewriter,
)
from src.ui.theme import apply_theme

# ── 快捷提问建议 ──────────────────────────────────────────────────
_SUGGESTION_CHIPS = [
    ("🥦", "高血压患者饮食上有哪些禁忌？"),
    ("💊", "降压药有哪些常见副作用？"),
    ("⚠️", "高血糖会引起哪些并发症？"),
    ("🏃", "高血脂患者适合什么运动？"),
    ("📈", "血压多少算正常？"),
    ("🌙", "三高人群如何调整生活作息？"),
]


def _render_sources(sources: dict) -> None:
    """渲染「参考来源」+「检索详情」（历史消息 & 实时回答共用）。"""
    refs = sources.get("references", [])
    chk = sources.get("chunks", []) or []
    ent_cnt = len(sources.get("entities", []))
    rel_cnt = len(sources.get("relations", []))

    if not refs and not chk:
        return

    st.divider()

    st.markdown(
        '<div style="display:flex;align-items:center;gap:0.35rem;margin-bottom:0.4rem;">'
        '<span style="font-size:0.9rem;">📖</span>'
        '<span style="font-weight:600;font-size:0.85rem;opacity:0.7;">参考来源</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if refs:
        ref_lines = []
        for idx, r in enumerate(refs, 1):
            fname = r.get("file_path", "unknown") if isinstance(r, dict) else str(r)
            count = r.get("count") if isinstance(r, dict) else None
            extra = (
                f' <span style="opacity:0.45;font-size:0.78rem;">'
                f'（引用 {count} 次）</span>'
                if count else ""
            )
            ref_lines.append(
                f'{idx}. <code style="font-size:0.8rem;">{fname}</code>{extra}'
            )
        st.markdown("\n".join(ref_lines))

    if chk or ent_cnt or rel_cnt:
        ref_map = build_ref_map(refs)
        detail_parts = []
        if chk:
            detail_parts.append(f"{len(chk)} 片段")
        if ent_cnt:
            detail_parts.append(f"{ent_cnt} 实体")
        if rel_cnt:
            detail_parts.append(f"{rel_cnt} 关系")

        with st.expander(
            f"🔍 检索详情（{' / '.join(detail_parts)}）", expanded=False
        ):
            if chk:
                st.markdown("**文档片段**")
                for i, piece in enumerate(chk[:5], 1):
                    if isinstance(piece, dict):
                        rid = int(piece.get("reference_id") or 0)
                        fname = ref_map.get(rid) or piece.get("file_path") or ""
                        text = piece.get("content") or piece.get("raw") or ""
                    else:
                        fname = ""
                        text = str(piece)
                    preview, truncated = clean_chunk_preview(text)
                    header = f"**{i}. {fname}**" if fname else f"**{i}.**"
                    st.markdown(f"{header}")
                    st.html(
                        f"<blockquote style='opacity:0.78;margin:0 0 0.4rem 0;"
                        f"padding:0.3rem 0.9rem;border-left:3px solid #34d399;"
                        f"border-radius:0 6px 6px 0;"
                        f"background:rgba(16,185,129,0.04);'>"
                        f"{preview}{'…' if truncated else ''}</blockquote>"
                    )
            if ent_cnt:
                st.markdown("**命中实体**")
                ent_lines: list[str] = []
                for e in sources["entities"][:6]:
                    if isinstance(e, dict):
                        name = (
                            e.get("entity") or e.get("name")
                            or e.get("entity_name", "?")
                        )
                        etype = infer_entity_type(
                            name, e.get("type") or e.get("entity_type", "")
                        )
                        desc = clean_desc(e.get("description", ""))
                        tag = f"`{etype}` " if etype else ""
                        ent_lines.append(
                            f"- {tag}**{name}**{'：' + desc if desc else ''}"
                        )
                    else:
                        ent_lines.append(f"- {str(e)[:200]}")
                if ent_lines:
                    st.markdown("\n".join(ent_lines))
            if rel_cnt:
                st.markdown("**命中关系**")
                rel_lines: list[str] = []
                for r in sources["relations"][:6]:
                    if isinstance(r, dict):
                        src = r.get("entity1") or r.get("src") or "?"
                        tgt = r.get("entity2") or r.get("tgt") or "?"
                        desc = clean_desc(r.get("description", ""))
                        rel_lines.append(
                            f"- **{src}** → **{tgt}**"
                            f"{'：' + desc if desc else ''}"
                        )
                    else:
                        rel_lines.append(f"- {str(r)[:200]}")
                if rel_lines:
                    st.markdown("\n".join(rel_lines))


# --------------------------------------------------------------------------- #
# 主渲染函数
# --------------------------------------------------------------------------- #
def render_chat_tab() -> None:
    # 注入聊天页专属布局 CSS（flex + sticky 输入框）
    apply_theme(include_chat_layout=True)

    # ── 初始化消息历史 ──
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "您好！我是三高智能健康顾问 🏥\n\n"
                    "我已学习底层医学知识图谱，涵盖 **高血压 / 高血糖 / 高血脂** "
                    "的防治指南、用药手册、饮食营养、运动方案及并发症管理等专题。\n\n"
                    "请随时提出您的问题，我会基于知识库为您提供专业、克制的回答。"
                ),
            }
        ]

    # ── 知识库空状态 ──
    kb_docs = list_documents()
    if not kb_docs:
        st.warning(
            "**知识库尚未初始化** — 当前系统只能依靠模型自身知识回答，"
            "回答可能不够精准且有幻觉风险。请先录入医学文献。"
        )
        init_col1, init_col2, init_col3 = st.columns([1, 1, 3])
        with init_col1:
            if st.button("一键初始化知识库", type="primary", width="stretch"):
                from src import data_loader

                with st.status(
                    "正在录入 data 目录全部文献（抽取实体/关系耗时较长）...",
                    expanded=True,
                ) as s:
                    try:
                        info = data_loader.ingest_folder()
                        s.update(
                            label=f"初始化完成：录入 {info['files']} 篇文献，"
                                  f"{info['chars']} 字符",
                            state="complete",
                        )
                        st.success(
                            f"已录入 {info['files']} 篇文献，可开始问答。"
                        )
                        time.sleep(1)
                        st.rerun()
                    except Exception as exc:
                        s.update(label="初始化失败", state="error")
                        st.error(f"录入出错：{exc}")
        with init_col2:
            if st.button("跳转到录入页", width="stretch"):
                st.session_state._tab_idx = 2
                st.rerun()
        st.divider()

    # ── 控制条 ──
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
    with ctrl_col1:
        force_mode = st.selectbox(
            "检索模式",
            options=[
                "自动 (基于意图)", "hybrid", "mix", "local", "global", "naive"
            ],
            index=0,
            help=(
                "hybrid=图谱+向量混合 / mix=KG集成检索 / "
                "local=局部实体检索 / global=全局摘要检索 / naive=纯向量检索"
            ),
        )
    with ctrl_col2:
        show_intent = st.checkbox("显示意图与策略", value=True)
    with ctrl_col3:
        if st.button("🗑️ 清空对话", width="stretch"):
            st.session_state.messages = st.session_state.messages[:1]
            st.session_state.chat_started = False
            st.rerun()

    # ── 首次加载：欢迎区 + 快捷提问 ──
    if not st.session_state.get("chat_started"):
        st.markdown("<div style='height:6vh;'></div>", unsafe_allow_html=True)

        st.markdown(
            '<p style="font-size:0.85rem;opacity:0.55;margin-bottom:0.4rem;">'
            '💡 试试这些问题：</p>',
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(3)
        for i, (icon, question) in enumerate(_SUGGESTION_CHIPS):
            with chip_cols[i % 3]:
                if st.button(
                    f"{icon}  {question}",
                    key=f"suggest_{i}",
                    width="stretch",
                    help=f"点击提问：{question}",
                ):
                    st.session_state.chat_started = True
                    st.session_state._pending_question = question
                    st.rerun()

        st.markdown("<div style='height:3vh;'></div>", unsafe_allow_html=True)

    # ── 消息历史 ──
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            _render_sources(msg["sources"])

    # ── 输入 ──
    user_input = st.chat_input("例如：高血压患者饮食上有哪些禁忌？")

    # 来自快捷提问的待处理问题
    pending = st.session_state.pop("_pending_question", None)
    if pending and not user_input:
        user_input = pending

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        if not pending:
            st.session_state.messages.append(
                {"role": "user", "content": user_input}
            )

        with st.chat_message("assistant"):
            intent = classify(user_input, llm_call=get_sync_llm())
            diseases = extract_diseases(user_input)
            strategy = for_intent(intent.label)

            if show_intent:
                with st.expander("🧠 意图与策略", expanded=False):
                    st.json(
                        {
                            "意图": intent.to_dict(),
                            "命中疾病": diseases,
                            "推荐检索模式": strategy.mode,
                            "top_k": strategy.top_k,
                            "chunk_top_k": strategy.chunk_top_k,
                        }
                    )

            mode = strategy.mode if force_mode.startswith("自动") else force_mode

            with st.status("正在检索...", expanded=True) as st_status:
                st.write(
                    f"意图：{intent.display} → "
                    f"模式：{mode} (top_k={strategy.top_k})"
                )
                history = [
                    m
                    for m in st.session_state.messages
                    if m["role"] in ("user", "assistant")
                ][-6:]

                t0 = time.time()
                answer: str | None = None
                sources: dict = {
                    "entities": [], "relations": [],
                    "chunks": [], "references": [],
                }
                err_msg: str | None = None
                try:
                    bundle = query_with_sources(
                        user_input,
                        mode=mode,
                        top_k=strategy.top_k,
                        chunk_top_k=strategy.chunk_top_k,
                        user_prompt=strategy.user_prompt,
                        conversation_history=history,
                    )
                    answer = bundle["answer"]
                    sources = bundle["sources"]
                    elapsed = time.time() - t0
                    st_status.update(
                        label=f"检索完成（{elapsed:.1f}s）",
                        state="complete",
                        expanded=False,
                    )
                except Exception as exc:
                    err_msg = str(exc)
                    st_status.update(
                        label="检索失败", state="error", expanded=True
                    )

            if err_msg:
                st.error(
                    f"系统错误：{err_msg}\n\n"
                    "若错误提示包含 `proxies`，多半是 openai/httpx 版本冲突，"
                    "执行 `pip install -U openai` 或 "
                    '`pip install "httpx<0.28"` 即可解决。'
                )
                return
            if not answer or not answer.strip():
                st.warning(
                    "⚠️ 模型返回了空回答。常见原因：\n"
                    "- LLM 调用失败（请查看终端日志）\n"
                    "- 知识库尚未录入数据\n"
                    "- 检索模式与意图不匹配，可手动切换 mode 重试"
                )
                return

            placeholder = st.empty()
            render_typewriter(placeholder, answer)
            _render_sources(sources)

            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
            st.session_state.chat_started = True
            st.rerun()
