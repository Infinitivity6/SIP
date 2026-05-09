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
# 1. 持久化后台事件循环 (防止死机卡死)
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
# 2. 打字机流式输出生成器
# ==========================================
def stream_text(text, delay=0.03):
    """模拟打字机效果，逐字输出"""
    for char in text:
        yield char
        time.sleep(delay)

# ==========================================
# 3. 核心引擎与模型配置
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
    run_async(rag.initialize_storages())
    return rag

rag = init_rag_engine()

# ==========================================
# 4. 图谱可视化功能
# ==========================================
def render_knowledge_graph():
    graph_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    if os.path.exists(graph_path):
        try:
            # 读取 GraphML 文件
            G = nx.read_graphml(graph_path)
            if len(G.nodes) == 0:
                st.warning("知识图谱中暂无节点，请先录入有效文献。")
                return
            
            # 使用 Pyvis 创建交互式网络图
            net = Network(height='400px', width='100%', bgcolor='#0E1117', font_color='white')
            # 开启物理斥力引擎，让图谱自动散开变好看
            net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
            net.from_nx(G)
            
            # 保存为临时 HTML 并渲染到 Streamlit
            html_path = os.path.join(WORKING_DIR, "temp_graph.html")
            net.save_graph(html_path)
            with open(html_path, 'r', encoding='utf-8') as f:
                html_data = f.read()
            
            st.markdown("### 🕸️ 知识图谱 (Knowledge Graph) 可视化")
            st.caption("您可以拖拽节点、放大缩小，查看实体之间的深度关联。")
            components.html(html_data, height=410)
        except Exception as e:
            st.error(f"图谱渲染失败: {e}")
    else:
        st.info("暂无图谱数据，请先在侧边栏上传文献。")

# ==========================================
# 5. 前端侧边栏：知识库录入模块
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100)
    st.title("🏥 知识库后台")
    
    uploaded_file = st.file_uploader("上传医疗知识库 (.txt)", type=["txt"])
    
    if st.button("开始解析并录入知识库", type="primary", use_container_width=True):
        if uploaded_file is not None:
            text_content = uploaded_file.getvalue().decode("utf-8")
            
            # 使用带进度的详细展示框
            with st.status("🧠 正在处理知识库...", expanded=True) as status:
                st.write("⏳ [10%] 读取文件成功，准备预处理...")
                time.sleep(0.5) # 模拟过程，提升视觉体验
                
                st.write("🔪 [30%] 正在对长文本进行语义切片...")
                time.sleep(0.5)
                
                st.write("🤖 [50%] 大模型正在提取医学实体与关联关系（此步耗时较长，请耐心等待）...")
                try:
                    # 执行耗时的核心处理
                    run_async(rag.ainsert(text_content))
                    
                    st.write("💾 [90%] 正在将知识图谱与向量索引写入本地数据库...")
                    time.sleep(0.5)
                    st.write("✨ [100%] 知识融合完毕！")
                    status.update(label="✅ 知识图谱构建完成！", state="complete", expanded=False)
                    st.success("文献已成功融合到系统大脑中！")
                except Exception as e:
                    status.update(label="❌ 录入失败", state="error", expanded=False)
                    st.error(f"处理失败: {e}")
        else:
            st.error("请先上传文件！")
            
    st.divider()
    # 图谱显示开关
    show_graph = st.checkbox("👁️ 显示实体知识图谱", value=False)
    
    st.caption("系统内核：LightRAG (GraphRAG)\n\n前端渲染：Streamlit + Pyvis")

# ==========================================
# 6. 主界面：可视区与智能问答聊天模块
# ==========================================
st.title("👨‍⚕️ 三高知识智能问答平台")

# 如果侧边栏勾选了显示图谱，则在聊天框上方渲染图谱
if show_graph:
    render_knowledge_graph()
    st.divider()

if "messages" not in st.session_state:
    st.session_state.messages =[
        {"role": "assistant", "content": "您好！我是三高智能健康顾问。我已经学习了相关的医学知识图谱，请问有什么关于高血压、高血糖或高血脂的问题我可以帮您？"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("例如：高血压患者的饮食禁忌有哪些？"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # 优化 2：带虚拟进度条的思考过程
        with st.status("💡 系统正在深度思考...", expanded=True) as query_status:
            st.write("🔍[20%] 正在解析患者意图...")
            time.sleep(0.3)
            st.write("📐 [50%] 正在向量数据库中进行语义匹配检索...")
            time.sleep(0.3)
            st.write("🕸️ [80%] 正在知识图谱中游走寻找关联实体规律...")
            time.sleep(0.3)
            st.write("✍️ [95%] 正在融合知识，大模型排版生成中...")
            
            user_prompt_template = """
            你是一位严谨的临床医学专家。
            请【严格且仅根据】以上检索到的知识库内容来回答用户的问题。
            要求：
            1. 回答要有条理，并在使用了知识库信息的句子后面标注来源（例如：[1]、[2]）。
            2. 在回答的最末尾另起一行加上：'（注：本建议由系统基于限定文献自动生成，仅供参考，不作为最终医疗诊断。）'
            """
            
            try:
                # 获取答案内容
                response = run_async(rag.aquery(
                    prompt, 
                    param=QueryParam(mode="hybrid", user_prompt=user_prompt_template)
                ))
                st.write("✨ [100%] 答案生成完毕！")
                # 完成后，让状态框自动折叠，不遮挡视线
                query_status.update(label="✅ 思考与检索完毕", state="complete", expanded=False)
                
                # 优化 3：高级打字机效果！直接在外层渲染输出
                st.write_stream(stream_text(response, delay=0.015))
                
                # 保存到聊天记录
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                query_status.update(label="❌ 检索处理发生错误", state="error", expanded=False)
                st.error(f"系统错误详情: {str(e)}")
