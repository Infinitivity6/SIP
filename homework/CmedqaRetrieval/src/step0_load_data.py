"""
step0_load_data.py
从 HuggingFace 镜像加载 CmedqaRetrieval 数据集，对齐 corpus + queries + qrels，
并按需采样后保存为本地 jsonl 文件，供后续步骤使用。

关键逻辑：
  - 全量模式：使用所有 100,001 corpus + 全部 qrels 涉及的 queries
  - 采样模式：只取 N_QUERIES_SAMPLE 条 queries，并保证它们的相关 corpus
              都在采样的 corpus 子集里（避免评估失效）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import random
from datasets import load_dataset

import config
from utils import save_jsonl, timer


def load_raw():
    """从HuggingFace加载三个数据集"""
    with timer("加载 corpus"):
        corpus_ds = load_dataset(config.DATASET_REPO, "default",
                                 split="corpus",
                                 cache_dir=str(config.DATA_DIR))
    with timer("加载 queries"):
        queries_ds = load_dataset(config.DATASET_REPO, "default",
                                  split="queries",
                                  cache_dir=str(config.DATA_DIR))
    with timer("加载 qrels"):
        # qrels 在另一个仓库；通常有 dev split
        qrels_ds_all = load_dataset(config.QRELS_REPO,
                                    cache_dir=str(config.DATA_DIR))
        # 取 dev split（C-MTEB 默认评估split）
        split_name = "dev" if "dev" in qrels_ds_all else list(qrels_ds_all.keys())[0]
        qrels_ds = qrels_ds_all[split_name]
        print(f"  使用 qrels split: '{split_name}'")

    print(f"\n原始数据规模：")
    print(f"  corpus  : {len(corpus_ds):>8} 条")
    print(f"  queries : {len(queries_ds):>8} 条")
    print(f"  qrels   : {len(qrels_ds):>8} 条")

    return corpus_ds, queries_ds, qrels_ds


def filter_and_sample(corpus_ds, queries_ds, qrels_ds):
    """
    对齐三个数据集 + 按配置采样。
    必须保证：
      1. queries 里的每个 query 在 qrels 中都有标注（否则无法评估）
      2. qrels 引用的 corpus-id 都在最终的 corpus 子集里
    """
    # ── 步骤1：先把 qrels 转成字典 query_id -> [{corpus_id, score}] ──
    # 自适应字段名：不同版本数据集可能用 query-id / qid / query_id 等
    fields = qrels_ds.column_names
    print(f"  qrels 字段名: {fields}")
    qid_field = next((f for f in fields if f.replace("-", "_").lower() in ("query_id", "qid")), None)
    cid_field = next((f for f in fields if f.replace("-", "_").lower() in ("corpus_id", "cid", "doc_id", "pid", "docid")), None)
    score_field = next((f for f in fields if f.lower() in ("score", "label", "relevance")), None)
    if not (qid_field and cid_field and score_field):
        raise ValueError(f"无法识别 qrels 字段，请检查列名: {fields}")
    print(f"  使用字段: query={qid_field}, corpus={cid_field}, score={score_field}")

    qrels_dict = {}
    for row in qrels_ds:
        qid = str(row[qid_field])
        cid = str(row[cid_field])
        score = int(row[score_field])
        if score < 1:    # 只保留正相关
            continue
        qrels_dict.setdefault(qid, []).append({"corpus_id": cid, "score": score})

    print(f"\n有效 qrels 覆盖 {len(qrels_dict)} 个 query")

    # ── 步骤2：仅保留在 qrels 中有标注的 queries ──
    queries_filtered = [
        {"id": str(row["id"]), "text": row["text"]}
        for row in queries_ds
        if str(row["id"]) in qrels_dict
    ]
    print(f"过滤后 queries: {len(queries_filtered)} 条")

    # ── 步骤3：决定 queries 采样规模 ──
    if config.USE_FULL_DATA:
        queries_final = queries_filtered
    else:
        random.seed(42)
        n = min(config.N_QUERIES_SAMPLE, len(queries_filtered))
        queries_final = random.sample(queries_filtered, n)
    print(f"最终 queries: {len(queries_final)} 条")

    # ── 步骤4：收集这些 queries 对应的"必须保留"的 corpus_id ──
    must_keep_cids = set()
    qrels_final = []
    final_qids = {q["id"] for q in queries_final}
    for qid in final_qids:
        for rel in qrels_dict[qid]:
            must_keep_cids.add(rel["corpus_id"])
            qrels_final.append({
                "query_id":  qid,
                "corpus_id": rel["corpus_id"],
                "score":     rel["score"],
            })
    print(f"qrels 引用的相关 corpus_id 数量: {len(must_keep_cids)}")

    # ── 步骤5：corpus采样 ──
    corpus_all = [
        {"id": str(row["id"]), "text": row["text"]}
        for row in corpus_ds
    ]

    if config.USE_FULL_DATA:
        corpus_final = corpus_all
    else:
        # 必须保留的相关corpus + 随机采样的干扰项
        corpus_id_to_text = {c["id"]: c["text"] for c in corpus_all}
        kept = [{"id": cid, "text": corpus_id_to_text[cid]}
                for cid in must_keep_cids if cid in corpus_id_to_text]
        # 补充随机干扰项到目标规模
        random.seed(42)
        all_ids = list(corpus_id_to_text.keys())
        random.shuffle(all_ids)
        target = config.N_CORPUS_SAMPLE
        existing_ids = must_keep_cids
        for cid in all_ids:
            if len(kept) >= target:
                break
            if cid not in existing_ids:
                kept.append({"id": cid, "text": corpus_id_to_text[cid]})
        corpus_final = kept
    print(f"最终 corpus: {len(corpus_final)} 条")

    return corpus_final, queries_final, qrels_final


def main():
    config.print_config()

    print("\n>>> Step 0: 加载并对齐数据集 <<<\n")

    # 已存在则跳过
    if (config.F_CORPUS_JSONL.exists()
        and config.F_QUERIES_JSONL.exists()
        and config.F_QRELS_JSONL.exists()):
        print("[跳过] 数据文件已存在。如需重新生成请删除 outputs/*.jsonl")
        return

    corpus_ds, queries_ds, qrels_ds = load_raw()
    corpus, queries, qrels = filter_and_sample(corpus_ds, queries_ds, qrels_ds)

    save_jsonl(corpus,  config.F_CORPUS_JSONL)
    save_jsonl(queries, config.F_QUERIES_JSONL)
    save_jsonl(qrels,   config.F_QRELS_JSONL)

    # 打印样例
    print("\n=== 样例 ===")
    print(f"corpus[0] : {corpus[0]['text'][:80]}...")
    print(f"queries[0]: {queries[0]['text']}")
    print(f"qrels[0]  : {qrels[0]}")


if __name__ == "__main__":
    main()