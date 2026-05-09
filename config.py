"""项目集中配置：模型、API、路径、检索参数等。

凡是可能调整的常量都集中在这里，方便后续切换模型或者迁移目录。
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKING_DIR = os.path.join(BASE_DIR, "rag_storage")
EVAL_DIR = os.path.join(BASE_DIR, "eval")
EVAL_RESULT_DIR = os.path.join(EVAL_DIR, "results")

for _d in (DATA_DIR, WORKING_DIR, EVAL_DIR, EVAL_RESULT_DIR):
    os.makedirs(_d, exist_ok=True)

# ===================== 大模型配置 =====================
API_KEY = os.getenv("SIP_API_KEY", "")
BASE_URL = os.getenv("SIP_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_MODEL = os.getenv("SIP_LLM_MODEL", "Qwen/Qwen2.5-32B-Instruct")
EMBED_MODEL = os.getenv("SIP_EMBED_MODEL", "BAAI/bge-m3")
EMBED_DIM = 1024
EMBED_MAX_TOKEN = 8192

# ===================== 重排序（Reranker）配置 =====================
ENABLE_RERANK = os.getenv("SIP_ENABLE_RERANK", "").lower() in ("1", "true", "yes")
RERANK_MODEL = os.getenv("SIP_RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

# ===================== LightRAG 检索参数 =====================
DEFAULT_QUERY_MODE = "mix" if ENABLE_RERANK else "hybrid"
DEFAULT_TOP_K = 30                    # 实体/关系 召回数量
DEFAULT_CHUNK_TOP_K = 8               # 文本块召回数量
LANGUAGE = "Simplified Chinese"
LLM_MAX_ASYNC = 2
EMBED_MAX_ASYNC = 2
EMBED_BATCH = 10

# ===================== 业务标签 =====================
DOMAIN_NAME = "三高（高血压 / 高血糖 / 高血脂）医疗知识"
DISCLAIMER = "（注：本回答由 AI 系统基于限定文献自动生成，仅供参考，不能替代专业医生的诊断与处方。）"
