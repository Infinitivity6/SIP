"""公用 UI 组件：打字机效果、知识图谱渲染、描述清理、实体类型推断。"""
from __future__ import annotations

import os
import time

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

import config


# --------------------------------------------------------------------------- #
# 打字机效果
# --------------------------------------------------------------------------- #
def render_typewriter(placeholder, text: str, chunk: int = 4, delay: float = 0.02) -> None:
    """累积式 markdown 打字机，避免单字符写入触发 markdown 错位。"""
    if not text:
        placeholder.markdown("")
        return
    buf: list[str] = []
    for i, ch in enumerate(text, 1):
        buf.append(ch)
        if i % chunk == 0:
            placeholder.markdown("".join(buf))
            time.sleep(delay)
    placeholder.markdown("".join(buf))


# --------------------------------------------------------------------------- #
# 知识图谱 pyvis 渲染
# --------------------------------------------------------------------------- #
def render_knowledge_graph(height: str = "640px") -> None:
    graph_path = os.path.join(config.WORKING_DIR, "graph_chunk_entity_relation.graphml")
    if not os.path.exists(graph_path):
        st.info("💡 暂无图谱数据。请先在「知识录入」页面录入文献。")
        return

    try:
        graph = nx.read_graphml(graph_path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"读取图谱失败：{exc}")
        return

    if graph.number_of_nodes() == 0:
        st.warning("⚠️ 图谱中没有节点，请先录入有效文献。")
        return

    # 图谱统计指标
    col1, col2, col3 = st.columns(3)
    col1.metric("🧩 实体数量", graph.number_of_nodes())
    col2.metric("🔗 关系数量", graph.number_of_edges())
    col3.metric("📐 图密度", f"{nx.density(graph):.4f}")

    st.divider()

    net = Network(
        height=height,
        width="100%",
        bgcolor="#0E1117",
        font_color="#e0e0e0",
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)

    # 手动添加节点（设置颜色、大小、截断标签）
    for node_id in graph.nodes():
        degree = graph.degree(node_id)
        raw_label = str(graph.nodes[node_id].get("label", node_id))
        label = raw_label[:28] + ("…" if len(raw_label) > 28 else "")
        size = min(35, max(10, 10 + degree * 3))
        if degree > 3:
            color = "#34d399"
        elif degree > 1:
            color = "#3b82f6"
        else:
            color = "#6b7280"
        net.add_node(
            str(node_id),
            label=label,
            size=size,
            color=color,
            borderWidth=1,
            borderWidthSelected=3,
            title=raw_label,
        )

    for src, dst in graph.edges():
        net.add_edge(
            str(src), str(dst),
            color="rgba(255,255,255,0.12)",
            width=0.8,
        )

    html_path = os.path.join(config.WORKING_DIR, "temp_graph.html")
    net.save_graph(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        components.html(f.read(), height=int(height.replace("px", "")) + 20)


# --------------------------------------------------------------------------- #
# 实体描述 / 类型推断
# --------------------------------------------------------------------------- #
def clean_desc(d: str, max_len: int = 120) -> str:
    """去除 <SEP> 分隔符，截断长文本。"""
    if not d:
        return ""
    d = d.replace("<SEP>", " | ").replace("\n", " ").strip()
    return d[:max_len] + ("…" if len(d) > max_len else "")


def infer_entity_type(name: str, etype: str) -> str:
    """LightRAG 偶有 UNKNOWN 类型，用名称关键词兜底推断。"""
    if etype and etype.upper() != "UNKNOWN":
        return etype
    if any(kw in name for kw in ["患者", "人群", "成人", "儿童", "老年人", "医师", "药师"]):
        return "人群"
    if any(kw in name for kw in ["药", "剂", "胰岛素", "他汀", "普利", "沙坦", "地平", "SGLT", "GLP", "ACEI", "ARB"]):
        return "药物"
    if any(kw in name for kw in ["糖尿病", "高血压", "高血脂", "高血糖", "病", "症", "卒中", "梗死", "综合征"]):
        return "疾病"
    if any(kw in name for kw in ["指南", "手册", "文献", "数据"]):
        return "文献"
    if any(kw in name for kw in ["饮食", "运动", "监测", "治疗", "管理", "控制"]):
        return "概念"
    return etype


def build_ref_map(refs: list[dict]) -> dict:
    """将参考文献列表转为 {ref_id: file_path} 映射。"""
    mapping: dict = {}
    for r in refs:
        if isinstance(r, dict):
            rid = r.get("id") or r.get("reference_id", 0)
            mapping[int(rid)] = r.get("file_path", f"ref-{rid}")
    return mapping


def clean_chunk_preview(text: str, max_len: int = 260) -> str:
    """清洗文档片段文本：去换行、去反引号、去开头截断的半句话。"""
    clean = text.strip().replace("\r\n", " ").replace("\n", " ").replace("`", "'")
    first_stop = min(
        (clean.find(p) for p in ("。", "！", "？", "；") if clean.find(p) >= 0),
        default=-1,
    )
    if 0 < first_stop < 30:
        clean = clean[first_stop + 1:].lstrip()
    return clean[:max_len], len(clean) > max_len
