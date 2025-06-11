from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from agents.supervisor_agent import build_supervisor_agent
from utils.helpers import get_chat_model, get_last_message, get_retriever, pretty_print_messages
app = FastAPI(
    title="LearnDash LMS API",
    description="API for LearnDash LMS with AGUI standards and Agent integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AgentRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    response: str
    agent_type: str
    metadata: Optional[Dict[str, Any]] = None

# Initialize supervisor agent
supervisor_model = get_chat_model(model_name="gemini-2.0-flash")
worker_model = get_chat_model(model_name="gemini-2.0-flash")
retriever = get_retriever(persistent_path="A:/Code/coder/data")
supervisor_graph = build_supervisor_agent(
    supervisor_model=supervisor_model,
    worker_model=worker_model,
    retriever=retriever
)

@app.post("/api/agent/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    try:
        # Process the request through the supervisor agent
        result = supervisor_graph.invoke({
            "messages": [{"role": "user", "content": request.message}],
            # "context": request.context or {}
        })
        pretty_print_messages(result["messages"])
        # Extract the response from the last message
        last_message = result["messages"][-1] if result["messages"][-1].content else result["messages"][-2]
        
        return AgentResponse(
            response=last_message.content,
            agent_type= last_message.type if hasattr(last_message, "type") else "supervisor",
            metadata=result.get("metadata", {})
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
