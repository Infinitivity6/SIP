"""
step6_evaluate.py
综合评估：BM25 vs 向量检索 vs 向量检索+重排

计算指标：
  - Recall@K：前K个结果中是否包含至少一个相关文档
  - MRR@K   ：第一个相关文档排名的倒数（衡量"正确答案排得多靠前"）
  - NDCG@K  ：折损累计增益（综合考虑相关性和排名位置）

输出：
  - results/metrics_summary.json
  - results/bad_case_analysis.md（重排修正了排名的典型例子）
  - results/metrics_comparison.png（柱状图，PPT素材）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
from utils import load_jsonl, load_json, save_json


# ────────────────────────────────────────────────────────
# 指标计算
# ────────────────────────────────────────────────────────

def recall_at_k(retrieved_ids: list, relevant_ids: set, k: int) -> float:
    """前K个结果中相关文档的占比（分母=相关文档总数）"""
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant_ids) / len(relevant_ids)


def mrr_at_k(retrieved_ids: list, relevant_ids: set, k: int) -> float:
    """第一个相关文档的排名倒数"""
    for rank, cid in enumerate(retrieved_ids[:k], start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list, relevant_ids: set, k: int) -> float:
    """折损累计增益（DCG / IDCG）"""
    dcg = 0.0
    for rank, cid in enumerate(retrieved_ids[:k], start=1):
        if cid in relevant_ids:
            dcg += 1.0 / math.log2(rank + 1)

    n_rel = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, n_rel + 1))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate(results: dict, qrels_dict: dict, k_list: list) -> dict:
    """
    对一种方法的检索结果计算所有 K 值的指标。
    results: {query_id: [{corpus_id, score, rank}, ...]}
    qrels_dict: {query_id: set(相关corpus_id)}
    """
    metrics = {f"Recall@{k}": [] for k in k_list}
    metrics.update({f"MRR@{k}":    [] for k in k_list})
    metrics.update({f"NDCG@{k}":   [] for k in k_list})

    for qid, retrieved in results.items():
        if qid not in qrels_dict:
            continue
        relevant_ids = qrels_dict[qid]
        retrieved_ids = [r["corpus_id"] for r in retrieved]

        for k in k_list:
            metrics[f"Recall@{k}"].append(recall_at_k(retrieved_ids, relevant_ids, k))
            metrics[f"MRR@{k}"].append(mrr_at_k(retrieved_ids, relevant_ids, k))
            metrics[f"NDCG@{k}"].append(ndcg_at_k(retrieved_ids, relevant_ids, k))

    # 求平均
    return {name: float(np.mean(vals)) for name, vals in metrics.items() if vals}


# ────────────────────────────────────────────────────────
# Bad case 分析（亮点：找出重排修正过来的例子）
# ────────────────────────────────────────────────────────

def find_rerank_wins(retrieve_results, rerank_results, qrels_dict,
                     corpus_dict, queries_dict, top_n=5) -> list:
    """
    找重排"修正成功"的典型例子：
    向量召回时正确答案排名靠后，重排后排名提前。
    """
    cases = []
    for qid, rel_ids in qrels_dict.items():
        if qid not in retrieve_results or qid not in rerank_results:
            continue

        retrieved_ids = [r["corpus_id"] for r in retrieve_results[qid]]
        reranked_ids  = [r["corpus_id"] for r in rerank_results[qid]]

        # 找正确答案在两个列表中的最佳排名
        retrieve_best = next((i+1 for i, c in enumerate(retrieved_ids) if c in rel_ids), 999)
        rerank_best   = next((i+1 for i, c in enumerate(reranked_ids)  if c in rel_ids), 999)

        improvement = retrieve_best - rerank_best
        if improvement >= 3 and rerank_best <= 3:    # 重排把答案推进Top3，且至少提升3名
            cases.append({
                "qid": qid,
                "query": queries_dict[qid],
                "retrieve_best_rank": retrieve_best,
                "rerank_best_rank":   rerank_best,
                "improvement":        improvement,
                "relevant_ids":       list(rel_ids),
                "retrieve_top3":      retrieved_ids[:3],
                "rerank_top3":        reranked_ids[:3],
            })

    cases.sort(key=lambda x: -x["improvement"])
    return cases[:top_n]


def write_bad_case_md(cases: list, corpus_dict: dict, path: Path):
    """生成可读的 bad case 分析报告"""
    lines = ["# 重排成功修正的典型案例\n",
             "以下案例展示了 cross-encoder 重排相比纯向量召回的优势：",
             "正确答案在向量召回中排名靠后，但重排后被推到 Top3。\n"]

    for i, c in enumerate(cases, 1):
        lines.append(f"## 案例 {i}\n")
        lines.append(f"**Query**: {c['query']}\n")
        lines.append(f"- 向量召回中相关答案最佳排名: **{c['retrieve_best_rank']}**")
        lines.append(f"- 重排后相关答案最佳排名: **{c['rerank_best_rank']}**")
        lines.append(f"- 排名提升: **+{c['improvement']}** 位\n")

        lines.append("**向量召回 Top3:**")
        for j, cid in enumerate(c["retrieve_top3"], 1):
            mark = "✅" if cid in c["relevant_ids"] else "❌"
            lines.append(f"  {j}. {mark} {corpus_dict[cid][:80]}...")
        lines.append("")

        lines.append("**重排后 Top3:**")
        for j, cid in enumerate(c["rerank_top3"], 1):
            mark = "✅" if cid in c["relevant_ids"] else "❌"
            lines.append(f"  {j}. {mark} {corpus_dict[cid][:80]}...")
        lines.append("\n---\n")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  已保存 → {path.name}")


# ────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────

def plot_comparison(metrics_dict: dict, k_list: list, save_path: Path):
    """画三种方案的指标对比柱状图"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 中文字体兼容
    plt.rcParams['axes.unicode_minus'] = False

    methods = list(metrics_dict.keys())
    metric_names = ["Recall", "MRR", "NDCG"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    colors = ["#888780", "#1D9E75", "#D85A30"]    # 灰、绿、珊瑚

    for idx, mname in enumerate(metric_names):
        ax = axes[idx]
        x = np.arange(len(k_list))
        width = 0.25
        for i, method in enumerate(methods):
            vals = [metrics_dict[method].get(f"{mname}@{k}", 0) for k in k_list]
            ax.bar(x + i*width, vals, width, label=method, color=colors[i % 3])
        ax.set_xticks(x + width)
        ax.set_xticklabels([f"@{k}" for k in k_list])
        ax.set_ylabel(mname)
        ax.set_title(f"{mname}@K 对比")
        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"  已保存图表 → {save_path.name}")


# ────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────

def main():
    print("\n>>> Step 6: 综合评估 <<<\n")

    # 加载数据
    corpus  = load_jsonl(config.F_CORPUS_JSONL)
    queries = load_jsonl(config.F_QUERIES_JSONL)
    qrels   = load_jsonl(config.F_QRELS_JSONL)

    corpus_dict  = {c["id"]: c["text"] for c in corpus}
    queries_dict = {q["id"]: q["text"] for q in queries}

    # 整理 qrels: query_id → set(corpus_id)
    qrels_dict = {}
    for r in qrels:
        qrels_dict.setdefault(r["query_id"], set()).add(r["corpus_id"])
    print(f"qrels 覆盖 {len(qrels_dict)} 个 query")

    # 加载三种方法的结果
    bm25_res     = load_json(config.F_BM25_RESULT)     if config.F_BM25_RESULT.exists()     else None
    retrieve_res = load_json(config.F_RETRIEVE_RESULT)
    rerank_res   = load_json(config.F_RERANK_RESULT)

    # 评估
    print("\n=== 评估结果 ===")
    results = {}

    if bm25_res is not None:
        m_bm25 = evaluate(bm25_res, qrels_dict, config.EVAL_K_LIST)
        results["BM25(关键词)"] = m_bm25
        print("\n[BM25 关键词检索]")
        for k, v in m_bm25.items():
            print(f"  {k}: {v:.4f}")

    m_dense = evaluate(retrieve_res, qrels_dict, config.EVAL_K_LIST)
    results["Dense(向量召回)"] = m_dense
    print("\n[向量召回]")
    for k, v in m_dense.items():
        print(f"  {k}: {v:.4f}")

    m_rerank = evaluate(rerank_res, qrels_dict, config.EVAL_K_LIST)
    results["Dense+Rerank"] = m_rerank
    print("\n[向量召回 + Cross-Encoder 重排]")
    for k, v in m_rerank.items():
        print(f"  {k}: {v:.4f}")

    # 保存指标
    save_json(results, config.F_FINAL_METRICS)

    # ── Bad case 分析 ──
    print("\n=== Bad Case 分析 ===")
    cases = find_rerank_wins(retrieve_res, rerank_res, qrels_dict,
                              corpus_dict, queries_dict, top_n=5)
    print(f"找到 {len(cases)} 个重排修正成功的案例")
    write_bad_case_md(cases, corpus_dict, config.F_BAD_CASE_REPORT)

    # ── 可视化 ──
    print("\n=== 生成对比图表 ===")
    plot_comparison(results, config.EVAL_K_LIST,
                    config.RESULTS_DIR / "metrics_comparison.png")

    # ── 汇总表（PPT 用）──
    df = pd.DataFrame(results).T
    df = df[[f"Recall@{k}" for k in config.EVAL_K_LIST]
            + [f"MRR@{k}"   for k in config.EVAL_K_LIST]
            + [f"NDCG@{k}"  for k in config.EVAL_K_LIST]]
    df.to_csv(config.RESULTS_DIR / "metrics_table.csv", encoding="utf-8-sig")
    print(f"  已保存表格 → metrics_table.csv")
    print("\n" + df.round(4).to_string())


if __name__ == "__main__":
    main()