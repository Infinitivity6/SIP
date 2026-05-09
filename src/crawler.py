"""爬虫接口占位。

为期末项目预留的"爬虫 → 清洗 → 入库"流水线骨架。当前阶段尚未实现真实抓取，
而是把 ``data/`` 目录下手工准备的样本视为"已经爬取并清洗完成的离线数据"。

后续若要补完爬虫，只需要在 :class:`MedicalCrawler.fetch` 中调用真实数据源
（例如 39 健康网、丁香医生等）即可，下游的清洗、入库、索引、问答完全无需改动。
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Iterable, Sequence

from config import DATA_DIR
from src.data_loader import clean_text

LOG = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #
@dataclass
class CrawlItem:
    url: str
    title: str
    raw_text: str
    fetched_at: float

    @property
    def cleaned(self) -> str:
        return clean_text(self.raw_text)


# --------------------------------------------------------------------------- #
# 爬虫骨架
# --------------------------------------------------------------------------- #
class MedicalCrawler:
    """三高医疗资料爬虫的接口骨架。

    设计上对外提供 :meth:`run`，内部按 fetch → clean → save 的顺序执行，
    每一步都暴露成方法以便单测或替换实现。
    """

    DEFAULT_SOURCES: Sequence[str] = (
        "https://www.example-health.com/sangao/hypertension",
        "https://www.example-health.com/sangao/hyperglycemia",
        "https://www.example-health.com/sangao/hyperlipidemia",
    )

    def __init__(self, sources: Sequence[str] | None = None, output_dir: str = DATA_DIR):
        self.sources = list(sources or self.DEFAULT_SOURCES)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # --------------------------- 真实实现的钩子 -------------------------- #
    def fetch(self, url: str) -> CrawlItem:
        """实际网络请求。"""
        # 当前阶段的占位逻辑：从本地 data 目录里挑一个样本回放。
        sample_files = [f for f in os.listdir(self.output_dir) if f.endswith(".txt")]
        if not sample_files:
            raise RuntimeError("data 目录暂无样本文件，请先放一个 .txt 用作爬虫回放。")
        sample = os.path.join(self.output_dir, sample_files[0])
        with open(sample, "r", encoding="utf-8") as f:
            raw = f.read()
        return CrawlItem(url=url, title=os.path.basename(sample), raw_text=raw, fetched_at=time.time())

    # ------------------------------ 流水线 ------------------------------ #
    def run(self) -> list[str]:
        """执行抓取，返回保存到本地的文件路径列表。"""
        saved: list[str] = []
        for url in self.sources:
            try:
                item = self.fetch(url)
            except Exception as exc:  # noqa: BLE001
                LOG.warning("抓取失败：%s -> %s", url, exc)
                continue

            text = item.cleaned
            if not text:
                continue

            stem = os.path.splitext(item.title)[0] or "page"
            filename = f"{stem}_{int(item.fetched_at)}.txt"
            path = os.path.join(self.output_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            saved.append(path)
        return saved


def crawl_to_data_dir() -> list[str]:
    """便捷入口。返回本次落地的文件路径列表。"""
    return MedicalCrawler().run()
