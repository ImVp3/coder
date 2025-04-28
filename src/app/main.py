# src/app/main.py
import os
import sys
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# --- Load Environment Variables ---
# Tìm file .env ở thư mục gốc của project (coder/)
dotenv_path = find_dotenv(raise_error_if_not_found=False) # Không báo lỗi nếu không tìm thấy
if dotenv_path:
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("Warning: .env file not found. Relying on system environment variables.")

# --- Add project root to sys.path ---
# Cần thiết để import từ src/core khi chạy từ src/app
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    print(f"Adding project root to sys.path: {project_root}")
    sys.path.insert(0, project_root)

# --- Import Routers and Dependencies ---
# Sử dụng import tương đối từ vị trí file này
try:
    from .routers import chat, documents
    from .dependencies import get_vector_store, get_codegen_graph # Import dependencies
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current sys.path: {sys.path}")
    print("Ensure your project structure and PYTHONPATH are correct, and run from the project root (coder/).")
    sys.exit(1)

# --- Lifespan Management (Recommended over startup/shutdown events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup...")
    try:
        # Khởi tạo (và cache) các dependencies khi ứng dụng khởi động
        print("Pre-initializing dependencies...")
        _ = get_vector_store()
        _ = get_codegen_graph()
        print("Dependencies initialized.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize dependencies during startup: {e}")
        # Quyết định xem có nên dừng ứng dụng hay không
        # raise RuntimeError("Failed to initialize core services.") from e
    print("Code Assistant API is ready.")
    yield
    # Code to run on shutdown
    print("Application shutdown...")
    # Thêm logic dọn dẹp nếu cần (ví dụ: đóng kết nối db)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Code Assistant API (FastAPI)",
    lifespan=lifespan # Sử dụng lifespan manager
)

# --- Mount Static Files ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.isdir(static_dir):
    print(f"Warning: Static directory not found at {static_dir}")
else:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"Mounted static files from: {static_dir}")

# --- Setup Templates ---
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.isdir(templates_dir):
    print(f"Warning: Templates directory not found at {templates_dir}")
    templates = None
else:
    templates = Jinja2Templates(directory=templates_dir)
    print(f"Templates directory configured: {templates_dir}")

# --- Include Routers ---
# Các dependencies sẽ được inject tự động vào các endpoint cần chúng
app.include_router(documents.router)
app.include_router(chat.router)
print("Included API routers.")

# --- Root Endpoint to Serve HTML ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Phục vụ trang HTML chính của ứng dụng."""
    if not templates:
        raise HTTPException(status_code=500, detail="Server configuration error: Templates not found.")
    return templates.TemplateResponse("index.html", {"request": request})

