import os
import asyncio
import threading
import streamlit as st
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import wrap_embedding_func_with_attrs

st.set_page_config(page_title="三高智能问答与图谱分析平台", page_icon="🏥", layout="wide")

# ==========================================
# 1. 核心修复：创建一个全局持久化的后台事件循环
# ==========================================
@st.cache_resource
def get_persistent_loop():
    """创建一个独立的后台线程来专门运行 asyncio 事件循环，防止被 Streamlit 刷新机制杀掉"""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    return loop

persistent_loop = get_persistent_loop()

def run_async(coro):
    """安全地将异步任务扔给后台线程执行，并等待结果"""
    future = asyncio.run_coroutine_threadsafe(coro, persistent_loop)
    return future.result()

# ==========================================
# 2. 配置大模型信息
# ==========================================
API_KEY = os.getenv("SIP_API_KEY", "")  # 请通过环境变量配置 API Key
BASE_URL = "https://api.siliconflow.cn/v1" 
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
EMBED_MODEL = "BAAI/bge-m3"
WORKING_DIR = "D:\\SIP\\rag_storage"

async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    return await openai_complete_if_cache(
        model=LLM_MODEL, prompt=prompt, system_prompt=system_prompt,
        history_messages=history_messages, api_key=API_KEY, base_url=BASE_URL, **kwargs
    )

@wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192, model_name="BAAI/bge-m3")
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed.func(texts, model=EMBED_MODEL, api_key=API_KEY, base_url=BASE_URL)

# ==========================================
# 3. 核心引擎初始化 (使用单例缓存)
# ==========================================
@st.cache_resource(show_spinner="正在唤醒三高知识大脑...")
def init_rag_engine():
    if not os.path.exists(WORKING_DIR):
        os.mkdir(WORKING_DIR)
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
        addon_params={"language": "Simplified Chinese"},
        llm_model_max_async=2,
        embedding_func_max_async=2,
        embedding_batch_num=10
    )
    # 初始化必须在持久化循环中运行
    run_async(rag.initialize_storages())
    return rag

rag = init_rag_engine()

# ==========================================
# 4. 前端侧边栏：知识库录入模块
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100)
    st.title("🏥 知识库管理")
    st.markdown("在这里上传相关的医学文献、临床指南。系统将自动提取实体并构建**知识图谱**。")
    
    uploaded_file = st.file_uploader("上传医疗知识库 (.txt)", type=["txt"])
    
    if st.button("开始解析并录入知识库", type="primary"):
        if uploaded_file is not None:
            text_content = uploaded_file.getvalue().decode("utf-8")
            with st.status("🧠 正在处理知识库，构建知识图谱...", expanded=True) as status:
                st.write("✅ 读取文件成功！")
                st.write("🔍 正在调用大模型切分文本并提取医学实体...")
                st.write("🕸️ 正在提取实体关系并构建 Graph...")
                try:
                    # 安全地执行插入
                    run_async(rag.ainsert(text_content))
                    status.update(label="✅ 知识图谱构建完成！", state="complete", expanded=False)
                    st.success("文献已成功融合到系统大脑中！")
                except Exception as e:
                    status.update(label="❌ 录入失败", state="error", expanded=False)
                    st.error(f"处理失败: {e}")
        else:
            st.error("请先上传文件！")
            
    st.divider()
    st.caption("系统内核：向量检索+知识图谱 (混合检索)\n\n数据存储：混合向量图数据库")

# ==========================================
# 5. 主界面：智能问答聊天模块
# ==========================================
st.title("👨‍⚕️ 三高知识问答平台")
st.markdown("基于 **知识图谱 (Knowledge Graph)** 与 **向量检索 (Vector RAG)** 双重引擎的专业医疗问答系统。")

# 初始化聊天历史记录
if "messages" not in st.session_state:
    st.session_state.messages =[
        {"role": "assistant", "content": "您好！我是三高智能健康顾问。我已经学习了相关的医学知识图谱，请问有什么关于高血压、高血糖或高血脂的问题我可以帮您？"}
    ]

# 显示历史聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理用户输入
if prompt := st.chat_input("例如：高血压患者的饮食禁忌有哪些？"):
    # 1. 立即在界面显示用户的提问
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 系统思考过程展示
    with st.chat_message("assistant"):
        with st.status("系统正在混合检索图谱和向量...", expanded=True) as query_status:
            st.write("🔍 正在意图识别...")
            st.write("🕸️ 正在知识图谱中游走寻找相关实体节点...")
            st.write("📐 正在进行语义向量匹配计算...")
            st.write("✍️ 正在融合知识，生成专业医生回复...")
            
            user_prompt_template = "你是一位专业的三高医学专家，请根据检索到的知识库温和、有条理地回答。并在结尾加上：'（注：本系统意见由大模型生成，仅供参考，不作为最终医疗诊断。）'"
            
            try:
                # 安全地执行问答
                response = run_async(rag.aquery(
                    prompt, 
                    param=QueryParam(mode="hybrid", user_prompt=user_prompt_template)
                ))
                query_status.update(label="✅ 检索与生成完毕", state="complete", expanded=False)
                
                # 渲染最终回答
                st.markdown(response)
                # 保存到聊天记录
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                query_status.update(label="❌ 检索处理发生错误", state="error", expanded=False)
                st.error(f"系统错误详情: {str(e)}")
