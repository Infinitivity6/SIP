"""
step1_encode.py
用 sentence_transformers 把 corpus 和 queries 编码为向量。

设计要点：
  - 使用 BAAI/bge-small-zh-v1.5 中文向量模型（512维）
  - normalize_embeddings=True，使内积 = 余弦相似度
  - GPU batch encode，4080 上 10 万 corpus 约 1~2 分钟
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from sentence_transformers import SentenceTransformer

import config
from utils import load_jsonl, timer


def main():
    print("\n>>> Step 1: 文本向量化 <<<\n")

    # 加载数据
    corpus  = load_jsonl(config.F_CORPUS_JSONL)
    queries = load_jsonl(config.F_QUERIES_JSONL)
    print(f"加载 corpus: {len(corpus)} 条, queries: {len(queries)} 条")

    corpus_texts  = [c["text"] for c in corpus]
    query_texts   = [q["text"] for q in queries]

    # 加载模型
    with timer("加载 Embedding 模型"):
        model = SentenceTransformer(config.EMBEDDING_MODEL, device=config.DEVICE)
        print(f"  模型: {config.EMBEDDING_MODEL}")
        print(f"  向量维度: {model.get_sentence_embedding_dimension()}")
        print(f"  设备: {model.device}")

    # 编码 corpus
    if config.F_CORPUS_EMB.exists():
        print(f"[跳过] {config.F_CORPUS_EMB.name} 已存在")
        corpus_emb = np.load(config.F_CORPUS_EMB)
    else:
        with timer(f"编码 corpus（{len(corpus_texts)} 条）"):
            corpus_emb = model.encode(
                corpus_texts,
                batch_size=config.BATCH_SIZE_ENCODE,
                show_progress_bar=True,
                normalize_embeddings=True,    # 关键：归一化使内积=余弦相似度
                convert_to_numpy=True,
            ).astype(np.float32)
        np.save(config.F_CORPUS_EMB, corpus_emb)
        print(f"  corpus_emb shape = {corpus_emb.shape}")

    # 编码 queries
    if config.F_QUERY_EMB.exists():
        print(f"[跳过] {config.F_QUERY_EMB.name} 已存在")
        query_emb = np.load(config.F_QUERY_EMB)
    else:
        with timer(f"编码 queries（{len(query_texts)} 条）"):
            query_emb = model.encode(
                query_texts,
                batch_size=config.BATCH_SIZE_ENCODE,
                show_progress_bar=True,
                normalize_embeddings=True,
                convert_to_numpy=True,
            ).astype(np.float32)
        np.save(config.F_QUERY_EMB, query_emb)
        print(f"  query_emb shape = {query_emb.shape}")

    # 显示一个样例向量（前8维），用于PPT展示
    print("\n=== 样例向量（query[0] 的前8维）===")
    print(f"原文: {query_texts[0][:50]}...")
    print(f"向量: {query_emb[0][:8]}")
    print(f"L2范数（应约等于1.0）: {np.linalg.norm(query_emb[0]):.4f}")


if __name__ == "__main__":
    main()


