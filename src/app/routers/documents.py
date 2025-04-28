# src/app/routers/documents.py
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends, # Sử dụng Depends cho Dependency Injection
    Request
)
from fastapi.responses import JSONResponse
from typing import List, Annotated
from pydantic import BaseModel, HttpUrl # Sử dụng HttpUrl để validate URL

# Import dependencies sử dụng đường dẫn tương đối
from ..dependencies import get_vector_store # <<< Dependency Injection
from ..utils import (
    load_docs_from_url,
    process_uploaded_files,
    get_source_list,
    delete_source
)
from ...core.database.vector_store import VectorStore # Import kiểu dữ liệu

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)

# --- Pydantic Models for Request Bodies ---
class UrlUploadRequest(BaseModel):
    url: HttpUrl # Validate URL
    max_depth: int = 2

class DeleteSourceRequest(BaseModel):
    source: str

# --- API Endpoints ---

@router.get("/sources", response_model=List[str])
async def get_all_sources(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)] # Inject VectorStore
):
    """Lấy danh sách tất cả các nguồn tài liệu."""
    sources = get_source_list(vector_store)
    return sources


@router.post("/upload_url")
async def upload_documents_from_url(
    payload: UrlUploadRequest,
    vector_store: Annotated[VectorStore, Depends(get_vector_store)] # Inject VectorStore
):
    """Tải và xử lý tài liệu từ một URL."""
    docs, status = await load_docs_from_url(url=str(payload.url), max_depth=payload.max_depth) # Convert HttpUrl to str

    if "Error" in status and not docs:
         raise HTTPException(status_code=400, detail=status)

    if docs:
        try:
            # Chạy add_documents trong thread pool nếu nó là blocking I/O
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, vector_store.add_documents, docs, True)
            # Cập nhật status nếu thành công
            status += f" | Successfully added {len(docs)} documents to the store."
            return {"status": status}
        except Exception as e:
            print(f"Error adding documents from URL {payload.url} to store: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add documents to store: {str(e)}")
    else:
        # Trả về status từ load_docs_from_url (có thể là "No documents found" hoặc lỗi nhẹ)
        return {"status": status}


@router.post("/upload_files")
async def upload_documents_from_files(
    files: List[UploadFile] = File(...),
    vector_store: Annotated[VectorStore, Depends(get_vector_store)] = Depends(get_vector_store) # Inject VectorStore
):
    """Tải lên và xử lý tài liệu từ các file."""
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    # Kiểm tra loại file (ví dụ)
    allowed_extensions = {".pdf", ".txt", ".md"}
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed for file '{file.filename}'. Allowed types: {', '.join(allowed_extensions)}"
            )

    count, status = await process_uploaded_files(files, vector_store)

    # Phân tích status để trả về mã lỗi phù hợp hơn
    if "error occurred during file processing" in status.lower():
        raise HTTPException(status_code=500, detail=status)
    elif "error" in status.lower() and count == 0:
        raise HTTPException(status_code=400, detail=status) # Lỗi xử lý file cụ thể
    elif count == 0 and not errors: # Không có lỗi nhưng không xử lý được file nào
        return JSONResponse(content={"status": status, "files_processed": count}, status_code=200) # Hoặc 202 Accepted

    return {"status": status, "files_processed": count}


@router.post("/delete") # Hoặc @router.delete("/delete")
async def delete_documents_by_source(
    payload: DeleteSourceRequest,
    vector_store: Annotated[VectorStore, Depends(get_vector_store)] # Inject VectorStore
):
    """Xóa tài liệu dựa trên tên nguồn."""
    source_to_delete = payload.source
    if not source_to_delete:
        raise HTTPException(status_code=400, detail="Source name cannot be empty.")

    # Chạy delete_source trong thread pool nếu nó blocking
    import asyncio
    loop = asyncio.get_event_loop()
    status = await loop.run_in_executor(None, delete_source, source_to_delete, vector_store)

    if "not found" in status.lower():
        raise HTTPException(status_code=404, detail=status)
    elif "error" in status.lower():
        raise HTTPException(status_code=500, detail=status)

    return {"status": status}

