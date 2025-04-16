from langgraph.graph import END, StateGraph, START
from .schema import State
from . import workflow_utils as wu

class CodeGenGraph:
    def __init__(self, 
                model: str, 
                temperature: float = 0.0,
                max_iterations: int = 3,
                reflect: bool = True, 
                framework: str = "python"):
        self.max_iterations = max_iterations
        self.reflect = reflect
        self.framework = framework
        self.code_gen_chain = wu.code_gen_chain(model, temperature)
        self.graph = self.init_graph()
        self.graph = self.compile()
    def init_graph(self):
        workflow = StateGraph(State)
        ## Add Nodes
        workflow.add_node(
            "generate",
            lambda state: wu.generate(state, self.code_gen_chain, self.framework)
        ) 
        workflow.add_node("check_code",wu.code_check)  # check code
        workflow.add_node("reflect",
                        lambda state: wu.reflect(state, self.code_gen_chain, self.framework),
                        )  # reflect
        ## Add Edges
        workflow.add_edge(START, "generate")
        workflow.add_edge("generate", "check_code")
        workflow.add_conditional_edges(
            "check_code",
            lambda state: wu.decide_to_finish(state, self.max_iterations, self.reflect),
            {
                "end": END,
                "reflect": "reflect",
                "generate": "generate",
            }
        )
        workflow.add_edge("reflect", "generate")
        return workflow
    
    def compile(self):
        return self.graph.compile()

    def run(self, query: str):
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
    def change_parameters(self, model: str, temperature: float, max_iterations: int, reflect: bool, framework: str|None = None):
        self.code_gen_chain = wu.code_gen_chain(model, temperature)
        self.max_iterations = max_iterations
        self.reflect = reflect
        self.framework = framework if framework else "python"
        return f"Parameters updated! Model: {model}, Temperature: {temperature}, Max Iterations: {self.max_iterations}, Reflect: {self.reflect}, Framework: {self.framework}"
