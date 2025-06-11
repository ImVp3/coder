# ----- IMPORTS -----
import ast
from typing import List

from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from utils.schemas import Code
from utils.helpers import get_chat_model
from .states import CodeGenState
from .chains import create_code_gen_chain

# ----- ENV SETUP -----
load_dotenv(find_dotenv())


# ----- CONSTANTS -----
EMPTY_DOC = Document(page_content="No documentation")


# ----- NODE FUNCTIONS -----
def retrieve_node(state: CodeGenState, retriever) -> dict:
    query = state["messages"][0].content if state["messages"] else ""
    docs = [EMPTY_DOC]
    if query:
        try:
            docs = retriever.invoke(query)
        except Exception:
            pass
    return {"documentation": docs, "flow": ["node:retrieve"]}


def generate_node(state: CodeGenState, chain, framework: str) -> dict:
    messages = list(state["messages"])
    if state.get("error"):
        messages.append(HumanMessage(content="Now, try again..."))

    docs = "\n".join(doc.page_content for doc in state.get("documentation", []))
    result: Code = chain.invoke({"context": docs, "question": messages, "framework": framework})
    messages.append(AIMessage(content=f"{result.prefix}\nImports:\n{result.imports}\nCode:\n{result.code}"))

    return {
        "generation": [result],
        "messages": messages,
        "iterations": state.get("iterations", 0) + 1,
        "flow": ["node:generate"]
    }


def check_code_node(state: CodeGenState) -> dict:
    generations = state.get("generation", [])
    if not generations:
        return {
            "messages": state["messages"] + [SystemMessage(content="No generation")],
            "error": True,
            "flow": ["node:check_code:no_generation"]
        }

    try:
        code: Code = Code.model_validate(generations[-1])
    except Exception:
        return {
            "messages": state["messages"] + [SystemMessage(content="Invalid format")],
            "error": True,
            "flow": ["node:check_code:invalid_format"]
        }

    full_code = f"{code.imports}\n{code.code}"
    try:
        ast.parse(full_code)
        return {"error": False, "flow": ["node:check_code:passed"]}
    except SyntaxError as e:
        msg = (
            f"Syntax error:\nLine {e.lineno}, Offset {e.offset}\n{e.msg}\n"
            f"```python\n{e.text.strip() if e.text else ''}```"
        )
        return {
            "messages": state["messages"] + [HumanMessage(content=msg)],
            "error": True,
            "flow": ["node:check_code:failed"]
        }


def reflect_node(state: CodeGenState, chain, framework: str) -> dict:
    docs = "\n".join(doc.page_content for doc in state.get("documentation", []))
    result: Code = chain.invoke({
        "context": docs,
        "question": state["messages"],
        "framework": framework
    })
    return {
        "messages": state["messages"] + [AIMessage(content=f"Reflection: {result.prefix}")],
        "flow": ["node:reflect"]
    }


def decide_next_node(state: CodeGenState, max_iter: int, reflect: bool) -> str:
    if not state.get("error") or state.get("iterations", 0) >= max_iter:
        return "end"
    return "reflect" if reflect else "generate"


# ----- GRAPH BUILD FUNCTION -----
def build_codegen_graph(retriever, code_gen_model: str|BaseChatModel, framework: str = "python", max_iter: int = 3, enable_reflect: bool = True):
    codegen_chain = create_code_gen_chain(model = code_gen_model)
    builder = StateGraph(CodeGenState)

    # Add nodes
    builder.add_node("retrieve", lambda s: retrieve_node(s, retriever))
    builder.add_node("generate", lambda s: generate_node(s, codegen_chain, framework))
    builder.add_node("check_code", check_code_node)
    builder.add_node("reflect", lambda s: reflect_node(s, codegen_chain, framework))

    # Set graph edges
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "check_code")
    builder.add_conditional_edges(
        "check_code",
        lambda s: decide_next_node(s, max_iter, enable_reflect),
        {
            "end": END,
            "reflect": "reflect",
            "generate": "generate"
        }
    )
    builder.add_edge("reflect", "generate")

    return builder.compile("codegen_agent")
