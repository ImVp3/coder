from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, START, END
from typing_extensions import Literal
from langgraph.graph.message import MessagesState # Use MessagesState for simplicity
from langchain_core.messages import AIMessage
from .codegen_graph import CodeGenGraph
from .utils.routing import decide_to_route
from .utils.helper import get_model
from ..utils.schema import Code
from ..utils.helper import parse_code_generation

class OverallGraph:
    """
    A parent graph that routes user requests to either the CodeGenGraph
    for code generation tasks or a simple conversational chain for default queries.
    """
    def __init__(self, 
                codegen_graph: CodeGenGraph, 
                model_name: str = "gemini-2.0-flash-lite"   ):
        self.model_name = model_name
        self.codegen_graph = codegen_graph
        self.casual_chain =  get_model(model = self.model_name)
        self.graph = self._create_graph()

    def _create_graph(self):
        """Builds the LangGraph StateGraph."""
        workflow = StateGraph(MessagesState)
        # Define nodes
        workflow.add_node("code_generator", self._call_codegen_graph)
        workflow.add_node("casual_responder", self._call_casual_chain)

        workflow.add_conditional_edges(
            START,
            self._route_question,
            {
                "GENERATION": "code_generator",
                "DEFAULT": "casual_responder",
            }
        )
        workflow.add_edge("code_generator", END)
        workflow.add_edge("casual_responder", END)
        
        return workflow.compile()

    def _route_question(self, state: MessagesState) -> Literal["GENERATION", "DEFAULT"]:
        """Routes the question based on the last message."""
        route = decide_to_route(state, model=self.model_name)
        return route

    def _call_codegen_graph(self, state: MessagesState) -> MessagesState:
        """Invokes the CodeGenGraph."""
        query = state["messages"][-1].content
        codegen_result = self.codegen_graph.invoke(query)["generation"][-1]
        if isinstance(codegen_result, Code):
            result = {"messages": [AIMessage(content = parse_code_generation(codegen_result))]}
        return result
    def _call_casual_chain(self, state: MessagesState) -> MessagesState:
        """Invokes the simple conversational chain."""
        query = state["messages"][-1]
        response = self.casual_chain.invoke(input = [query])
        return {"messages": [response]} 

    def invoke(self, query: str):
        """Invokes the overall graph with the user query."""
        initial_state: MessagesState = {"messages": [("user", query)]}
        final_state = self.graph.invoke(initial_state)
        return final_state 
    def stream(self, query: str, stream_mode: str = "values"):
        initial_state: MessagesState = {"messages": [("user", query)]}
        return self.graph.stream(initial_state, stream_mode=stream_mode)

    def astream(self, query: str, stream_mode: str = "values"):
        initial_state: MessagesState = {"messages": [("user", query)]}
        return self.graph.astream(initial_state, stream_mode=stream_mode)
    def change_parameters(
        self, 
        model: str, 
        temperature: float, 
        max_iterations: int, 
        reflect: bool, 
        framework: str|None = None
        ):
        return self.codegen_graph.change_parameters(model, temperature, max_iterations, reflect, framework)
    def get_current_parameters (self) -> dict:
        return self.codegen_graph.get_current_parameters()