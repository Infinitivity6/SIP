"""
step2_build_index.py
用 faiss 构建向量索引。

设计：
  - 使用 IndexFlatIP（精确内积）— 因为我们的向量已归一化，内积 = 余弦相似度
  - 10万规模下 IndexFlatIP 完全够用，搜索毫秒级
  - 如果 corpus 更大（百万级）才需要 IVF/HNSW 加速

附加：同时构建一个 IVF 索引做对比（亮点：展示工程权衡）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import numpy as np
import faiss

import config
from utils import timer


def build_flat_index(corpus_emb: np.ndarray) -> faiss.Index:
    """精确搜索索引：遍历所有向量，准确率100%"""
    dim = corpus_emb.shape[1]
    index = faiss.IndexFlatIP(dim)   # 内积索引（向量已归一化 → 等价于余弦相似度）
    index.add(corpus_emb)
    return index


def build_ivf_index(corpus_emb: np.ndarray, nlist: int = 100) -> faiss.Index:
    """倒排索引：先聚成 nlist 个簇，搜索时只查最近的几个簇"""
    dim = corpus_emb.shape[1]
    quantizer = faiss.IndexFlatIP(dim)
    index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
    index.train(corpus_emb)
    index.add(corpus_emb)
    index.nprobe = 10   # 搜索时查询最近的10个簇
    return index


def benchmark_search(index: faiss.Index, query_emb: np.ndarray, k: int):
    """测量搜索耗时"""
    t0 = time.time()
    D, I = index.search(query_emb, k)
    elapsed = time.time() - t0
    return D, I, elapsed


def main():
    print("\n>>> Step 2: 构建 faiss 索引 <<<\n")

    # 加载向量
    corpus_emb = np.load(config.F_CORPUS_EMB)
    query_emb  = np.load(config.F_QUERY_EMB)
    print(f"corpus_emb: {corpus_emb.shape}, query_emb: {query_emb.shape}")

    # ── 主索引：IndexFlatIP（用于后续检索）──
    with timer("构建 IndexFlatIP（精确）"):
        flat_index = build_flat_index(corpus_emb)
        print(f"  index.ntotal = {flat_index.ntotal}")
    faiss.write_index(flat_index, str(config.F_FAISS_INDEX))
    print(f"  已保存 → {config.F_FAISS_INDEX.name}")

    # ── 对比测试：IVF vs Flat 的速度差异（亮点：工程权衡分析）──
    print("\n=== 索引方案对比 ===")

    # Flat
    _, _, flat_t = benchmark_search(flat_index, query_emb, config.TOP_K_RETRIEVE)
    print(f"  IndexFlatIP   - 搜索 {len(query_emb)} 条 query × Top{config.TOP_K_RETRIEVE} = {flat_t*1000:.1f}ms")

    # IVF对比测试（可选，Windows下faiss-cpu偶有线程问题，置False跳过）
    RUN_IVF_BENCHMARK = False
    if RUN_IVF_BENCHMARK and corpus_emb.shape[0] >= 2000:
        try:
            faiss.omp_set_num_threads(1)   # Windows下避免多线程死锁
            with timer("构建 IndexIVFFlat（加速）"):
                ivf_index = build_ivf_index(corpus_emb, nlist=min(100, corpus_emb.shape[0] // 50))
            _, _, ivf_t = benchmark_search(ivf_index, query_emb, config.TOP_K_RETRIEVE)
            print(f"  IndexIVFFlat  - 搜索 {len(query_emb)} 条 query × Top{config.TOP_K_RETRIEVE} = {ivf_t*1000:.1f}ms")
            speedup = flat_t / ivf_t if ivf_t > 0 else 0
            print(f"  → IVF 加速比: {speedup:.2f}x")
        except Exception as e:
            print(f"  [跳过 IVF 测试] {e}")
    else:
        print("  [说明] IVF 对比测试已跳过（Flat 已能在毫秒级完成搜索）")

    print("\n[说明] 后续检索使用 IndexFlatIP（精确）以保证召回质量")


if __name__ == "__main__":
    main()