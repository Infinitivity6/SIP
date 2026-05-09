"""LightRAG 引擎封装。

负责：
    1. 模型 / Embedding 适配器（接入硅基流动的 OpenAI 兼容接口）
    2. 持久化的后台 asyncio 事件循环（避免 Streamlit rerun 把任务杀掉）
    3. 单例风格的初始化与 ainsert / aquery 安全调用
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
from typing import Any

import numpy as np

# 自动把仓库内随附的 LightRAG 源码加入 sys.path（`D:\SIP\RAG\lightrag`）
# 这样不依赖 pip install lightrag-hku 也能跑通，对答辩演示更方便。
_BUNDLED_RAG = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir, "RAG"))
if os.path.isdir(_BUNDLED_RAG) and _BUNDLED_RAG not in sys.path:
    sys.path.insert(0, _BUNDLED_RAG)

from lightrag import LightRAG, QueryParam  # noqa: E402
from lightrag.llm.openai import openai_complete_if_cache, openai_embed  # noqa: E402
from lightrag.utils import wrap_embedding_func_with_attrs  # noqa: E402

from config import (
    API_KEY,
    BASE_URL,
    DEFAULT_CHUNK_TOP_K,
    DEFAULT_QUERY_MODE,
    DEFAULT_TOP_K,
    EMBED_BATCH,
    EMBED_DIM,
    EMBED_MAX_ASYNC,
    EMBED_MAX_TOKEN,
    EMBED_MODEL,
    ENABLE_RERANK,
    LANGUAGE,
    LLM_MAX_ASYNC,
    LLM_MODEL,
    WORKING_DIR,
)


# --------------------------------------------------------------------------- #
# 1. 持久化事件循环（防止 Streamlit rerun 时丢任务）
# --------------------------------------------------------------------------- #
_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()


def get_persistent_loop() -> asyncio.AbstractEventLoop:
    """获取/创建一个常驻后台线程中的事件循环。"""
    global _loop
    if _loop is None or _loop.is_closed():
        with _loop_lock:
            if _loop is None or _loop.is_closed():
                _loop = asyncio.new_event_loop()
                threading.Thread(target=_loop.run_forever, daemon=True).start()
    return _loop


def run_async(coro):
    """同步上下文中安全地运行协程。"""
    loop = get_persistent_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# --------------------------------------------------------------------------- #
# 2. LLM / Embedding 适配
# --------------------------------------------------------------------------- #
async def llm_model_func(
    prompt: str,
    system_prompt: str | None = None,
    history_messages: list[dict] | None = None,
    **kwargs: Any,
) -> str:
    return await openai_complete_if_cache(
        model=LLM_MODEL,
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=API_KEY,
        base_url=BASE_URL,
        **kwargs,
    )


@wrap_embedding_func_with_attrs(
    embedding_dim=EMBED_DIM,
    max_token_size=EMBED_MAX_TOKEN,
    model_name=EMBED_MODEL,
)
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed.func(
        texts,
        model=EMBED_MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
    )


# --------------------------------------------------------------------------- #
# 3. 引擎构建 / 查询封装
# --------------------------------------------------------------------------- #
_rag_instance: LightRAG | None = None


def get_rag() -> LightRAG:
    """获取（必要时初始化）LightRAG 单例。"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
            addon_params={"language": LANGUAGE},
            llm_model_max_async=LLM_MAX_ASYNC,
            embedding_func_max_async=EMBED_MAX_ASYNC,
            embedding_batch_num=EMBED_BATCH,
        )
        run_async(_rag_instance.initialize_storages())
    return _rag_instance


def insert_texts(texts: str | list[str], file_paths: list[str] | None = None) -> None:
    """同步接口：批量录入文本。"""
    rag = get_rag()
    if file_paths:
        run_async(rag.ainsert(texts, file_paths=file_paths))
    else:
        run_async(rag.ainsert(texts))


_REPLACEMENT_CHAR = "�"  # UTF-8 替换字符，对应展示中的 �

import re as _re

# 删除模型常胡乱生成的"参考文献/References"片段（小模型会编造）
_REF_BLOCK = _re.compile(
    r"(?:\n+)?(?:#{1,6}\s*)?(?:References|参考文献|引用文献|引文标明来源|参考资料|参考来源).*$",
    flags=_re.S | _re.I,
)
# 把行首的 markdown 标题前缀（# / ## / ###）打平成普通粗体行
_HEADING = _re.compile(r"^(#{1,6})\s*(.*?)$", flags=_re.M)
# 删除 [1][2] / [11 References] / [[ ]] 之类 citation 残留
_CITATION = _re.compile(r"\[\s*\d+\s*(?:Reference[s]?)?\s*\]|\[\s*\d+\s+Reference[s]?\s*\]")
_BRACKETS = _re.compile(r"\[+\s*\"+\s*\]+|\[\[+|\]\]+")
# 行尾出现的孤立 "[1" "[2" 之类没有闭合的标号
_DANGLING_BRACKET = _re.compile(r"\[\s*\d+\s*(?=\s|$|[，。；,.;])")


def sanitize_response(text: str) -> str:
    """规范化 LLM 输出，避免乱码字符与混乱排版污染前端。"""
    if not text:
        return ""
    # 1) 删除 UTF-8 替换字符
    cleaned = text.replace(_REPLACEMENT_CHAR, "")
    # 2) 删除模型自己拼出来的 References 段
    cleaned = _REF_BLOCK.sub("", cleaned)
    # 3) markdown 标题降级，避免 ### 把字号撑爆
    cleaned = _HEADING.sub(lambda m: f"**{m.group(2).strip()}**", cleaned)
    # 4) 移除引用 citation 标签
    cleaned = _CITATION.sub("", cleaned)
    cleaned = _BRACKETS.sub("", cleaned)
    cleaned = _DANGLING_BRACKET.sub("", cleaned)
    # 5) 折叠多余换行 / 行尾空白
    cleaned = _re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = _re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def query(
    question: str,
    *,
    mode: str = DEFAULT_QUERY_MODE,
    top_k: int = DEFAULT_TOP_K,
    chunk_top_k: int = DEFAULT_CHUNK_TOP_K,
    user_prompt: str | None = None,
    only_need_context: bool = False,
    conversation_history: list[dict] | None = None,
    enable_rerank: bool = ENABLE_RERANK,
) -> str:
    """统一的同步问答接口。返回值已做净化处理。"""
    rag = get_rag()
    param = QueryParam(
        mode=mode,
        top_k=top_k,
        chunk_top_k=chunk_top_k,
        user_prompt=user_prompt,
        only_need_context=only_need_context,
        conversation_history=conversation_history or [],
        enable_rerank=enable_rerank,
    )
    raw = run_async(rag.aquery(question, param=param))
    if only_need_context:
        return raw or ""
    return sanitize_response(raw or "")


def retrieve_context(
    question: str,
    *,
    mode: str = DEFAULT_QUERY_MODE,
    top_k: int = DEFAULT_TOP_K,
    chunk_top_k: int = DEFAULT_CHUNK_TOP_K,
) -> str:
    """只取检索上下文，方便评测命中率。"""
    return query(
        question,
        mode=mode,
        top_k=top_k,
        chunk_top_k=chunk_top_k,
        only_need_context=True,
    )


# --------------------------------------------------------------------------- #
# 4. 知识库元信息 / 来源解析（用于 UI 展示"参考文献"）
# --------------------------------------------------------------------------- #
import json as _json   # noqa: E402


def list_documents() -> list[dict]:
    """读取 kv_store_full_docs.json，返回当前 KB 中所有文档的元信息列表。"""
    from config import WORKING_DIR  # noqa: WPS433
    path = os.path.join(WORKING_DIR, "kv_store_full_docs.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = _json.load(f)
    except Exception:  # noqa: BLE001
        return []
    docs = []
    for doc_id, info in (raw or {}).items():
        if not isinstance(info, dict):
            continue
        content = info.get("content") or ""
        docs.append(
            {
                "doc_id": doc_id,
                "file_path": info.get("file_path") or info.get("source") or doc_id,
                "length": len(content),
                "preview": content[:80].replace("\n", " "),
            }
        )
    return docs


_SECTION_HEADERS = {
    "entities":   "Knowledge Graph Data (Entity)",
    "relations":  "Knowledge Graph Data (Relationship)",
    "chunks":     "Document Chunks",
    # 必须用足够长的前缀，否则会匹配到 Document Chunks 那行里的反引号引用
    "references": "Reference Document List (Each entry",
}


def _extract_fenced_block_after(text: str, header: str) -> str:
    """从 ``header`` 标题后第一个 ``` ... ``` 代码块中提取内容（不含围栏）。"""
    idx = text.find(header)
    if idx < 0:
        return ""
    fence_open = text.find("```", idx)
    if fence_open < 0:
        return ""
    # 跳过 ``` 后可能的语言标记（json / 空）
    body_start = text.find("\n", fence_open)
    if body_start < 0:
        return ""
    fence_close = text.find("```", body_start + 1)
    if fence_close < 0:
        return text[body_start + 1:].strip()
    return text[body_start + 1: fence_close].strip()


def parse_context_sources(context: str) -> dict:
    """解析 LightRAG ``only_need_context=True`` 的输出。

    LightRAG 把 context 渲染成下面这种结构（见 RAG/lightrag/prompt.py 的 kg_query_context）::

        Knowledge Graph Data (Entity):
        ```json
        {"id": ..., "name": "...", ...}
        {"id": ..., "name": "...", ...}
        ```

        Knowledge Graph Data (Relationship):
        ```json
        {"src": ..., "tgt": ..., ...}
        ```

        Document Chunks (...):
        ```json
        {"reference_id": 1, "content": "..."}
        ```

        Reference Document List (...):
        ```
        [1] Medicine.txt
        [2] 3high_data.txt
        ```

    我们把每一节按行解析成结构化 list，便于 UI 渲染"参考文献"。
    """
    out: dict = {"entities": [], "relations": [], "chunks": [], "references": []}
    if not context:
        return out

    # 1) 解析实体 / 关系 / 文本块（json 行）
    for key in ("entities", "relations", "chunks"):
        body = _extract_fenced_block_after(context, _SECTION_HEADERS[key])
        if not body:
            continue
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = _json.loads(line)
                if isinstance(obj, dict):
                    out[key].append(obj)
            except _json.JSONDecodeError:
                # 兜底：保留原文行
                out[key].append({"raw": line})

    # 2) 解析参考文献列表（[1] file_path），并统计每条文献被引用次数
    ref_body = _extract_fenced_block_after(context, _SECTION_HEADERS["references"])
    if ref_body:
        for line in ref_body.splitlines():
            line = line.strip()
            m = _re.match(r"\[\s*(\d+)\s*\]\s*(.+)", line)
            if m:
                out["references"].append(
                    {"id": int(m.group(1)), "file_path": m.group(2).strip()}
                )

    # 3) 统计每条文献在 chunks 中的被引次数
    chunk_ref_counts: dict[int, int] = {}
    for ch in out["chunks"]:
        ref_id = ch.get("reference_id") if isinstance(ch, dict) else None
        if ref_id is not None:
            chunk_ref_counts[int(ref_id)] = chunk_ref_counts.get(int(ref_id), 0) + 1
    for ref in out["references"]:
        rid = ref["id"]
        if rid in chunk_ref_counts:
            ref["count"] = chunk_ref_counts[rid]

    return out


def query_with_sources(
    question: str,
    *,
    mode: str = DEFAULT_QUERY_MODE,
    top_k: int = DEFAULT_TOP_K,
    chunk_top_k: int = DEFAULT_CHUNK_TOP_K,
    user_prompt: str | None = None,
    conversation_history: list[dict] | None = None,
) -> dict:
    """同时返回最终回答 + 检索来源，用于 UI 展示参考文献。

    先取检索上下文（无 LLM 调用，仅向量 + 图谱检索），再调用生成 LLM。
    这样一次 LLM 调用即可得到答案，同时保有上下文来源供 UI 展示。
    """
    ctx = ""
    sources: dict = {"entities": [], "relations": [], "chunks": [], "references": []}
    try:
        ctx = retrieve_context(question, mode=mode, top_k=top_k, chunk_top_k=chunk_top_k)
        sources = parse_context_sources(ctx)
    except Exception:  # noqa: BLE001
        pass

    answer = query(
        question,
        mode=mode,
        top_k=top_k,
        chunk_top_k=chunk_top_k,
        user_prompt=user_prompt,
        conversation_history=conversation_history,
    )
    return {"answer": answer, "sources": sources}


def get_sync_llm() -> callable:
    """返回一个同步的 LLM 调用函数，供意图分类等模块使用。"""
    def _call(prompt: str, system_prompt: str = "") -> str:
        return run_async(llm_model_func(
            prompt=prompt,
            system_prompt=system_prompt or None,
        ))
    return _call
