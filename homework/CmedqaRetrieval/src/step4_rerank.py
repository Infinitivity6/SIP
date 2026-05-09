"""
step4_rerank.py
用 cross-encoder 对粗排 Top-K 做精排。

设计：
  - 加载 BAAI/bge-reranker-base（中文cross-encoder）
  - 对每个 query，从粗排结果中取 Top-K，让 reranker 重新打分
  - 输出最终 Top-N（精排）

注意：cross-encoder 速度慢，对每条 (query, doc) 都要单独跑一次模型。
     全量数据 + Top50 重排 在 4080 上大约 5~10 分钟。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tqdm import tqdm
from rerankers import Reranker

import config
from utils import load_jsonl, load_json, save_json, timer


def main():
    print("\n>>> Step 4: 候选重排 <<<\n")

    # 加载数据
    corpus  = load_jsonl(config.F_CORPUS_JSONL)
    queries = load_jsonl(config.F_QUERIES_JSONL)
    retrieve_results = load_json(config.F_RETRIEVE_RESULT)

    corpus_dict = {c["id"]: c["text"] for c in corpus}
    queries_dict = {q["id"]: q["text"] for q in queries}

    # 加载 reranker 模型
    with timer(f"加载 Reranker 模型: {config.RERANKER_MODEL}"):
        ranker = Reranker(
            config.RERANKER_MODEL,
            model_type="cross-encoder",
            device=config.DEVICE,
        )

    # 对每个 query 重排
    rerank_results = {}
    with timer(f"对 {len(queries)} 个 query 进行重排"):
        for q in tqdm(queries, desc="重排进度"):
            qid = q["id"]
            q_text = q["text"]

            # 从粗排结果取 Top-K
            top_k = retrieve_results.get(qid, [])[:config.TOP_K_RETRIEVE]
            if not top_k:
                rerank_results[qid] = []
                continue

            doc_ids   = [r["corpus_id"]            for r in top_k]
            doc_texts = [corpus_dict[cid]          for cid in doc_ids]

            # cross-encoder 打分
            ranked = ranker.rank(query=q_text, docs=doc_texts, doc_ids=doc_ids)

            # 整理为统一格式（取 Top-N）
            reranked = []
            for new_rank, item in enumerate(ranked.results[:config.TOP_K_RERANK], start=1):
                reranked.append({
                    "corpus_id": item.doc_id,
                    "score":     float(item.score),
                    "rank":      new_rank,
                })
            rerank_results[qid] = reranked

    save_json(rerank_results, config.F_RERANK_RESULT)

    # 展示一个样例
    sample_qid = queries[0]["id"]
    print(f"\n=== 样例：query_id={sample_qid} 的重排前后对比 ===")
    print(f"Query: {queries[0]['text']}\n")

    print("[重排前 Top5（向量召回）]")
    for r in retrieve_results[sample_qid][:5]:
        print(f"  [rank {r['rank']}] {corpus_dict[r['corpus_id']][:60]}...")

    print("\n[重排后 Top5（cross-encoder精排）]")
    for r in rerank_results[sample_qid][:5]:
        print(f"  [rank {r['rank']}] {corpus_dict[r['corpus_id']][:60]}...")


if __name__ == "__main__":
    main()