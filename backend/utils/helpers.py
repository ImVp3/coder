from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.graph import MessagesState
from langgraph.types import Command

from infrastructure.vectorstore import ChromaVectorStore

def get_chat_model(model_name: str, temperature: float = 0.0) -> BaseChatModel:
    if model_name.startswith("gemini-"):
        return ChatGoogleGenerativeAI(model=model_name, temperature = temperature)
    else:
        raise ValueError(f"Unsupported model_name: {model_name}")

def get_retriever(
    persistent_path: str ,
    embeddings_model: str = "models/text-embedding-004",
    collection_name: str = "my_documents",
    chunk_config: dict = {"chunk_size": 500,"chunk_overlap": 20 }
    ):
    vectorstore = ChromaVectorStore(    
        persistent_path=persistent_path,
        embeddings_model=embeddings_model,
        collection_name=collection_name,
        chunk_config=chunk_config
    )
    return vectorstore.as_retriever()
def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,  
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,  
        )
    return handoff_tool

def get_last_message(messages: list[BaseMessage]) -> BaseMessage:
    if messages[-1]:
        return messages[-1]
    else:
        return messages[-2]
def pretty_print_messages(messages: list[BaseMessage]):
    print("\n--- Conversation Trace ---")
    for idx, msg in enumerate(messages, 1):
        role = (
            "User" if isinstance(msg, HumanMessage)
            else "Assistant" if isinstance(msg, AIMessage)
            else "System" if isinstance(msg, SystemMessage)
            else type(msg).__name__
        )
        print(f"\n[{idx}] {role}:")
        print(msg.content)
    print("\n--- End of Trace ---\n")
