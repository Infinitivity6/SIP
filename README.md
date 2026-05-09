# 三高知识智能问答平台（SIP）

> 期末项目 · 基于 **GraphRAG（LightRAG）** 的特定领域问答系统
>
> 领域：高血压 / 高血糖 / 高血脂（"三高"）医疗知识

本项目是课程"特定领域知识问答系统"的完整实现：从数据采集（爬虫骨架）→
清洗与切片 → 向量化 + 知识图谱构建 → 意图理解 → 检索召回 → 提示工程 →
答案生成 → 系统评测，全链路打通，并通过 Streamlit 提供产品化的可视化界面。

---

## 一、项目结构

```
D:\SIP\
├── main.py                       # 全功能 Streamlit 主入口
├── config.py                     # 集中配置（API Key / 模型 / 路径 / 检索 / Reranker）
├── requirements.txt              # 第三方依赖
├── .env.example                  # 环境变量模板（可复制为 .env 覆盖默认值）
├── README.md                     # 本说明文档
│
├── src/                          # 核心后端模块（解耦、可单测）
│   ├── rag_engine.py             #  LightRAG 引擎封装 + 持久化事件循环 + 来源解析
│   ├── intent_classifier.py      #  意图理解（规则 + LLM 兜底双引擎）
│   ├── prompt_templates.py       #  提示工程（按意图分发 8 套差异化 Prompt）
│   ├── data_loader.py            #  数据清洗 / 去重 / 批量入库
│   ├── crawler.py                #  爬虫流水线骨架（fetch → clean → save）
│   └── evaluator.py              #  系统评测（准确率 / 召回率 / 覆盖率 / 延迟）
│
├── data/                         # 医学知识文献（8 个专题 txt）
│   ├── 3high_data.txt            # 三高概述
│   ├── Medicine.txt              # 降压药简明手册
│   ├── hypertension_guide.txt    # 高血压综合防治指南
│   ├── diabetes_guide.txt        # 糖尿病与高血糖综合防治指南
│   ├── hyperlipidemia_guide.txt  # 高血脂综合防治指南
│   ├── medicine_guide.txt        # 三高常用药物综合手册
│   ├── diet_nutrition.txt        # 三高饮食营养指导方案
│   └── exercise_lifestyle.txt    # 运动与健康生活方式指导
│
├── eval/                         # 评测资源
│   ├── test_questions.json       # 测试题集（26 道，覆盖全部 8 个意图类别）
│   └── results/                  # 自动生成的评测报告（JSON）
│
├── rag_storage/                  # LightRAG 自动维护的存储目录
│   ├── graph_chunk_entity_relation.graphml   # 知识图谱
│   ├── vdb_*.json                              # 向量索引
│   └── kv_store_*.json                         # KV 缓存
│
├── RAG/                          # 上游开源底座 LightRAG（HKUDS/LightRAG）
└── archive/                      # 历史迭代版本归档
    ├── app.py / app1.py / app2.py
    └── prompt.txt
```

---

## 二、对应课程要求的实现

| 课程要求 | 在本项目中的实现 |
| --- | --- |
| **数据抓取** | `src/crawler.py` 提供完整的爬虫骨架（`fetch → clean → save` 三步）。当前阶段用 `data/` 目录下的样本文件做"回放"，后续替换 `MedicalCrawler.fetch` 即可接入真实数据源。 |
| **数据清洗** | `src/data_loader.clean_text` 负责零宽字符过滤 / 多余空行收敛 / 行尾空格清理；`deduplicate` 用 md5 去重。 |
| **文本切片** | 由 LightRAG 内部按 chunk 自动完成，参数化配置在 `config.py`。 |
| **向量化存储** | `BAAI/bge-m3`（1024 维）作为 embedding，索引落到 `rag_storage/vdb_*.json`。 |
| **意图理解** | `src/intent_classifier.py`：规则关键词优先匹配 8 种意图（definition / diet / medicine / exercise / monitor / complication / lifestyle / general），匹配失败时回退 LLM 二次分类，并识别问题中的疾病实体。规则命中率约 90%，LLM 兜底确保全覆盖。 |
| **相关片段检索 + 排序** | 直接复用 LightRAG 的多模式检索（`hybrid` / `mix` / `local` / `global` / `naive`），并按意图自动选择最合适的模式，可在 UI 上手动切换以做对比。 |
| **Prompt 工程** | `src/prompt_templates.py` 为每个意图维护独立 prompt（含分点结构、引用要求、统一免责声明）。 |
| **结果整合输出** | UI 端打字机流式呈现，支持引用标注 `[1][2]` 与最末免责声明。 |
| **系统评价** | `src/evaluator.py` + `eval/test_questions.json`：自动批跑 24 道题（覆盖全部 8 个意图类别），给出准确率、召回率、覆盖率、平均延迟；支持柱状图可视化 + 颜色标注热力图 + JSON/CSV 双格式导出。 |

---

## 三、快速启动

### 1. 安装依赖

```powershell
pip install -r requirements.txt
# 国内网络可加镜像：
#   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 📦 **关于 LightRAG 底座**：项目里已经把 [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG)
> 的源码完整放在 `RAG/` 目录中，`src/rag_engine.py` 启动时会自动把它注入到 `sys.path`，
> 因此 **无需** `pip install lightrag-hku` 也能直接 `import lightrag` 跑通。
> 如果希望走标准安装方式，也可以 `pip install -e ./RAG`。

> ⚠️ 默认配置使用 [硅基流动](https://siliconflow.cn) 的 OpenAI 兼容接口
> （`Qwen/Qwen2.5-7B-Instruct` + `BAAI/bge-m3`）。可通过环境变量
> `SIP_API_KEY` / `SIP_BASE_URL` / `SIP_LLM_MODEL` / `SIP_EMBED_MODEL` 覆盖。

### 2. 启动 Web 应用

```powershell
streamlit run main.py
```

打开 [http://localhost:8501](http://localhost:8501) 即可看到四个标签页：

| 标签页 | 用途 |
| --- | --- |
| 💬 **智能问答** | 流式打字机输出 / 可视化意图识别 / 一键切换检索模式 / 多轮对话上下文 |
| 🕸️ **知识图谱** | 实时渲染 LightRAG 抽取的实体-关系网络（pyvis 交互） |
| 📚 **知识录入** | 单文件上传 · 一键录入 data 目录 · 触发爬虫骨架 |
| 📊 **系统评测** | 一键跑测试集，实时进度 + 类别统计 + 报告下载 |

### 3. 命令行评测（无需 UI）

```powershell
python -c "from src.evaluator import evaluate, load_test_set, save_report; r,s = evaluate(load_test_set()); print(s); save_report(r, s)"
```

---

## 四、关键技术点

### 4.1 持久化事件循环

LightRAG 全异步 + Streamlit 频繁 rerun 的组合很容易触发"loop already closed"。
我们在 `src/rag_engine.py` 中开了一个守护线程跑常驻 `asyncio` 事件循环，
所有 `ainsert / aquery` 都通过 `run_coroutine_threadsafe` 投递过去，避免被 UI 刷掉。

### 4.2 意图理解 → 检索策略

```
用户问题 ──► IntentClassifier.classify ──► PromptStrategy(mode, top_k, user_prompt)
              │
              └── 提取疾病实体（高血压/高血糖/高血脂）作为辅助信号
```

不同意图选择不同 `mode` 与 `top_k`：
- 概念解释类问题 → `hybrid`（综合 KG + 向量）
- 用药咨询类问题 → `hybrid` + 较高 `top_k`（药物名容易分散）
- 并发症类问题 → `global`（侧重宏观知识）

### 4.3 提示工程

每个意图都有专属 `user_prompt`，在共同基础约束（必须基于检索内容、引用标注、免责声明）之上，叠加角色化指令（"内科医师/营养师/药师/康复师"）和结构化输出要求。

### 4.4 评测体系

| 维度 | 计算方式 |
| --- | --- |
| 检索召回率 | `must_have ∪ nice_to_have` 关键词在 **检索上下文** 中的出现比例 |
| 生成准确率 | `must_have` 关键词在 **最终回答** 中的出现比例 |
| 关键词覆盖率 | `must_have ∪ nice_to_have` 在最终回答中的出现比例 |
| 平均延迟 | 单题 `aquery` 耗时取均值 |

测试集分 6 个类别（definition / diet / medicine / complication / lifestyle 等），方便分类查看强弱项。

---

## 五、相比初版（app.py）的增量

| 维度 | app.py | 本项目 |
| --- | --- | --- |
| 代码组织 | 单文件 ~250 行 | 模块化（config + src + eval + main，职责清晰） |
| 意图理解 | ❌ 无 | ✅ 8 类意图 + 规则 / LLM 双引擎 |
| 提示工程 | 单一固定模板 | ✅ 按意图分发 8 套差异化 Prompt |
| 检索控制 | 固定 hybrid | ✅ 意图驱动 + UI 手动切换 5 种模式 |
| 数据接入 | 仅支持上传单文件 | ✅ 单文件 / 批量目录 / 爬虫骨架三种入口 |
| 系统评测 | ❌ 无 | ✅ 准确率/召回/覆盖/延迟 + 可视化图表 + JSON/CSV 导出 |
| 多轮对话上下文 | ❌ 无 | ✅ 最近 6 条历史进上下文 |
| 图谱面板 | 仅渲染 | ✅ 节点/边/密度三项指标 + 侧边栏统计 |
| 知识库数据 | 2 篇短文 | ✅ 8 篇专业文献，合计约 2 万中文字符 |
| 测试题集 | 无 | 26 道覆盖全部 8 类意图 + must_have/nice_to_have |
| Reranker 重排序 | ❌ 无 | ✅ 可选启用，通过环境变量配置 |
| 首次启动 | 需手动录入 | ✅ 自动检测空库并索引 data 目录 |
| LLM 意图兜底 | ❌ 未接线 | ✅ 规则失败自动回退 LLM 二次分类 |

---

## 六、后续可扩展方向

1. **真实爬虫**：替换 `MedicalCrawler.fetch` 为 `requests + BeautifulSoup`（39 健康网 / 丁香医生 / 国家卫健委公开指南）。
2. **RAGAS 评估集成**：LightRAG 已内置 RAGAS 支持，可加入 `faithfulness / answer_relevancy / context_precision` 三项更专业的指标。
3. **持久化对话**：把会话记录落到 SQLite，支持历史会话回看 / 导出。
5. **角色权限**：医生 / 患者 / 健康管理师不同身份对应不同 Prompt 风格。

---

## 七、致谢

- 底座：[HKUDS / LightRAG](https://github.com/HKUDS/LightRAG)
- 模型推理：[硅基流动 SiliconFlow](https://siliconflow.cn)
- 前端：[Streamlit](https://streamlit.io) + [pyvis](https://pyvis.readthedocs.io)
