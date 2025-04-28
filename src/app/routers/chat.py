# src/app/routers/chat.py
import asyncio
import json
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Depends, # Sử dụng Depends cho Dependency Injection
    Request
)
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from typing import Optional, Annotated, AsyncGenerator, Dict, Any

# Import dependencies sử dụng đường dẫn tương đối
from ..dependencies import get_codegen_graph # <<< Dependency Injection
from ..utils import parse_code_generation
from ...core.graph.codegen_graph import CodeGenGraph # Import kiểu dữ liệu

router = APIRouter(
    prefix="/api",
    tags=["chat & settings"],
)

# --- Pydantic Models ---
class SettingsPayload(BaseModel):
    model: str
    temperature: float = Field(..., ge=0.0, le=1.0) # Thêm validation
    max_iterations: int = Field(..., ge=1, le=10) # Thêm validation
    reflect: bool
    framework: Optional[str] = None

# --- API Endpoints ---

@router.post("/settings")
async def update_graph_settings(
    payload: SettingsPayload,
    graph: Annotated[CodeGenGraph, Depends(get_codegen_graph)] # Inject CodeGenGraph
):
    """Cập nhật các tham số của CodeGenGraph."""
    try:
        # Gọi hàm change_parameters của graph instance
        # Đảm bảo hàm này tồn tại và chấp nhận các tham số này
        update_status = graph.change_parameters(
            model=payload.model,
            temperature=payload.temperature,
            max_iterations=payload.max_iterations,
            reflect=payload.reflect,
            framework=payload.framework
        )
        status_message = update_status if isinstance(update_status, str) else "Settings updated successfully."
        return {"status": status_message}
    except AttributeError:
         raise HTTPException(status_code=500, detail="Graph object does not have 'change_parameters' method or it failed.")
    except Exception as e:
        print(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


async def chat_event_generator(
    user_message: str,
    graph: CodeGenGraph # Nhận graph đã được inject
) -> AsyncGenerator[str, None]:
    """Async generator for Server-Sent Events during chat."""
    current_flow_str = "Initializing..."
    try:
        # Stream the response from the graph
        # Sử dụng astream nếu graph hỗ trợ async streaming
        # Nếu không, cần chạy graph.stream trong executor
        if hasattr(graph, 'astream'):
            async for state in graph.astream({"messages": [("user", user_message)]}): # Truyền input đúng format của graph
                # Xử lý state trả về từ astream
                yield await process_graph_state(state, current_flow_str)
        elif hasattr(graph, 'stream'):
             # Chạy stream đồng bộ trong executor
             loop = asyncio.get_event_loop()
             # Cần một cách để lấy state từ stream đồng bộ trong generator async
             # Cách tiếp cận đơn giản là chạy toàn bộ stream và yield kết quả cuối,
             # nhưng sẽ mất tính streaming thực sự.
             # Để streaming thực sự với stream đồng bộ, cần queue hoặc cơ chế phức tạp hơn.
             # Ví dụ đơn giản hóa: chạy và lấy kết quả cuối (không lý tưởng)
             # final_state = await loop.run_in_executor(None, lambda: list(graph.stream({"messages": [("user", user_message)]}))[-1])
             # yield await process_graph_state(final_state, current_flow_str)

             # ---> Cách tốt hơn nếu phải dùng stream đồng bộ: Dùng Queue
             import queue
             from functools import partial

             q = queue.Queue()

             def run_stream_in_thread(msg, graph_stream, q_put):
                 try:
                     for item in graph_stream({"messages": [("user", msg)]}):
                         q_put(item)
                     q_put(None) # Signal end
                 except Exception as thread_e:
                     q_put(Exception(f"Error in stream thread: {thread_e}"))


             stream_func = partial(run_stream_in_thread, user_message, graph.stream, q.put)
             await loop.run_in_executor(None, stream_func)

             while True:
                 state = q.get()
                 if state is None:
                     break
                 if isinstance(state, Exception):
                     raise state # Ném lỗi từ thread ra generator
                 yield await process_graph_state(state, current_flow_str)

        else:
             raise NotImplementedError("Graph object must have 'astream' or 'stream' method.")

        # Signal the end of the stream
        yield json.dumps({"type": "end", "content": "Stream finished"}) + "\n\n"

    except Exception as e:
        print(f"Error during chat stream: {e}")
        error_message = f"An error occurred: {str(e)}"
        # Đảm bảo đóng gói lỗi trong format SSE
        yield json.dumps({"type": "error", "content": error_message}) + "\n\n"

async def process_graph_state(state: Dict[str, Any], current_flow: str) -> str:
    """Xử lý một state từ graph stream và tạo chuỗi SSE."""
    sse_data = None
    # Cập nhật flow nếu có thay đổi
    # Giả sử state['flow'] là list các node name
    if "flow" in state and isinstance(state["flow"], list):
        new_flow_str = " -> ".join(state["flow"])
        if new_flow_str != current_flow:
            current_flow = new_flow_str # Cập nhật flow hiện tại (cần truyền lại vào generator)
            sse_data = {"type": "flow", "content": current_flow}

    # Xử lý generation nếu có
    # Giả sử state['generation'] chứa object có code, imports, prefix
    elif "generation" in state and state["generation"]:
        # Lấy object generation cuối cùng nếu là list, hoặc chính nó nếu không phải list
        gen_obj = state["generation"]
        if isinstance(gen_obj, list):
            gen_obj = gen_obj[-1] if gen_obj else None

        if gen_obj:
            parsed_message = parse_code_generation(gen_obj)
            if parsed_message:
                # Gửi full message mỗi khi có generation mới
                sse_data = {"type": "full_message", "content": parsed_message}

    if sse_data:
        return json.dumps(sse_data) + "\n\n"
    else:
        return "" # Trả về chuỗi rỗng nếu state không cần gửi


@router.get("/chat/stream")
async def chat_stream_endpoint(
    request: Request, # Thêm Request để kiểm tra client disconnect
    message: str = Query(..., min_length=1), # Yêu cầu message không rỗng
    graph: Annotated[CodeGenGraph, Depends(get_codegen_graph)] = Depends(get_codegen_graph) # Inject Graph
):
    """Endpoint SSE để stream phản hồi chat."""

    async def event_publisher():
        try:
            async for data in chat_event_generator(message, graph):
                # Kiểm tra xem client còn kết nối không
                if await request.is_disconnected():
                    print("Client disconnected, stopping stream.")
                    break
                yield data
        except Exception as e:
            # Log lỗi và gửi thông báo lỗi tới client nếu có thể
            print(f"Error in event_publisher: {e}")
            # Cố gắng gửi lỗi cuối cùng nếu stream chưa đóng
            yield json.dumps({"type": "error", "content": f"Server error: {e}"}) + "\n\n"

    return EventSourceResponse(event_publisher())

