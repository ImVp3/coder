from typing import Dict
from langgraph.graph import END, StateGraph, START
from langchain.schema.retriever import BaseRetriever
from .utils.state import UnitTestWorkflowState
from .utils import unittest_gen_nodes as nodes
from .utils.routing import decision_to_end_workflow, decision_to_extract
from .utils.helper import (
    create_code_analysis_chain, 
    create_test_generation_chain, 
    create_evaluation_chain, 
    create_extract_code_chain
)


from ..logger import GraphLogger
import time

GRAPH_NAME = "UnitTestWorkflow"
class UnitTestWorkflow:
    """A workflow class for generating unit tests using LangGraph.
    """ 
    def __init__(self, model: str = "gemini-2.0-flash", temperature: float = 0.0, max_attempts:int = 3):
        self.model = model
        self.temperature = temperature
        self.max_attempts = max_attempts
        self.code_analysis_chain = create_code_analysis_chain(model, temperature)
        self.test_generation_chain = create_test_generation_chain(model, temperature)
        self.evaluation_chain = create_evaluation_chain(model, temperature)
        self.extract_code_chain = create_extract_code_chain(model, temperature)
        self.logger = GraphLogger()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Creates the state graph for the unit test generation workflow."""
        graph = StateGraph(UnitTestWorkflowState)
        graph.add_node(
            "analyze_code_node",
            lambda state: self._wrap_node("analyze_code_node", nodes.code_analysis, state, self.code_analysis_chain)
        )    
        graph.add_node(
            "generate_test_node",
            lambda state: self._wrap_node("generate_test_node", nodes.generate_tests, state, self.test_generation_chain)
        )
        graph.add_node(
            "evaluate_test_node",
            lambda state: self._wrap_node("evaluate_test_node", nodes.evaluate_tests, state, self.evaluation_chain)
        )
        graph.add_node(
            "extract_code_node",
            lambda state: self._wrap_node("extract_code_node", nodes.extract_code, state, self.extract_code_chain)
        )
        graph.add_conditional_edges(
            START, 
            lambda state: self._wrap_decision(decision_to_extract,state),
            {
                "extract": "extract_code_node",
                "analyze": "analyze_code_node",
                "end": END
            }
        )
        graph.add_edge("extract_code_node", "analyze_code_node")
        graph.add_edge("analyze_code_node", "generate_test_node")
        graph.add_edge("generate_test_node", "evaluate_test_node")
        graph.add_conditional_edges(
            "evaluate_test_node",
            lambda state: self._wrap_decision(decision_to_end_workflow, state),
            {
                "end": END,
                "regenerate": "generate_test_node"
            }
        )
        return graph.compile(name = "UnitTest_Generator")
    
    def _wrap_node(self, node_name: str, node_func, *args):
        """Wrapper function to add logging to node execution"""
        self.logger.log_node_execution(GRAPH_NAME, node_name, {"args": str(args)})
        start_time = time.time()
        try:
            result = node_func(*args)
            duration = time.time() - start_time
            self.logger.log_node_completion(GRAPH_NAME, node_name, {"result": str(result)}, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(GRAPH_NAME, node_name, e)
            raise

    def _wrap_decision(self,decision_func, state: UnitTestWorkflowState):
        """Wrapper function to add logging to decision making"""
        decision = decision_func(state)
        self.logger.log_graph_state(GRAPH_NAME, f"Decision made: {decision}")
        return decision
    
    def invoke(self, code: str):
        self.logger.log_graph_start(GRAPH_NAME, {"original_code": code, "max_attempts": self.max_attempts})
        start_time = time.time()
        try:
            state = UnitTestWorkflowState(original_code=code, max_generation_attempts=self.max_attempts)
            result = self.graph.invoke(state)
            duration = time.time() - start_time
            self.logger.log_graph_end(GRAPH_NAME, "success", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(GRAPH_NAME, None, e)
            self.logger.log_graph_end(GRAPH_NAME, "failed", duration)
            raise

    def stream(self, code: str, stream_mode: str = "values"):
        self.logger.log_graph_start(GRAPH_NAME, {"original_code": code, "max_attempts": self.max_attempts})
        start_time = time.time()
        try:
            state = UnitTestWorkflowState(original_code=code, max_generation_attempts=self.max_attempts)
            result = self.graph.stream(state, stream_mode=stream_mode)
            duration = time.time() - start_time
            self.logger.log_graph_end(GRAPH_NAME, "success", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(GRAPH_NAME, None, e)
            self.logger.log_graph_end(GRAPH_NAME, "failed", duration)
            raise

    def astream(self, code: str, stream_mode: str = "values"):
        self.logger.log_graph_start(GRAPH_NAME, {"original_code": code, "max_attempts": self.max_attempts})
        start_time = time.time()
        try:
            state = UnitTestWorkflowState(original_code=code, max_generation_attempts=self.max_attempts)
            result = self.graph.astream(state, stream_mode=stream_mode)
            duration = time.time() - start_time
            self.logger.log_graph_end(GRAPH_NAME, "success", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(GRAPH_NAME, None, e)
            self.logger.log_graph_end(GRAPH_NAME, "failed", duration)
            raise
    def as_graph(self) -> StateGraph:
        """
        Returns the current state graph of the workflow.
        """
        return self.graph
    def change_parameters(self, model: str = None, temperature: float = None):
        """
        Change the parameters of the workflow.

        Args:
            model (str): The new model to use.
            temperature (float): The new temperature for the model.
        """
        if model:
            self.model = model
        if temperature is not None:
            self.temperature = temperature
        self.code_analysis_chain = create_code_analysis_chain(self.model, self.temperature)
        self.test_generation_chain = create_test_generation_chain(self.model, self.temperature)
        self.evaluation_chain = create_evaluation_chain(self.model, self.temperature)
        self.logger.log_graph_state(GRAPH_NAME, f"Parameters changed: model={self.model}, temperature={self.temperature}")
        self.graph = self._create_graph()
        self.logger.log_graph_state(GRAPH_NAME, f"Graph recompiled with new parameters.")
        return f"Parameters changed: model={self.model}, temperature={self.temperature}"
    def get_current_parameters(self) -> Dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_attempts": self.max_attempts
        }
