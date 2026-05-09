# SIP v1 版本说明

## 版本定位

v1 是“三高知识智能问答平台”的初始可运行版本，面向高血压、高血糖、高血脂领域，完成从医学文献录入、LightRAG 图增强检索、意图识别、Prompt 生成、问答展示到系统评测的完整闭环。

## 核心功能

- 基于 Streamlit 提供 Web 应用入口，包含智能问答、知识图谱、知识录入、系统评测四个标签页。
- 集成本地随附的 HKUDS/LightRAG 源码，通过 GraphRAG 同时利用文本片段、实体和关系进行检索增强生成。
- 支持硅基流动 OpenAI 兼容接口，默认模型配置为 Qwen/Qwen2.5-32B-Instruct 与 BAAI/bge-m3 embedding。
- 提供 8 类医疗问答意图识别：概念解释、饮食建议、用药咨询、运动指导、监测指标、并发症风险、生活作息、综合咨询。
- 针对不同意图自动选择检索模式、召回数量和专用 Prompt，提升回答结构和领域适配性。
- 支持文献上传、data 目录批量录入和爬虫骨架触发，形成“采集 -> 清洗 -> 切片 -> 向量化 -> 图谱抽取”的流程。
- 支持 pyvis 知识图谱可视化，展示实体数量、关系数量和图密度。
- 支持自动化评测，基于 26 道测试题统计生成准确率、检索召回率、关键词覆盖率和平均延迟，并导出 JSON/CSV 报告。
- 聊天页支持多轮上下文、检索来源展示、文档片段、命中实体和命中关系展开查看。

## 项目结构

- `main.py`：Streamlit 主入口。
- `config.py`：API、模型、路径、检索参数集中配置。
- `src/rag_engine.py`：LightRAG 引擎封装、异步事件循环、查询和来源解析。
- `src/intent_classifier.py`：规则优先、LLM 兜底的意图识别。
- `src/prompt_templates.py`：按意图分发的 Prompt 与检索策略。
- `src/data_loader.py`：文本读取、清洗、去重和入库。
- `src/crawler.py`：医疗资料爬虫流水线骨架。
- `src/evaluator.py`：批量评测与报告生成。
- `src/ui/`：四个功能标签页和公共 UI 组件。
- `data/`：三高领域知识文本。
- `eval/`：测试题集与评测结果。
- `RAG/`：随项目提交的 LightRAG 上游源码。

## 当前数据与评测状态

- `data/` 目录包含 8 个三高专题文本文件，覆盖疾病概述、药物、饮食、运动生活方式等方向。
- 当前本地 `rag_storage/` 属于运行时索引目录，已在 `.gitignore` 中排除；首次部署后可通过“一键录入 data 目录”重新构建知识库索引。
- 已有评测报告显示 26 道题平均准确率约 0.84、平均召回率约 0.805、平均覆盖率约 0.706，后续可通过扩充数据和启用 reranker 继续提升。

## 运行方式

```powershell
conda activate SIP
pip install -r requirements.txt
copy .env.example .env
# 在 .env 中配置 SIP_API_KEY
streamlit run main.py
```

## 安全与配置

- v1 已移除源码中的硬编码 API Key，运行时请通过 `.env` 或环境变量 `SIP_API_KEY` 配置。
- `.env`、`rag_storage/`、`lightrag.log` 和 Python 缓存文件不会进入版本控制。

## 后续迭代方向

- 接入真实医疗信息源爬虫，替换当前本地样本回放逻辑。
- 启用并评估 BAAI/bge-reranker-v2-m3 重排序能力。
- 扩充知识库文献和评测集，增加人工评测维度。
- 增强移动端 UI 适配和部署脚本，例如 Dockerfile。
