
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import find_dotenv, load_dotenv

from agents.supervisor_agent import build_supervisor_agent
from infrastructure.vectorstore import ChromaVectorStore
from agents.states import SupervisorState
from utils.helpers import serialize_state


load_dotenv(find_dotenv())

retriever = ChromaVectorStore(persistent_path= "A:/Code/coder/data").as_retriever()
chat_model = ChatGoogleGenerativeAI(model = "gemini-2.0-flash")
agent = build_supervisor_agent(
    retriever= retriever,
    supervisor_model= chat_model,
    worker_model=chat_model
)

async def handle_chat(input_text: str) -> SupervisorState:
    raw_output = await agent.ainvoke({"messages": input_text})
    return SupervisorState(**raw_output)

async def handle_streaming_chat(input_text: str):
    async for raw_output in agent.astream(input = {"messages": input_text}, stream_mode="values"):
        yield serialize_state(raw_output)
