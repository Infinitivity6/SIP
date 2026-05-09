"""数据装载与清洗。

负责把 ``data/`` 目录下的原始文本（爬虫产物的占位文件）读取、清洗、去重，
然后调用 :mod:`src.rag_engine` 的 ``insert_texts`` 录入到 LightRAG。
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Iterable

from config import DATA_DIR
from src.rag_engine import insert_texts


# --------------------------------------------------------------------------- #
# 1. 数据结构
# --------------------------------------------------------------------------- #
@dataclass
class DocItem:
    file_path: str
    content: str

    @property
    def doc_id(self) -> str:
        return hashlib.md5(self.content.encode("utf-8")).hexdigest()[:12]

    @property
    def filename(self) -> str:
        return os.path.basename(self.file_path)


# --------------------------------------------------------------------------- #
# 2. 清洗逻辑
# --------------------------------------------------------------------------- #
_INVALID_CHARS = re.compile(r"[​‌‍﻿]")  # 零宽字符
_MULTI_BLANK = re.compile(r"\n{3,}")
_TRAIL_SPACE = re.compile(r"[ \t]+\n")


def clean_text(text: str) -> str:
    """轻量清洗：去除零宽字符、收敛多余空行、去除行尾空格。"""
    if not text:
        return ""
    text = _INVALID_CHARS.sub("", text)
    text = _TRAIL_SPACE.sub("\n", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# 3. 读取 / 录入
# --------------------------------------------------------------------------- #
def iter_text_files(folder: str = DATA_DIR) -> Iterable[DocItem]:
    """遍历目录下所有 .txt 文件并返回清洗过的 DocItem。"""
    if not os.path.isdir(folder):
        return
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(folder, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="gbk", errors="ignore") as f:
                raw = f.read()
        cleaned = clean_text(raw)
        if cleaned:
            yield DocItem(file_path=path, content=cleaned)


def deduplicate(docs: Iterable[DocItem]) -> list[DocItem]:
    """根据内容 md5 去重。"""
    seen: set[str] = set()
    unique: list[DocItem] = []
    for d in docs:
        if d.doc_id in seen:
            continue
        seen.add(d.doc_id)
        unique.append(d)
    return unique


def ingest_folder(folder: str = DATA_DIR) -> dict:
    """读取 → 清洗 → 去重 → 写入 LightRAG。返回统计字典。"""
    docs = deduplicate(list(iter_text_files(folder)))
    if not docs:
        return {"folder": folder, "files": 0, "chars": 0, "doc_ids": []}

    contents = [d.content for d in docs]
    file_paths = [d.file_path for d in docs]
    insert_texts(contents, file_paths=file_paths)

    return {
        "folder": folder,
        "files": len(docs),
        "chars": sum(len(c) for c in contents),
        "doc_ids": [d.doc_id for d in docs],
        "filenames": [d.filename for d in docs],
    }


def ingest_raw_text(text: str, source_name: str = "uploaded.txt") -> dict:
    """前端上传文本时直接调用。"""
    cleaned = clean_text(text)
    if not cleaned:
        return {"files": 0, "chars": 0}
    insert_texts(cleaned, file_paths=[source_name])
    return {"files": 1, "chars": len(cleaned), "filenames": [source_name]}
