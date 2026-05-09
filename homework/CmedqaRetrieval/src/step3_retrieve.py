"""
step3_retrieve.py
用 faiss 索引对所有 query 做 Top-K 检索。

输出 JSON 格式：
{
  "query_id_1": [
    {"corpus_id": "xxx", "score": 0.91, "rank": 1},
    {"corpus_id": "yyy", "score": 0.88, "rank": 2},
    ...
  ],
  ...
}
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import faiss

import config
from utils import load_jsonl, save_json, timer


def main():
    print("\n>>> Step 3: 向量检索 <<<\n")

    # 加载数据和索引
    corpus  = load_jsonl(config.F_CORPUS_JSONL)
    queries = load_jsonl(config.F_QUERIES_JSONL)
    query_emb = np.load(config.F_QUERY_EMB)
    index = faiss.read_index(str(config.F_FAISS_INDEX))

    corpus_id_list = [c["id"] for c in corpus]    # 下标 → corpus_id 映射

    print(f"queries: {len(queries)}, corpus索引: {index.ntotal}")

    # 批量检索
    with timer(f"Top-{config.TOP_K_RETRIEVE} 向量检索"):
        D, I = index.search(query_emb, config.TOP_K_RETRIEVE)
    # D: 相似度分数矩阵 (n_query, K)
    # I: corpus下标矩阵 (n_query, K)

    # 整理结果
    results = {}
    for q_idx, q in enumerate(queries):
        qid = q["id"]
        retrieved = []
        for rank, (corpus_idx, score) in enumerate(zip(I[q_idx], D[q_idx]), start=1):
            if corpus_idx < 0:    # faiss 用 -1 表示无效
                continue
            retrieved.append({
                "corpus_id": corpus_id_list[corpus_idx],
                "score":     float(score),
                "rank":      rank,
            })
        results[qid] = retrieved

    save_json(results, config.F_RETRIEVE_RESULT)

    # 展示一个样例（用于 PPT）
    sample_qid = queries[0]["id"]
    print(f"\n=== 样例：query_id={sample_qid} 的Top5召回结果 ===")
    print(f"Query: {queries[0]['text']}\n")
    corpus_dict = {c["id"]: c["text"] for c in corpus}
    for r in results[sample_qid][:5]:
        text = corpus_dict[r["corpus_id"]]
        print(f"  [rank {r['rank']}] score={r['score']:.4f}")
        print(f"    {text[:80]}...")


if __name__ == "__main__":
    main()