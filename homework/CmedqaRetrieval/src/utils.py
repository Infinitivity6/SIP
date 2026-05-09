"""
utils.py — 通用工具函数
"""

import json
import time
from pathlib import Path
from contextlib import contextmanager


def save_jsonl(data: list, path: Path):
    """保存为 jsonl 格式（每行一个json对象）"""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  已保存 {len(data)} 条 → {path.name}")


def load_jsonl(path: Path) -> list:
    """加载 jsonl"""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  已保存 → {path.name}")


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@contextmanager
def timer(name: str):
    """简易计时器：with timer('阶段名'): ..."""
    print(f"[{name}] 开始...")
    t0 = time.time()
    yield
    elapsed = time.time() - t0
    print(f"[{name}] 完成，耗时 {elapsed:.2f}s")