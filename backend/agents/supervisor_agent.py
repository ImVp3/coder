from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.graph import StateGraph, START, MessagesState, END

from langgraph.types import Command
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage
from utils.helpers import create_handoff_tool
from .chains import create_synthesis_chain
from . import build_codegen_graph, build_testgen_graph
from .states import SupervisorState
from utils.schemas import FlowStep

def build_supervisor_agent(supervisor_model: str|BaseChatModel, worker_model: str|BaseChatModel, retriever):
    synthesis_chain = create_synthesis_chain(model=worker_model)
    
    @tool(description="Synthesizes final answer from the full conversation.")
    def synthesis_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        conversation_log = "\n".join(
            f"{getattr(msg, 'role', msg.__class__.__name__)}: {msg.content}"
            for msg in state["messages"]
        )
        final_answer  = synthesis_chain.invoke({
            "user_request": state["messages"][0].content,
            "conversation": conversation_log
        })
        return Command(
            goto=END,
            update={
                "messages": state["messages"] + [
                    ToolMessage(content="Synthesis complete", tool_call_id=tool_call_id),
                    final_answer 
                ],
                "flow":  [FlowStep(agent = "supervisor", step = "synthesis")]
            }
        )
    def synthesis(state: SupervisorState) -> dict:
        conversation_log = "\n".join(
            f"{getattr(msg, 'role', msg.__class__.__name__)}: {msg.content}"
            for msg in state["messages"]
        )
        final_answer  = synthesis_chain.invoke({
            "user_request": state["messages"][0].content,
            "conversation": conversation_log
        })
        return {
                "messages": [final_answer],
                "flow":  [FlowStep(agent = "supervisor", step = "synthesis")]
            }
    # Define workers
    codegen_agent = build_codegen_graph(retriever=retriever, code_gen_model=worker_model)
    testgen_agent = build_testgen_graph(model=worker_model)

    # Handoffs
    assign_to_research_agent = create_handoff_tool(
        agent_name="codegen_agent",
        description="Assign task to a code generation agent.",
    )

    assign_to_math_agent = create_handoff_tool(
        agent_name="testgen_agent",
        description="Assign task to a unit-test generation agent.",
    )
    supervisor_agent = create_react_agent(
        model= supervisor_model,
        tools=[assign_to_research_agent, assign_to_math_agent],
        prompt=(
        "You are a supervisor managing two agents:\n"
        "- a testgen_agent agent. Assign tasks that are related to unit testing to this agent.\n"
        "- a codegen_agent agent. Assign tasks that are related to code generation to this agent except generate unit test.\n\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself **until you determine that agents have completed their respective tasks**.\n"
        "When you have collected all relevant outputs, continue with the synthesis node to synthesize the final answer."
        ),
        name="supervisor",
    )

    supervisor_graph = StateGraph(SupervisorState)
    supervisor_graph.add_node("codegen_agent",codegen_agent)
    supervisor_graph.add_node("testgen_agent",testgen_agent)
    supervisor_graph.add_node("synthesis", synthesis)
    supervisor_graph.add_node(supervisor_agent, destinations=("codegen_agent", "testgen_agent"))
    supervisor_graph.add_edge(START, "supervisor")
    supervisor_graph.add_edge("codegen_agent", "supervisor")
    supervisor_graph.add_edge("testgen_agent", "supervisor")
    supervisor_graph.add_edge("supervisor", "synthesis")
    supervisor_graph.add_edge("synthesis", END)
    supervisor_graph = supervisor_graph.compile()
    return supervisor_graph