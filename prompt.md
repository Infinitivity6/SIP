# 三高知识智能问答平台 — 完整上下文 Prompt

## 项目概述

**名称**：三高知识智能问答平台（GraphRAG-based Domain-specific Medical QA System）

**定位**：大学期末项目。面向「高血压/高血糖/高血脂」三大慢病的特定领域医学知识问答系统，底层使用 HKUDS/LightRAG 实现图增强检索生成（GraphRAG），前端使用 Streamlit 搭建 Web UI。

**核心能力**：
1. 数据采集：爬虫骨架（占位）→ 清洗 → 文本切片 → 向量化 → 知识图谱实体/关系抽取
2. 智能问答：意图识别（规则+LLM兜底）→ GraphRAG 多模式检索 → Prompt工程 → 打字机流式输出 → 参考文献展示
3. 知识图谱：pyvis 交互式实体-关系可视化（可拖拽/缩放）
4. 系统评测：召回率/准确率/覆盖率/延迟 + 报告导出

**目录结构**：
```
D:\SIP\
├── main.py                    # Streamlit 主入口
├── config.py                  # 集中配置（API/模型/路径/参数）
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── prompt.md                  # 本文件
├── data/                      # 医学文献源数据（.txt）
│   ├── 3high_data.txt
│   ├── Medicine.txt
│   ├── hypertension_guide.txt
│   ├── diabetes_guide.txt
│   ├── hyperlipidemia_guide.txt
│   ├── medicine_guide.txt
│   ├── diet_nutrition.txt
│   └── exercise_lifestyle.txt
├── rag_storage/               # LightRAG 持久化存储（KV + 图 + 向量）
├── eval/
│   ├── test_questions.json    # 26道测试题（8类意图）
│   └── results/               # 评测报告输出
├── RAG/                       # LightRAG 源码（本地捆绑，不依赖 pip）
│   └── lightrag/              # HKUDS/LightRAG 核心库
├── src/
│   ├── __init__.py
│   ├── rag_engine.py          # LightRAG 引擎封装（核心）
│   ├── data_loader.py         # 数据加载与清洗
│   ├── intent_classifier.py   # 意图识别（规则+LLM）
│   ├── prompt_templates.py    # 8种意图的Prompt策略
│   ├── evaluator.py           # 自动化评测
│   ├── crawler.py             # 爬虫占位骨架
│   └── ui/
│       ├── __init__.py
│       ├── components.py      # 公用组件（打字机/图谱/类型推断）
│       ├── sidebar.py         # 侧边栏（机器人+系统信息+KB列表+图谱统计）
│       ├── chat_tab.py        # 智能问答标签页
│       ├── graph_tab.py       # 知识图谱可视化标签页
│       ├── ingest_tab.py      # 知识录入标签页
│       └── eval_tab.py        # 系统评测标签页
└── homework/                  # 与项目无关，忽略
└── archive/
    └── prompt.txt             # 原始课程需求描述
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| Web 框架 | Streamlit >= 1.32 | 全栈 Python Web UI |
| 知识底座 | LightRAG (HKUDS) | 本地捆绑在 `RAG/`，从源码加载 |
| 图存储 | NetworkX + GraphML | 知识图谱持久化格式 |
| 图可视化 | pyvis | 交互式图谱渲染（Barnes-Hut 力导向） |
| LLM | Qwen2.5-32B-Instruct | 通过硅基流动 API（OpenAI 兼容）调用 |
| Embedding | BAAI/bge-m3 (1024d) | 同上 API |
| Reranker | BAAI/bge-reranker-v2-m3 | 可选启用 |
| 评测 | 关键词匹配 | recall@k / accuracy / coverage |

## 核心架构数据流

```
用户提问 → intent_classifier.classify() → 规则/LLM 意图分类
         → prompt_templates.for_intent() → 检索策略（mode/top_k/user_prompt）
         → rag_engine.query_with_sources() → ① retrieve_context() 拿上下文
                                              ② parse_context_sources() 解析实体/关系/片段/参考文献
                                              ③ query() 调用 LLM 生成回答
         → sanitize_response() → 净化输出（去引用标签/降级标题/折叠空行）
         → render_typewriter() → 打字机效果展示
         → _render_sources() → 渲染参考文献卡片
```

## 关键文件详解

### 1. `config.py` — 配置中心

```python
API_KEY = os.getenv("SIP_API_KEY", "")  # 硅基流动 API Key，通过 .env 配置
BASE_URL = "https://api.siliconflow.cn/v1"
LLM_MODEL = "Qwen/Qwen2.5-32B-Instruct"
EMBED_MODEL = "BAAI/bge-m3"
EMBED_DIM = 1024
ENABLE_RERANK = False  # 默认关闭，通过环境变量 SIP_ENABLE_RERANK=1 开启
DEFAULT_QUERY_MODE = "mix" if ENABLE_RERANK else "hybrid"
DEFAULT_TOP_K = 30
DEFAULT_CHUNK_TOP_K = 8
```

### 2. `src/rag_engine.py` — LightRAG 封装（最核心模块）

**关键设计决策**：
- 使用**持久化后台 asyncio 事件循环**（`get_persistent_loop()`），避免 Streamlit 每次 rerun 杀掉异步任务
- 引擎通过 `@st.cache_resource` 单例化，首次启动耗时较长（加载向量/图索引）
- LightRAG 从 `RAG/lightrag/` 本地源码加载（`sys.path.insert`），不依赖 pip 包
- `sanitize_response()` 净化 LLM 输出：删 UTF-8 替换字符、删除模型编造的 References 段、将 markdown 标题降级为粗体、移除 citation 残留（`[1][2]` `[11 References]` 等）、折叠多余空行

**检索模式说明**（LightRAG QueryParam.mode）：
| mode | 说明 |
|------|------|
| `hybrid` | 图谱+向量混合检索（默认） |
| `mix` | KG 集成检索（推荐搭配 Reranker） |
| `local` | 局部实体检索（精准查询） |
| `global` | 全局摘要检索（宏观问题） |
| `naive` | 纯向量检索（无图谱） |

**context 输出格式**（LightRAG 的 `only_need_context=True` 返回）：
```
Knowledge Graph Data (Entity):
```json
{"id": "...", "entity": "...", "type": "...", "description": "..."}
```

Knowledge Graph Data (Relationship):
```json
{"src_id": "...", "tgt_id": "...", "src": "...", "tgt": "...", "description": "..."}
```

Document Chunks (...):
```json
{"reference_id": 1, "content": "..."}
```

Reference Document List (...):
```
[1] Medicine.txt
[2] 3high_data.txt
```
```

`parse_context_sources()` 解析上述格式，返回结构化 dict。

### 3. `src/intent_classifier.py` — 意图识别

8 种意图标签：`definition` / `diet` / `medicine` / `exercise` / `monitor` / `complication` / `lifestyle` / `general`

**策略**：先规则关键词匹配（速度快、覆盖常见问法），命中不到时回退 LLM 分类。

**平局决胜优先级**（多意图命中数相同时）：complication > medicine=diet > exercise=lifestyle > monitor > definition > general

### 4. `src/prompt_templates.py` — 提示工程

每种意图维护独立的 `PromptStrategy`（user_prompt + mode + top_k + chunk_top_k）：
- definition: hybrid, top_k=25
- diet: hybrid, top_k=30
- medicine: hybrid, top_k=35（用药问题需更广检索）
- complication: **global**（并发症需要全局视角）
- 其余: hybrid, top_k=20-30

所有策略共享 `_BASE_RULES`：
1. 严格基于知识库回答，不编造
2. 简体中文，专业克制，先结论再分点
3. 不输出 markdown 标题，不拼 References 段落
4. 不输出 citation 标签
5. 末尾输出免责声明

### 5. `src/data_loader.py` — 数据录入

- `iter_text_files()`: 遍历 data/ 下所有 .txt，支持 UTF-8/GBK 编码
- `clean_text()`: 去零宽字符、去行尾空格、收敛多余空行
- `deduplicate()`: 按内容 MD5 去重
- `ingest_folder()`: 一键录入 data 目录全部文件
- `ingest_raw_text()`: 单文件上传录入

### 6. `src/evaluator.py` — 评测系统

- `load_test_set()`: 加载 `eval/test_questions.json`（26 题 8 类）
- `evaluate_case()`: 单题评测（意图→检索→生成→关键词命中率）
- `evaluate()`: 批量评测，支持进度回调
- `save_report()`: 输出 JSON 报告

评测指标：
- **context_recall**: 检索上下文中 must_have+nice_to_have 关键词命中率
- **answer_accuracy**: 回答中 must_have 关键词覆盖率
- **key_coverage**: 回答中 全部关键词覆盖率
- **elapsed_sec**: 响应时间

### 7. `src/crawler.py` — 爬虫占位

当前为骨架：`MedicalCrawler.fetch()` 从本地 data 目录取样本文件回放。后续接入真实数据源只需重写 `fetch()`。

### 8. UI 模块

#### `main.py`
- `st.set_page_config` 宽屏模式 + 展开侧边栏
- `@st.cache_resource` 缓存引擎初始化
- `render_sidebar()` → 4 个标签页

#### `src/ui/sidebar.py`
包含两大块：

**A. 动态机器人吉祥物** (`_ROBOT_HTML` 模块级常量)
- 纯 SVG + CSS + JS，通过 `st.components.v1.html` 嵌入
- SVG viewBox="-14 -12 148 182"，显式 width="110" height="138"，iframe height=148
- 动画特征：
  - 身体浮动：`<animateTransform type="translate">` 4s 周期
  - 身体摇摆：`<animateTransform type="rotate">` 绕 pivot (60,90) 6s 周期
  - 手臂挥动：左右臂各绕肩关节 pivot 旋转 4.2s 周期
  - 眨眼：嵌套 `<g transform="translate(eyeX,eyeY)">` + 内层 `<animateTransform type="scale">` 7s 不规则眨眼（5次，含双眨眼）
  - 天线脉冲：`<circle>` r 和 opacity 动画 1.6s
  - 地面阴影：ellipse rx 和 opacity 随浮动同步变化
- 交互：
  - 鼠标悬停：CSS `#rb-wrap:hover svg { transform: scale(1.10); }` 0.35s 弹性过渡
  - 点击弹跳：CSS `@keyframes pop` 0.55s + JS 临时放大 `maxOff=4.5` 400ms
  - 红十字符号心跳：CSS `@keyframes heartBeat` 2.2s 无限循环于 `.hb-cross`
- 眼球追踪：
  - JS `mousemove` 监听 → 计算鼠标相对 SVG 位置 → 限制 `maxOff=3.0` 偏移范围
  - `requestAnimationFrame` lerp 平滑追踪（鼠标活跃时 speed=0.11，空闲时 0.07）
  - 空闲漂移：Lissajous 曲线 (`sin(angle*1.7)*1.5`, `cos(angle*1.3)*1.2`)
  - 随机环顾：每 4-8 秒生成随机目标点，`glanceWeight` 指数衰减（0.995/帧）
  - 2.2 秒无鼠标移动后进入空闲模式

**B. 侧边栏信息**
- 系统信息卡片（领域/LLM/Embedding/框架/Reranker）
- 知识库文献列表（从 `kv_store_full_docs.json` 读取，显示文件名+字数）
- 图谱统计（节点数/边数）

#### `src/ui/chat_tab.py`
**CSS 布局策略**（关键）：
```css
/* 使 block-container 充满视口 + flex 列布局 */
section[data-testid="stMain"] .block-container {
  display: flex !important;
  flex-direction: column !important;
  min-height: calc(100vh - 3.6rem) !important;
}
/* 聊天输入框容器推至底部并固定 */
section[data-testid="stMain"] .block-container > div:has(.stChatInput) {
  margin-top: auto !important;
  position: sticky !important;
  bottom: 0 !important;
  background: #0e1117 !important;
}
```

**首次居中逻辑**：
- 使用 `session_state.chat_started` 标志
- 初始为 False → 渲染 14vh 空白占位，视觉上让输入框居中
- 首次提交后设为 True + `st.rerun()` → 不再渲染占位 → 输入框被 CSS 推至底部

**参考文献渲染** (`_render_sources()`):
- 从 `sources` dict 中提取 references/chunks/entities/relations
- references: 编号文件列表，标注引用次数
- chunks: expander 内展示前 5 个片段，`clean_chunk_preview()` 去换行/反引号/截断半句
- entities: 展示前 6 个实体，`infer_entity_type()` 推断 UNKNOWN 类型
- relations: 展示前 6 条关系 (src→tgt)
- 消息历史回放时也会渲染 sources（修复了之前 `st.rerun()` 后参考文献消失的 bug）

**检索流程**：
1. `classify(user_input)` → 意图
2. `extract_diseases(user_input)` → 命中疾病列表
3. `for_intent(intent.label)` → 检索策略
4. `query_with_sources()` → 一次调用同时获取 answer + sources
5. `render_typewriter()` → 打字机输出
6. `_render_sources()` → 参考文献卡片
7. 追加到 `session_state.messages`，设置 `chat_started=True`，`st.rerun()`

#### `src/ui/components.py`
- `render_typewriter()`: 累积式 markdown 打字机，4字符/chunk，0.02s 延迟
- `render_knowledge_graph()`: pyvis 渲染，Barnes-Hut 力导向，暗色背景
- `clean_desc()`: 去 `<SEP>` 分隔符
- `infer_entity_type()`: 关键词兜底推断 UNKNOWN 实体类型
- `build_ref_map()`: {ref_id: file_path} 映射
- `clean_chunk_preview()`: 片段预览清洗（去换行/反引号/句首半句话）

#### `src/ui/ingest_tab.py`
- 左栏：文件上传 + 解析录入
- 右栏：一键批量录入 data 目录 / 触发爬虫骨架

#### `src/ui/eval_tab.py`
- 测试集概览（26题 8类 分布柱状图）
- 一键跑全量评测（带实时进度+表格刷新）
- 4 维指标卡片（准确率/召回率/覆盖率/延迟）
- 各类别表现表格+柱状图
- 单题详情（带颜色标注的 dataframe）
- JSON/CSV 双格式导出

#### `src/ui/graph_tab.py`
- 图谱可视化页，支持刷新和高度选择

## 对话迭代历史

本次对话对项目做了以下修改（按时间顺序）：

### 1. 创建动态机器人吉祥物
**文件**: `src/ui/sidebar.py`
- 新增 `_ROBOT_HTML` 模块级常量（约 290 行纯 SVG+CSS+JS）
- 机器人特征：身体/手臂/头/眼/天线/书本+红十字
- 初始动画：浮动、摇摆、眨眼、手臂挥动
- 初始眼球追踪：mousemove → JS 直接跟随

### 2. 修复眨眼动画 Bug
**问题**: 眨眼时眼球向下移动到身体位置（非常诡异）
**原因**: CSS `scaleY` 在 SVG `<g>` 上的 `transform-origin` 默认是 SVG 原点 (0,0)，不是眼球中心
**解决**: 改用嵌套 SVG `<g transform="translate(eyeX,eyeY)">` + 内层 `<animateTransform type="scale">`，缩放原点即眼中心

### 3. 修复机器人裁剪问题
**问题**: 机器人上下被 iframe 边缘裁切，天线和阴影不可见
**解决**: 逐步扩大 viewBox 从 "-5 -5 130 170" → "-14 -12 148 182"，同时设置显式 SVG width="110" height="138" + iframe height=148

### 4. 增强机器人交互趣味性
- 不规则眨眼（7s 周期 5 次，含双眨眼，模拟自然行为）
- 随机环顾（JS 每 4-8s 生成随机目标，`glanceWeight` 指数衰减混合）
- 鼠标悬停放大（CSS scale 1.10 + 弹性过渡）
- 点击弹跳（CSS keyframes + JS 眼睛短暂放大 `maxOff=4.5`）
- 红十字符号心跳（CSS keyframes 2.2s 循环）

### 5. 修复聊天框底部固定
**问题**: 用户希望首次加载时输入框居中，首次对话后固定在浏览器视口最底部（像 ChatGPT/Claude）
**涉及**: CSS flexbox `:has(.stChatInput)` + `margin-top: auto` + `position: sticky`
**踩坑**: `st.chat_input` 由 Streamlit 渲染在页面内容最下方，CSS 需要通过 `:has()` 伪类定位其父容器

### 6. 修复参考文献/卡片消失
**问题**: `st.rerun()` 后历史消息只渲染了 `msg["content"]`，没有渲染 `msg["sources"]`
**解决**: 提取 `_render_sources()` 为模块级函数，在历史消息循环中检查 `msg.get("sources")` 并调用

### 7. 替换弃用参数
**问题**: Streamlit 警告 `use_container_width` 将于 2025-12-31 后移除
**解决**: 全局替换 19 处 `use_container_width=True` → `width="stretch"`，`use_container_width=False` → `width="content"`

## 已知注意事项

1. **API Key 配置**: `config.py` 已移除硬编码 API Key，实际部署应通过 `.env` 或环境变量 `SIP_API_KEY` 配置
2. **LightRAG 本地捆绑**: 引擎从 `RAG/lightrag/` 源码加载，不依赖 pip；如需升级 LightRAG，替换 `RAG/` 目录即可
3. **Streamlit rerun 模型**: `st.rerun()` 会保留 `session_state` 但重置 widget 返回值，所有 widget 交互必须通过 `session_state` 持久化
4. **异步事件循环**: `rag_engine.py` 使用后台线程运行 `asyncio` 事件循环，streamlit 的 `@st.cache_resource` 确保引擎全局唯一
5. **CSS 选择器脆弱性**: `:has(.stChatInput)` 依赖 Streamlit 内部 DOM 结构，如果 Streamlit 升级改变 class 名需对应调整
6. **SVG 内嵌 JS 通信**: 机器人眼球追踪通过 iframe 内 JS 独立运行，无法与 Streamlit 后端通信
7. **数据文件编码**: `data_loader.py` 支持 UTF-8 和 GBK 两种编码，新增数据文件建议使用 UTF-8
8. **评测依赖 LLM**: 每次跑全量评测需要调用 26 次 LLM，耗时较长（每次 2-5 秒）
9. **GraphML 文件**: 图谱数据存储在 `rag_storage/graph_chunk_entity_relation.graphml`，由 LightRAG 在录入时自动生成

## 启动方式

```bash
cd D:\SIP
pip install -r requirements.txt
# 配置 .env（复制 .env.example 并填入 API Key）
streamlit run main.py
```

## 后续可迭代方向

1. **爬虫完善**: 重写 `crawler.py` 的 `fetch()` 方法接入真实数据源（39健康网、丁香医生等）
2. **Reranker 启用**: 设置 `SIP_ENABLE_RERANK=1` 可显著提升检索精度
3. **更多数据**: 向 `data/` 目录添加更多医学指南/文献 .txt 文件
4. **意图分类优化**: 当前规则关键词覆盖有限，可扩充词典或改用更小更快的分类模型
5. **评测增强**: 接入 ROUGE/BLEU 等自动指标，或增加人工评分维度
6. **多轮对话**: 当前 `conversation_history` 已传入但取最近 6 条，可优化上下文窗口策略
7. **机器人动效**: 可增加更多 SVG 动画或表情变化
8. **移动端适配**: 当前 CSS 针对桌面浏览器，移动端可能需要调整
9. **Docker 部署**: 编写 Dockerfile 方便答辩演示环境一致性
10. **Logging 完善**: 当前主要依赖 streamlit 的 st.status/st.error，可补充文件日志

---

*此文件由 Claude Code 在 2026-05-07 对话中生成，用于交接给其他模型继续版本迭代。*

这个项目运行方法：

conda activate SIP

streamlit run main.py
