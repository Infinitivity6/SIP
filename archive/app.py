import os
import time
import asyncio
import threading
import streamlit as st
import numpy as np
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import wrap_embedding_func_with_attrs

st.set_page_config(page_title="三高智能问答与图谱分析平台", page_icon="🏥", layout="wide")

# ==========================================
# 1. 持久化后台事件循环 (防死机核心)
# ==========================================
@st.cache_resource
def get_persistent_loop():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    return loop

persistent_loop = get_persistent_loop()

def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, persistent_loop)
    return future.result()

# ==========================================
# 2. 高级打字机流式输出生成器
# ==========================================
def stream_text(text, delay=0.015):
    """模拟打字机效果，逐字输出，增加阅读高级感"""
    for char in text:
        yield char
        time.sleep(delay)

# ==========================================
# 3. 核心引擎与模型配置 (修复绝对路径)
# ==========================================
API_KEY = os.getenv("SIP_API_KEY", "")  # 请通过环境变量配置 API Key
BASE_URL = "https://api.siliconflow.cn/v1" 
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
EMBED_MODEL = "BAAI/bge-m3"

# 【核心修复】使用绝对路径，彻底解决图谱找不到的问题！
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(BASE_DIR, "rag_storage")

async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    return await openai_complete_if_cache(
        model=LLM_MODEL, prompt=prompt, system_prompt=system_prompt,
        history_messages=history_messages, api_key=API_KEY, base_url=BASE_URL, **kwargs
    )

@wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192, model_name="BAAI/bge-m3")
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed.func(texts, model=EMBED_MODEL, api_key=API_KEY, base_url=BASE_URL)

@st.cache_resource(show_spinner="正在唤醒三高知识大脑...")
def init_rag_engine():
    os.makedirs(WORKING_DIR, exist_ok=True)
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
        addon_params={"language": "Simplified Chinese"},
        llm_model_max_async=2,
        embedding_func_max_async=2,
        embedding_batch_num=10
    )
    run_async(rag.initialize_storages())
    return rag

rag = init_rag_engine()

# ==========================================
# 4. 图谱可视化功能 (全屏大图优化版)
# ==========================================
def render_knowledge_graph():
    graph_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    
    if not os.path.exists(graph_path):
        st.info("💡 暂无图谱数据。请先在左侧边栏上传医学文献，系统会自动构建知识图谱。")
        return

    try:
        G = nx.read_graphml(graph_path)
        if len(G.nodes) == 0:
            st.warning("⚠️ 知识图谱中暂无节点数据。")
            return
        
        # 创建更绚丽的 Pyvis 交互网络图
        net = Network(height='600px', width='100%', bgcolor='#0E1117', font_color='white')
        net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
        net.from_nx(G)
        
        html_path = os.path.join(WORKING_DIR, "temp_graph.html")
        net.save_graph(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_data = f.read()
        
        components.html(html_data, height=620)
    except Exception as e:
        st.error(f"图谱渲染失败，请检查数据格式: {e}")

# ==========================================
# 5. 前端侧边栏：知识库录入模块
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100)
    st.title("🏥 知识库构建")
    st.markdown("在此上传医疗知识库。系统将基于文献提取实体，自动构建**底层知识图谱**。")
    
    uploaded_file = st.file_uploader("上传医疗知识库 (.txt)", type=["txt"])
    
    if st.button("开始解析并录入知识库", type="primary", use_container_width=True):
        if uploaded_file is not None:
            text_content = uploaded_file.getvalue().decode("utf-8")
            
            # 【高级 UI】动态进度条设计
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.markdown("⏳ **[15%]** 正在读取文件并进行基础数据清洗...")
            progress_bar.progress(15)
            time.sleep(0.8)  # 增加延迟，提升视觉感知
            
            status_text.markdown("🔪 **[35%]** 正在对长文本进行语义切片处理...")
            progress_bar.progress(35)
            time.sleep(0.8)
            
            status_text.markdown("🤖 **[60%]** 核心任务：大模型正在疯狂提取医学实体与关联关系...")
            progress_bar.progress(60)
            
            try:
                # 执行耗时的核心录入处理
                run_async(rag.ainsert(text_content))
                
                status_text.markdown("💾 **[90%]** 正在将知识图谱与向量索引持久化至混合数据库...")
                progress_bar.progress(90)
                time.sleep(0.8)
                
                status_text.markdown("✨ **[100%]** 知识库融合完毕！大脑已升级！")
                progress_bar.progress(100)
                time.sleep(0.5)
                
                # 清除进度条，换成成功提示框
                progress_bar.empty()
                status_text.empty()
                st.success("✅ 文献已成功融合到系统大脑中！您可以前往图谱探索区查看。")
            except Exception as e:
                progress_bar.empty()
                status_text.error(f"处理失败，详情: {e}")
        else:
            st.error("请先上传文件！")
            
    st.divider()
    st.caption("技术栈：LightRAG (图检索增强) + Streamlit + NetworkX")

# ==========================================
# 6. 主界面：双标签页 (Tabs) 产品级架构
# ==========================================
st.title("👨‍⚕️ 三高知识智能问答平台")

# 创建双标签页
tab_chat, tab_graph = st.tabs(["💬 智能对话问答", "🕸️ 知识图谱探索"])

# ==================== Tab 1: 智能问答 ====================
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages =[
            {"role": "assistant", "content": "您好！我是三高智能健康顾问。我已经学习了底层的医学知识图谱，请问有什么关于高血压、高血糖或高血脂的问题我可以帮您？"}
        ]

    # 渲染历史记录
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 提问处理
    if prompt := st.chat_input("例如：高血压患者的饮食禁忌有哪些？"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            # 【高级 UI】问答过程进度条
            with st.status("💡 系统正在深度思考...", expanded=True) as query_status:
                q_progress_bar = st.progress(0)
                q_status_text = st.empty()
                
                q_status_text.markdown("**🔍 [20%] 正在解析患者意图与医学实体...**")
                q_progress_bar.progress(20)
                time.sleep(0.6)
                
                q_status_text.markdown("**📐 [50%] 正在向量数据库中进行高维度语义匹配检索...**")
                q_progress_bar.progress(50)
                time.sleep(0.6)
                
                q_status_text.markdown("**🕸️ [80%] 正在知识图谱中顺藤摸瓜寻找深层逻辑关联...**")
                q_progress_bar.progress(80)
                
                # 定义严格的回复限制
                user_prompt_template = """
                你是一位严谨的临床医学专家。
                请【严格且仅根据】以上检索到的知识库内容来回答用户的问题。
                要求：
                1. 回答要专业、有条理，并在使用了知识库信息的句子末尾标注来源（例如：[1]、[2]）。
                2. 如果知识库中没有提及，请坦诚回答“根据当前知识库，暂无相关信息”。
                3. 在回答的最末尾另起一行加上：'（注：本建议由AI系统基于限定文献自动生成，仅供参考，不作为最终医疗诊断。）'
                """
                
                try:
                    # 真正向后台查询
                    response = run_async(rag.aquery(
                        prompt, 
                        param=QueryParam(mode="hybrid", user_prompt=user_prompt_template)
                    ))
                    
                    q_status_text.markdown("**✍️[100%] 大模型排版与多模态知识融合完成！**")
                    q_progress_bar.progress(100)
                    time.sleep(0.4)
                    
                    query_status.update(label="✅ 思考与检索完毕", state="complete", expanded=False)
                    
                    # 动态打字机效果呈现最终答案
                    st.write_stream(stream_text(response))
                    
                    # 保存到历史记录
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    query_status.update(label="❌ 检索处理发生错误", state="error", expanded=False)
                    st.error(f"系统错误详情: {str(e)}")

# ==================== Tab 2: 知识图谱 ====================
with tab_graph:
    st.markdown("### 🕸️ 医疗实体关系知识网")
    st.caption("可视化的知识大脑：您可以拖拽节点、使用滚轮放大缩小，查看深层逻辑网络。如果图谱未更新，请点击下方刷新按钮。")
    
    if st.button("🔄 重新加载最新图谱数据"):
        st.rerun()
        
    render_knowledge_graph()
