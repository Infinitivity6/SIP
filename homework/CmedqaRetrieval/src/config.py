"""
config.py — 项目全局配置
所有路径、模型、超参数集中在这里管理。
"""

import os
from pathlib import Path

# ── 项目路径 ─────────────────────────────────────────────
ROOT_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR     = ROOT_DIR / "data"
OUTPUT_DIR   = ROOT_DIR / "outputs"
RESULTS_DIR  = ROOT_DIR / "results"

for d in (DATA_DIR, OUTPUT_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── HuggingFace 镜像（解决国内访问问题）──────────────────
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ── 数据集 ───────────────────────────────────────────────
DATASET_REPO       = "C-MTEB/CmedqaRetrieval"
QRELS_REPO         = "C-MTEB/CmedqaRetrieval-qrels"

# 数据采样配置（4080显卡完全够跑全量；如想快速测试可减小）
USE_FULL_DATA      = True              # True=全量 / False=快速测试模式
N_CORPUS_SAMPLE    = 10000             # 仅在 USE_FULL_DATA=False 时生效
N_QUERIES_SAMPLE   = 200               # 同上

# ── 模型配置 ─────────────────────────────────────────────
EMBEDDING_MODEL    = "BAAI/bge-small-zh-v1.5"   # 中文向量模型，512维，速度快
RERANKER_MODEL     = "BAAI/bge-reranker-base"   # 中文cross-encoder重排模型
DEVICE             = "cuda"                      # 4080可用，无GPU时改为"cpu"

# ── 检索参数 ─────────────────────────────────────────────
TOP_K_RETRIEVE     = 50      # 粗排召回 Top-K
TOP_K_RERANK       = 10      # 精排输出 Top-K
BATCH_SIZE_ENCODE  = 256     # 编码batch size（4080建议256，显存不足改小）

# ── 评估指标 K 值 ────────────────────────────────────────
EVAL_K_LIST        = [1, 5, 10]

# ── 中间产物文件名 ───────────────────────────────────────
F_CORPUS_JSONL       = OUTPUT_DIR / "corpus.jsonl"
F_QUERIES_JSONL      = OUTPUT_DIR / "queries.jsonl"
F_QRELS_JSONL        = OUTPUT_DIR / "qrels.jsonl"

F_CORPUS_EMB         = OUTPUT_DIR / "corpus_embeddings.npy"
F_QUERY_EMB          = OUTPUT_DIR / "query_embeddings.npy"
F_FAISS_INDEX        = OUTPUT_DIR / "faiss.index"

F_RETRIEVE_RESULT    = OUTPUT_DIR / "retrieve_top50.json"
F_RERANK_RESULT      = OUTPUT_DIR / "rerank_top10.json"
F_BM25_RESULT        = OUTPUT_DIR / "bm25_top50.json"

F_FINAL_METRICS      = RESULTS_DIR / "metrics_summary.json"
F_BAD_CASE_REPORT    = RESULTS_DIR / "bad_case_analysis.md"


def print_config():
    print("=" * 60)
    print("项目配置")
    print("=" * 60)
    print(f"  数据模式      : {'全量数据' if USE_FULL_DATA else '采样模式'}")
    print(f"  Embedding模型 : {EMBEDDING_MODEL}")
    print(f"  Reranker模型  : {RERANKER_MODEL}")
    print(f"  设备          : {DEVICE}")
    print(f"  Top-K(召回)   : {TOP_K_RETRIEVE}")
    print(f"  Top-K(重排)   : {TOP_K_RERANK}")
    print(f"  数据目录      : {DATA_DIR}")
    print(f"  输出目录      : {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()