# CmedqaRetrieval 检索系统作业

基于 sentence_transformers + faiss + rerankers 的中文医疗问答检索流水线。

## 项目亮点

1. **三种方案横向对比**：BM25 关键词检索 vs Dense 向量召回 vs Dense+Rerank 精排
2. **多维度评估指标**：Recall@K、MRR@K、NDCG@K（K=1, 5, 10）
3. **Bad case 分析**：自动找出"重排修正成功"的典型案例
4. **工程权衡分析**：IndexFlatIP vs IndexIVFFlat 速度对比

## 项目结构

```
.
├── data/                    HuggingFace数据集缓存
├── outputs/                 中间产物（向量、索引、检索结果）
├── results/                 评估结果（PPT素材）
├── src/
│   ├── config.py           全局配置
│   ├── utils.py            工具函数
│   ├── step0_load_data.py  数据加载
│   ├── step1_encode.py     向量化
│   ├── step2_build_index.py 索引构建
│   ├── step3_retrieve.py   向量检索
│   ├── step4_rerank.py     重排
│   ├── step5_bm25.py       BM25基线
│   └── step6_evaluate.py   综合评估
├── run_all.py              一键运行
└── requirements.txt
```

## 使用方法

```powershell
# 1. 激活环境并安装依赖
conda activate xxx
pip install -r requirements.txt

# 2. 创建data、outputs文件夹
因为文件大小限制，这里没有将data、outputs文件夹一并上传，所以需要使用人自己创建。以供下载数据集和储存结果。

# 3. 一键跑完整流程
python run_all.py

# 或者分步跑（可单独调试）
python src/step0_load_data.py
python src/step1_encode.py
python src/step2_build_index.py
python src/step3_retrieve.py
python src/step4_rerank.py
python src/step5_bm25.py
python src/step6_evaluate.py
```

## 配置说明

修改 `src/config.py`：

- `USE_FULL_DATA = True/False` 切换全量/采样模式
- `EMBEDDING_MODEL` 切换向量模型
- `RERANKER_MODEL` 切换重排模型
- `TOP_K_RETRIEVE / TOP_K_RERANK` 调整召回/重排数量

## 输出结果（用于PPT）

跑完后 `results/` 目录会有：

- `metrics_summary.json`     三种方案的所有指标
- `metrics_table.csv`        指标对比表
- `metrics_comparison.png`   柱状对比图
- `bad_case_analysis.md`     重排成功案例分析
