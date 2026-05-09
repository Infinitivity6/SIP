"""知识录入标签页：文件上传、批量导入、爬虫触发。"""
from __future__ import annotations

import os
import time

import streamlit as st

import config
from src import data_loader
from src.crawler import crawl_to_data_dir
from src.ui.theme import render_panel_title, render_section


def render_ingest_tab() -> None:
    render_section(
        "知识库录入与维护",
        "覆盖数据采集、清洗、切片、向量化与图谱抽取流程。",
        "Ingest",
    )

    ing_col1, ing_col2 = st.columns(2)

    # ── 左：上传单个文件 ──
    with ing_col1:
        with st.container(border=True):
            render_panel_title("上传文献", "支持 .txt 格式的医学文献或临床指南。")

            uploaded_file = st.file_uploader(
                "选择文件", type=["txt"], label_visibility="collapsed"
            )
            if st.button("解析并录入此文件", type="primary", width="stretch"):
                if uploaded_file is None:
                    st.error("请先选择文件")
                else:
                    text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                    with st.status("正在处理文件...", expanded=True) as ingest_status:
                        st.write("文件读取成功")
                        st.write("数据清洗中")
                        st.write("调用 LLM 提取实体与关系，耗时取决于文本长度")
                        try:
                            info = data_loader.ingest_raw_text(
                                text, source_name=uploaded_file.name
                            )
                            ingest_status.update(label="录入完成", state="complete")
                            st.success(f"已录入 1 个文档，共 {info['chars']} 字符。")
                            time.sleep(1)
                            st.rerun()
                        except Exception as exc:
                            ingest_status.update(label="录入失败", state="error")
                            st.error(f"处理失败：{exc}")

    # ── 右：批量导入 / 爬虫 ──
    with ing_col2:
        with st.container(border=True):
            render_panel_title("批量导入 / 爬虫", f"data 目录：{config.DATA_DIR}")

            if os.path.isdir(config.DATA_DIR):
                files = [f for f in os.listdir(config.DATA_DIR) if f.endswith(".txt")]
                if files:
                    preview = ", ".join(
                        f[:20] + ("..." if len(f) > 20 else "") for f in files
                    )
                    st.caption(f"当前 {len(files)} 个文件：{preview}")
                else:
                    st.caption("目录为空")

            c1, c2 = st.columns(2)
            if c1.button("一键录入 data 目录", type="primary", width="stretch"):
                with st.status("批量录入中...", expanded=True) as ingest_status:
                    try:
                        info = data_loader.ingest_folder()
                        ingest_status.update(label="批量录入完成", state="complete")
                        st.success(
                            f"录入 {info['files']} 个文件，共 {info['chars']} 字符。\n"
                            f"文件列表：{info.get('filenames', [])}"
                        )
                        time.sleep(1)
                        st.rerun()
                    except Exception as exc:
                        ingest_status.update(label="批量录入失败", state="error")
                        st.error(f"处理失败：{exc}")

            if c2.button("触发爬虫骨架", width="stretch"):
                with st.status("调用爬虫骨架...", expanded=True) as crawl_status:
                    try:
                        saved = crawl_to_data_dir()
                        crawl_status.update(label="爬虫流水线执行完毕", state="complete")
                        if saved:
                            st.success(f"本次爬虫保存了 {len(saved)} 个文件到 data 目录。")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.info("本次没有新增文件（爬虫骨架使用本地样本回放）。")
                    except Exception as exc:
                        crawl_status.update(label="爬虫执行失败", state="error")
                        st.error(f"错误：{exc}")

    # ── 底部流程说明 ──
    st.divider()
    st.markdown(
        '<div class="sip-steps">'
        '<span>文件上传</span>'
        '<span>清洗去重</span>'
        '<span>文本切片</span>'
        '<span>向量化</span>'
        '<span>图谱抽取</span>'
        '<span>可检索</span>'
        '</div>',
        unsafe_allow_html=True,
    )
