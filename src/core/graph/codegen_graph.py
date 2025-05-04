from typing import Dict
from langgraph.graph import END, StateGraph, START
from langchain.schema.retriever import BaseRetriever
from .utils.state import CodeGenState
from .utils import nodes
from .utils.routing import decide_to_finish
from .utils.helper import create_code_gen_chain
class CodeGenGraph: 
    def __init__(self, 
                retriever: BaseRetriever ,
                model: str, 
                temperature: float = 0.0,
                max_iterations: int = 3,
                reflect: bool = True, 
                framework: str = ""
                ):
        self.max_iterations = max_iterations
        self.reflect = reflect
        self.framework = framework
        self.model = model 
        self.temperature = temperature
        self.code_gen_chain = create_code_gen_chain(model, temperature)
        self.graph = self.create_graph()
        if isinstance(retriever, BaseRetriever):
            self.retriever = retriever
        else:
            raise ValueError("Retriever must be a BaseRetriever.")
    def create_graph(self):
        workflow = StateGraph(CodeGenState)
        ## Add Nodes
        workflow.add_node(
            "retrieve",
            lambda state: nodes.retrieve_docs(state, self.retriever)
        )
        workflow.add_node(
            "generate",
            lambda state: nodes.generate(state, self.code_gen_chain, self.framework)
        ) 
        workflow.add_node("check_code",nodes.static_syntax_check_v2)  
        workflow.add_node("reflect",
                        lambda state: nodes.reflect(state, self.code_gen_chain, self.framework),
                        ) 
        ## Add Edges
        workflow.add_edge(START, "generate")
        workflow.add_edge("generate", "check_code")
        workflow.add_conditional_edges(
            "check_code",
            lambda state: decide_to_finish(state, self.max_iterations, self.reflect),
            {
                "end": END,
                "reflect": "reflect",
                "generate": "generate",
            }
        )
        workflow.add_edge("reflect", "generate")
        graph = workflow.compile()
        return graph

    def invoke(self, query: str):
        state = {
            "messages": [("user", query)],
            "documentation": [],
            "iterations": 0,
            "error": False,
            "flow": ["START"]
        }
        return self.graph.invoke(state)
    def stream(self, query: str, stream_mode: str = "values"):
        state = {
            "messages": [("user", query)],
            "documentation": [],
            "iterations": 0,
            "error": False,
            "flow": ["START"]
        }
        return self.graph.stream(state, stream_mode= stream_mode)
    def astream(self, query: str, stream_mode: str = "values"):
        state = {
            "messages": [("user", query)],
            "documentation": [],
            "iterations": 0,
            "error": False,
            "flow": ["START"]
        }
        return self.graph.astream(state, stream_mode= stream_mode)
    def change_parameters(self, model: str, temperature: float, max_iterations: int, reflect: bool, framework: str|None = None):
        self.code_gen_chain = create_code_gen_chain(model, temperature)
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.reflect = reflect
        self.framework = framework if framework else "any framework"
        self.graph = self.create_graph()
        return f"Parameters updated! Model: {model}, Temperature: {temperature}, Max Iterations: {self.max_iterations}, Reflect: {self.reflect}, Framework: {self.framework}"
    def get_current_parameters (self) -> Dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_iterations": self.max_iterations,
            "reflect": self.reflect,
            "framework": self.framework
        }
    def visualize_graph(self, output_format: str = 'mermaid') -> str | bytes:
        """
        Visualizes the compiled LangGraph.

        Args:
            output_format (str): The desired output format.
                                'mermaid' returns the MermaidJS syntax string.
                                'png' returns the PNG image bytes (requires pygraphviz and graphviz).
                                'ascii' returns an ASCII representation string.

        Returns:
            str | bytes: The graph visualization in the specified format.

        Raises:
            ValueError: If an unsupported output_format is provided.
            ImportError: If 'png' format is requested but pygraphviz/graphviz is not installed.
        """
        if output_format == 'mermaid':
            return self.graph.get_graph().draw_mermaid()
        elif output_format == 'png':
            try:
                # This method often requires pygraphviz and a Graphviz installation
                return self.graph.get_graph().draw_png()
            except ImportError as e:
                raise ImportError("Drawing PNG requires pygraphviz and Graphviz installation. "
                                "Install with: pip install pygraphviz and ensure Graphviz is in your system PATH.") from e
            except Exception as e:
                print(f"Error drawing PNG: {e}")
                raise
        elif output_format == 'ascii':
            return self.graph.get_graph().draw_ascii()
        else:
            raise ValueError(f"Unsupported output_format: {output_format}. Choose 'mermaid', 'png', or 'ascii'.")
