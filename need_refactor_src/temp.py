import streamlit as st
from dotenv import load_dotenv, find_dotenv
import os

# Imports từ project của bạn
# Đảm bảo các đường dẫn này chính xác và các module có thể được import
try:
    from core.graph.codegen_graph import CodeGenGraph
    from core.graph.unittest_gen_graph import UnitTestWorkflow
    from core.agents.main import create_supervisor_agent, create_research_agent
    from core.database.vector_store import VectorStore
    from core.graph.utils.helper import get_model
except ImportError as e:
    st.error(f"Lỗi import module 'core': {e}. Hãy đảm bảo rằng thư mục 'core' của bạn nằm trong PYTHONPATH hoặc cùng cấp với file app Streamlit này.")
    st.stop() # Ngăn không cho app chạy tiếp nếu không import được

# --- Tải cấu hình và khởi tạo các thành phần (chạy một lần) ---
@st.cache_resource # Sử dụng cache_resource để tránh khởi tạo lại trên mỗi lần tương tác
def initialize_components():
    """
    Tải biến môi trường và khởi tạo tất cả các thành phần cần thiết.
    """
    load_dotenv(find_dotenv())

    default_model_name = os.getenv("DEFAULT_MODEL")
    vectorstore_path = os.getenv("VECTORSTORE_PATH")
    vectorstore_collection = os.getenv("VECTORSTORE_COLLECTION")

    # Kiểm tra các biến môi trường thiết yếu
    if not all([default_model_name, vectorstore_path, vectorstore_collection]):
        missing_vars = [var for var, val in [("DEFAULT_MODEL", default_model_name),
                                             ("VECTORSTORE_PATH", vectorstore_path),
                                             ("VECTORSTORE_COLLECTION", vectorstore_collection)] if not val]
        st.error(f"Thiếu các biến môi trường sau: {', '.join(missing_vars)}. Vui lòng kiểm tra file .env hoặc cài đặt môi trường của bạn.")
        return None # Trả về None nếu thiếu

    try:
        llm = get_model(model=default_model_name)

        vector_database = VectorStore(
            persistent_path=vectorstore_path,
            collection_name=vectorstore_collection
        )
        code_generator = CodeGenGraph(
            model=default_model_name, # Hoặc truyền llm đã khởi tạo nếu CodeGenGraph chấp nhận
            retriever=vector_database.as_retriever()
        )
        unit_test_generator = UnitTestWorkflow() # Giả sử không cần tham số phức tạp
        
        # Đổi tên biến để tránh xung đột nếu create_research_agent là hàm
        research_agent_instance = create_research_agent( 
            model=llm
        )

        supervisor = create_supervisor_agent(
            llm=llm,
            agents=[
                code_generator.as_graph(),
                unit_test_generator.as_graph(),
                research_agent_instance # Sử dụng instance đã khởi tạo
            ],
            add_handoff_back_messages=True,
            output_mode="full_history" # Rất quan trọng để hiển thị lịch sử
        )
        return supervisor, default_model_name # Chỉ trả về supervisor hoặc các thông tin cần hiển thị
    except Exception as e:
        st.error(f"Lỗi trong quá trình khởi tạo components: {e}")
        st.exception(e) # Hiển thị traceback chi tiết trong app
        return None

# --- Giao diện người dùng Streamlit ---
st.set_page_config(layout="wide", page_title="Supervisor Agent Demo")
st.title("🎬 Demo Hệ Thống Multi-Agent với Supervisor")
st.markdown("Ứng dụng này minh họa cách một Supervisor Agent điều phối các agent con (Code Generator, Unit Test Generator, Research Agent) để thực hiện yêu cầu phức tạp.")

# Khởi tạo các components
init_result = initialize_components()

if init_result:
    supervisor_agent, model_name_loaded = init_result
    
    st.sidebar.header("Thông Tin Cấu Hình")
    st.sidebar.success(f"✅ Components đã được khởi tạo thành công!")
    st.sidebar.info(f"LLM Model đang sử dụng: `{model_name_loaded}`")
    # Bạn có thể thêm thông tin khác ở đây nếu muốn (ví dụ: đường dẫn VectorStore)

    st.markdown("---")
    st.header("📝 Nhập Yêu Cầu Của Bạn")
    st.markdown("Supervisor agent sẽ phân tích yêu cầu này và ủy quyền cho các agent phù hợp.")

    # Yêu cầu mặc định từ code của bạn
    default_request = """Please write a Python program that implements a simple command-line contact book. Create a unit Test for this program after the code is generated.

The program should support the following features:

Add Contact:
Prompt the user for a name and a phone number.
Store these as a new contact. Ensure a name cannot be added if it already exists (names are unique identifiers).

View Contact:
Prompt the user for a name.
If the contact exists, display their name and phone number.
If not found, inform the user.

Delete Contact:
Prompt the user for a name.
If the contact exists, remove it.
If not found, inform the user.

View All Contacts:
Display all stored contacts, showing both name and phone number for each.

Requirements & Constraints:
Use a dictionary to store the contacts, where the key is the contact's name (string) and the value is the phone number (string).
The program should loop, allowing the user to perform multiple actions until they choose an "exit" option.
Provide a simple menu for the user to choose an action (e.g., "1. Add", "2. View", "3. Delete", "4. View All", "5. Exit").
Handle basic input validation where appropriate (e.g., ensure the user enters a number for menu choices if that's how you structure it).
"""
    user_request = st.text_area("Nhập yêu cầu:", value=default_request, height=350,
                                help="Mô tả chi tiết tác vụ bạn muốn supervisor thực hiện, ví dụ: tạo code, viết unit test, nghiên cứu...")

    if st.button("🚀 Chạy Supervisor Agent", type="primary", use_container_width=True):
        if not user_request.strip():
            st.warning("⚠️ Vui lòng nhập yêu cầu.")
        else:
            st.markdown("---")
            st.header("🔍 Kết Quả Thực Thi & Lịch Sử Tương Tác")
            with st.spinner("Supervisor agent đang xử lý yêu cầu của bạn... Quá trình này có thể mất một chút thời gian. ⏳"):
                try:
                    # Input cho supervisor agent thường là một dict với key "messages"
                    input_payload = {"messages": [("user", user_request)]}
                    
                    # Gọi supervisor agent
                    results = supervisor_agent.invoke(input_payload)

                    # Hiển thị kết quả - `output_mode="full_history"` sẽ trả về toàn bộ lịch sử message
                    if isinstance(results, dict) and "messages" in results:
                        st.info(f"Hoàn thành! {len(results['messages'])} tin nhắn trong lịch sử tương tác.")
                        
                        for i, message in enumerate(results["messages"]):
                            msg_type = getattr(message, 'type', 'unknown_type')
                            msg_content = getattr(message, 'content', str(message))
                            msg_name = getattr(message, 'name', None)
                            additional_kwargs = getattr(message, 'additional_kwargs', {})
                            tool_calls = additional_kwargs.get('tool_calls', [])
                            function_call_details = additional_kwargs.get('function_call', None)

                            role_icon = "👤" if msg_type.lower() == "human" or msg_name is None else \
                                        "🤖" if msg_type.lower() == "ai" or msg_name else \
                                        "🛠️" if msg_type.lower() == "tool" else "💬"
                            
                            with st.expander(f"{role_icon} **Tin nhắn {i+1}:** `{msg_type.upper()}` {f'- Agent: `{msg_name}`' if msg_name else ''}", expanded= i == len(results["messages"]) -1 ): # Mở rộng tin nhắn cuối
                                st.markdown(f"**Nội dung:**")
                                # Nếu nội dung là code Python, hiển thị dưới dạng code block
                                if "python" in str(msg_content).lower() and ("def " in msg_content or "import " in msg_content or "class " in msg_content):
                                    # Cố gắng trích xuất code nếu nó nằm trong markdown backticks
                                    cleaned_content = msg_content
                                    if "```python" in msg_content:
                                        cleaned_content = msg_content.split("```python\n", 1)[-1].split("\n```", 1)[0]
                                    elif "```" in msg_content:
                                         cleaned_content = msg_content.split("```\n", 1)[-1].split("\n```", 1)[0]
                                    st.code(cleaned_content, language="python")
                                else:
                                    st.markdown(f"```text\n{msg_content}\n```" if isinstance(msg_content, str) and len(msg_content) > 80 else str(msg_content))

                                if tool_calls:
                                    st.markdown("**Lệnh gọi Tool (Tool Calls):**")
                                    for tc_idx, tool_call in enumerate(tool_calls):
                                        st.json(tool_call, expanded=False)
                                if function_call_details:
                                    st.markdown("**Lệnh gọi Hàm (Function Call):**")
                                    st.json(function_call_details, expanded=False)
                                if additional_kwargs and not tool_calls and not function_call_details:
                                    st.markdown("**Thông tin thêm (Additional Kwargs):**")
                                    st.json(additional_kwargs, expanded=False)
                    else:
                        st.warning("Kết quả trả về không có định dạng lịch sử tin nhắn như mong đợi.")
                        st.json(results) # Hiển thị raw JSON nếu không đúng định dạng

                except Exception as e:
                    st.error(f"🚫 Đã xảy ra lỗi trong quá trình thực thi:")
                    st.exception(e) # Hiển thị traceback đầy đủ
else:
    st.error("Không thể khởi tạo các thành phần. Vui lòng kiểm tra log và cấu hình.")

st.markdown("---")
st.sidebar.markdown("---")
st.sidebar.markdown("🧑‍💻 **Thông tin thêm:**")
st.sidebar.markdown("Ứng dụng này sử dụng Streamlit để tạo giao diện và LangGraph để xây dựng hệ thống multi-agent. Các agent giao tiếp và được điều phối bởi một Supervisor Agent trung tâm.")
st.sidebar.markdown("Mã nguồn Streamlit này được tạo để demo đoạn code Python được cung cấp.")