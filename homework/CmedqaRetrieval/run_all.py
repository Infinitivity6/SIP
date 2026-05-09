"""
run_all.py — 一键串起整个 pipeline

按顺序执行：
  Step 0: 加载数据
  Step 1: 文本向量化
  Step 2: 构建 faiss 索引
  Step 3: 向量检索
  Step 4: Cross-Encoder 重排
  Step 5: BM25 基线（独立分支）
  Step 6: 综合评估
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import config


def banner(text: str):
    print("\n" + "█" * 70)
    print(f"  {text}")
    print("█" * 70)


def main():
    config.print_config()

    total_start = time.time()

    banner("STEP 0  加载并对齐数据集")
    from step0_load_data import main as step0
    step0()

    banner("STEP 1  文本向量化")
    from step1_encode import main as step1
    step1()

    banner("STEP 2  构建 faiss 索引")
    from step2_build_index import main as step2
    step2()

    banner("STEP 3  向量检索（粗排）")
    from step3_retrieve import main as step3
    step3()

    banner("STEP 4  Cross-Encoder 重排")
    from step4_rerank import main as step4
    step4()

    banner("STEP 5  BM25 关键词检索基线")
    from step5_bm25 import main as step5
    step5()

    banner("STEP 6  综合评估与可视化")
    from step6_evaluate import main as step6
    step6()

    total = time.time() - total_start
    banner(f"全部完成！总耗时 {total/60:.1f} 分钟")
    print(f"\n关键产物在: {config.RESULTS_DIR}")
    print("  - metrics_summary.json   评估指标")
    print("  - metrics_table.csv      指标对比表（PPT用）")
    print("  - metrics_comparison.png 柱状对比图（PPT用）")
    print("  - bad_case_analysis.md   重排成功案例分析")


if __name__ == "__main__":
    main()