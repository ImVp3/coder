# src/app/dependencies.py
import os
from functools import lru_cache # Cache instance để tránh khởi tạo lại nhiều lần
from fastapi import HTTPException

# Import từ các module core và utils tương đối
from ..core.database.vector_store import VectorStore
from ..core.graph.codegen_graph import CodeGenGraph

# Lấy cấu hình từ biến môi trường (đã load ở main.py)
PERSISTENT_PATH = os.getenv("VECTORSTORE_PATH")
COLLECTION_NAME = os.getenv("VECTORSTORE_COLLECTION")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

# Kiểm tra các biến môi trường cần thiết
if not PERSISTENT_PATH:
    raise ValueError("VECTORSTORE_PATH environment variable not set.")
if not COLLECTION_NAME:
    raise ValueError("VECTORSTORE_COLLECTION environment variable not set.")
if not DEFAULT_MODEL:
    raise ValueError("DEFAULT_MODEL environment variable not set.")
# Kiểm tra GOOGLE_API_KEY nếu model là gemini
if "gemini" in DEFAULT_MODEL.lower() and not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable not set for Gemini model.")


@lru_cache() # Cache kết quả của hàm này
def get_vector_store() -> VectorStore:
    """Dependency function to get a VectorStore instance."""
    try:
        print(f"Initializing VectorStore: Path={PERSISTENT_PATH}, Collection={COLLECTION_NAME}")
        vector_store = VectorStore(
            persistent_path=PERSISTENT_PATH,
            collection_name=COLLECTION_NAME
        )
        # Có thể thêm kiểm tra kết nối ở đây nếu cần
        print("VectorStore initialized successfully.")
        return vector_store
    except Exception as e:
        print(f"FATAL: Failed to initialize VectorStore: {e}")
        # Không raise ở đây, để endpoint tự xử lý nếu không có store
        # Hoặc raise HTTPException để dừng ngay lập tức
        raise HTTPException(status_code=503, detail=f"VectorStore service unavailable: {e}")

@lru_cache() # Cache kết quả của hàm này
def get_codegen_graph() -> CodeGenGraph:
    """Dependency function to get a CodeGenGraph instance."""
    try:
        vector_store = get_vector_store() # Lấy instance vector_store đã được cache
        retriever = vector_store.as_retriever()
        if retriever is None:
            raise ValueError("Failed to create retriever from VectorStore.")

        print(f"Initializing CodeGenGraph with model: {DEFAULT_MODEL}")
        graph = CodeGenGraph(
            retriever=retriever,
            model=DEFAULT_MODEL
        )
        # Có thể thêm kiểm tra graph ở đây nếu cần
        print("CodeGenGraph initialized successfully.")
        return graph
    except Exception as e:
        print(f"FATAL: Failed to initialize CodeGenGraph: {e}")
        raise HTTPException(status_code=503, detail=f"CodeGenGraph service unavailable: {e}")

