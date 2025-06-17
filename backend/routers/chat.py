from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.agent_service import handle_chat, handle_streaming_chat
from agents.states import SupervisorState

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatInput(BaseModel):
    input: str

@router.post("/ask", response_model= SupervisorState)
async def ask_agent(input_data: ChatInput):
    input = input_data.input
    output = await handle_chat(input)
    print(input, "\n", output)
    return output
    # return await handle_chat(input_data.input)
@router.post("/stream", response_model= SupervisorState)
async def stream_agent(input_data: ChatInput):
    return StreamingResponse(handle_streaming_chat(input_data.input), media_type="text/event-stream")
