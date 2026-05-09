"""
step5_bm25.py
BM25 关键词检索基线，作为对比方案。

为什么加这一步？
  - 课件第18-20页讲了"基于关键词的检索"，作业要求中提到了"选择一条技术路线"，
    加上 BM25 基线对比能有"传统方法 vs 语义检索 vs 重排"的横向对比。
  - 中文需要先用 jieba 分词再喂给 BM25。

设计：
  - 用 rank_bm25 库实现 BM25Okapi
  - 与向量检索使用相同的 query/corpus 集合，输出相同格式的 Top-K 结果
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import jieba
from tqdm import tqdm
from rank_bm25 import BM25Okapi

import config
from utils import load_jsonl, save_json, timer


def tokenize(text: str) -> list:
    """中文分词（jieba精确模式）"""
    return [w for w in jieba.lcut(text) if w.strip()]


def main():
    print("\n>>> Step 5: BM25 关键词检索基线 <<<\n")

    corpus  = load_jsonl(config.F_CORPUS_JSONL)
    queries = load_jsonl(config.F_QUERIES_JSONL)
    print(f"corpus: {len(corpus)}, queries: {len(queries)}")

    # 分词
    with timer("corpus 分词"):
        tokenized_corpus = [tokenize(c["text"]) for c in tqdm(corpus, desc="分词")]

    # 构建 BM25 索引
    with timer("构建 BM25 索引"):
        bm25 = BM25Okapi(tokenized_corpus)

    # 检索
    corpus_id_list = [c["id"] for c in corpus]
    bm25_results = {}

    with timer(f"BM25 Top-{config.TOP_K_RETRIEVE} 检索"):
        for q in tqdm(queries, desc="BM25检索"):
            q_tokens = tokenize(q["text"])
            scores = bm25.get_scores(q_tokens)
            # 取 Top-K
            top_k_idx = scores.argsort()[::-1][:config.TOP_K_RETRIEVE]
            retrieved = []
            for rank, idx in enumerate(top_k_idx, start=1):
                retrieved.append({
                    "corpus_id": corpus_id_list[idx],
                    "score":     float(scores[idx]),
                    "rank":      rank,
                })
            bm25_results[q["id"]] = retrieved

    save_json(bm25_results, config.F_BM25_RESULT)

    # 样例展示
    corpus_dict = {c["id"]: c["text"] for c in corpus}
    sample_qid = queries[0]["id"]
    print(f"\n=== 样例：query_id={sample_qid} 的 BM25 Top5 ===")
    print(f"Query: {queries[0]['text']}\n")
    for r in bm25_results[sample_qid][:5]:
        print(f"  [rank {r['rank']}] score={r['score']:.4f}")
        print(f"    {corpus_dict[r['corpus_id']][:60]}...")


if __name__ == "__main__":
    main()