# unified_unittest_workflow.py

import json
import ast
from typing import Dict, Any, Optional, List

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langchain_core.language_models import BaseChatModel
from langgraph.types import Command
from .states import TestGenState
from utils.schemas import TestCodeEvaluation, FlowStep
from .chains import (
    create_code_analysis_chain, 
    create_test_generation_chain, 
    create_evaluation_chain, 
    create_extract_code_chain
)

AGENT_NAME = "testgen_agent"

# ---------- Node Functions ----------
def extract_code_node(state: TestGenState, chain) -> Dict[str, Any] | Command:
    query = state.get("messages")
    if query:
        original_code = chain.invoke({"message": query}).content
        if original_code != "NONE":
            return {"original_code": original_code, "flow": [ FlowStep(agent=AGENT_NAME, step = "extract_code:success")]}
    return Command(update={
        "messages": [AIMessage(content="No code extracted from the messages.")],
        "flow": [FlowStep(agent=AGENT_NAME, step = "extract_code:failed")]
    }, goto=END)

def code_analysis_node(state: TestGenState, chain) -> Dict[str, Any]:
    original_code = state.get("original_code")
    if not original_code:
        return {"messages": [SystemMessage(content="No original code")], "flow": [FlowStep(agent=AGENT_NAME, step ="code_analysis:failed:no_code")]}
    analyzed = chain.invoke({"code_to_analyze": original_code})
    if not analyzed:
        return {"messages": [SystemMessage(content="LLM analysis error")], "flow": [FlowStep(agent=AGENT_NAME, step ="code_analysis:failed:llm")]}
    return {"analyzed_code": analyzed, "messages": [AIMessage(content=analyzed.model_dump_json(indent=2))], "flow": [FlowStep(agent=AGENT_NAME, step ="code_analysis:success")]}

def generate_tests_node(state: TestGenState, chain) -> Dict[str, Any]:
    analyzed_code = state.get("analyzed_code")
    original_code = state.get("original_code")
    attempts = state.get("generation_attempts", 0)
    if not analyzed_code:
        return {"messages": [SystemMessage(content="No code analysis found")], "flow": [ FlowStep(agent=AGENT_NAME, step = "generate_tests:failed:no_analysis")], "generation_attempts": attempts + 1}

    components = analyzed_code.components
    if not components or not isinstance(components, list):
        return {"messages": [SystemMessage(content="Invalid analysis format")], "flow": [ FlowStep(agent=AGENT_NAME, step = "generate_tests:failed:invalid_format")],"generation_attempts": attempts + 1}

    feedback = ""
    if state.get("test_code") and state.get("evaluation"):
        feedback = f"Previous test:\n{state['test_code']}\n\nEval:\n{state['evaluation'].model_dump_json(indent=2)}"

    test_codes = []
    for component in components:
        try:
            response = chain.invoke({
                "original_code_snippet": original_code,
                "component_name": component.name,
                "component_type": component.type,
                "component_signature": component.signature,
                "component_description": component.description,
                "key_behaviors": component.key_behaviors,
                "edge_cases": component.edge_cases,
                "feedback": feedback
            })
            test_codes.append(response.content)
        except Exception as e:
            return {"messages": [SystemMessage(content=f"Error generating test: {e}")], "flow": [ FlowStep(agent=AGENT_NAME, step = "generate_tests:failed:llm")],"generation_attempts": attempts + 1}

    if not test_codes:
        return {"messages": [SystemMessage(content="No test generated")], "flow": [ FlowStep(agent=AGENT_NAME, step = "generate_tests:failed:empty")]}

    combined = "\n\n".join(test_codes) + "\n\n# Add if __name__ == '__main__': unittest.main() if needed"
    return {
        "messages": [AIMessage(content=combined)],
        "test_code": combined,
        "flow": [ FlowStep(agent=AGENT_NAME, step = "generate_tests:success")],
        "generation_attempts": attempts + 1,
    }

def evaluate_tests_node(state: TestGenState, chain) -> Dict[str, Any]:
    test_code = state.get("test_code")
    original_code = state.get("original_code")
    analyzed_code = state.get("analyzed_code")

    if not original_code:
        return {"messages": [SystemMessage(content="No original code")], "flow": [ FlowStep(agent=AGENT_NAME, step = "evaluate_tests:failed:no_code")]}
    if not test_code:
        return {"messages": [SystemMessage(content="No test code")], "flow": [ FlowStep(agent=AGENT_NAME, step = "evaluate_tests:failed:no_tests")]}
    if not analyzed_code:
        return {"messages": [SystemMessage(content="Missing analysis")], "flow": [ FlowStep(agent=AGENT_NAME, step = "evaluate_tests:failed:no_analysis")]}

    try:
        result = chain.invoke({
            "original_code": original_code,
            "code_analysis_json": analyzed_code.model_dump_json(indent=2),
            "test_code": test_code
        })
    except Exception as e:
        return {"messages": [SystemMessage(content=f"Eval error: {e}")], "flow": [ FlowStep(agent=AGENT_NAME, step = "evaluate_tests:failed:exception")]}

    if not isinstance(result, TestCodeEvaluation):
        return {"messages": [SystemMessage(content="Invalid result format")], "flow": [ FlowStep(agent=AGENT_NAME, step = "evaluate_tests:failed:bad_output")]}

    new_state = {
        "messages": [AIMessage(content= result.model_dump_json(indent=2))],
        "evaluation": result,
        "flow": [FlowStep(agent=AGENT_NAME, step =f"evaluate_tests:success:{result.qualitative_assessment}")]
    }
    if state["generation_attempts"] >= state.get("max_generation_attempts",3) or result.qualitative_assessment == "high":
        return Command(
            goto = END,
            update = {
                "messages": [AIMessage(content= result.model_dump_json(indent=2)), AIMessage(content=f"# The qualitative accessment of UnitTest: {result.qualitative_assessment}\n\n {test_code}")],
                "evaluation": result,
                "flow": [
                    FlowStep(agent=AGENT_NAME, step = f"evaluate_tests:success:{result.qualitative_assessment}"),
                    FlowStep(agent=AGENT_NAME, step =f"End Test Flow after {state.get("generation_attempts")} tries")]
            }
        )
    return Command(
        goto="generate_tests",
        update = {
            "messages": [AIMessage(content= result.model_dump_json(indent=2))],
            "evaluation": result,
            "flow": [FlowStep(agent=AGENT_NAME, step =f"evaluate_tests:success:{result.qualitative_assessment}")]
        }
    )
# ---------- Decision Functions ----------
def decision_to_extract(state) -> str:
    if "messages" not in state and "original_code" not in state:
        return "end"
    if "original_code" not in state or not state["original_code"]:
        return "extract"
    return "analyze"
# ---------- Graph Build Function ----------
def build_testgen_graph(model: BaseChatModel| str = "gemini-2.0-flash", temperature: float = 0.0, max_attempts: int = 3):
    code_analysis_chain = create_code_analysis_chain(model, temperature)
    test_generation_chain = create_test_generation_chain(model, temperature)
    evaluation_chain = create_evaluation_chain(model, temperature)
    extract_code_chain = create_extract_code_chain(model, temperature)

    g = StateGraph(TestGenState)
    g.add_node("extract_code", lambda s: extract_code_node(s, extract_code_chain))
    g.add_node("code_analysis", lambda s: code_analysis_node(s, code_analysis_chain))
    g.add_node("generate_tests", lambda s: generate_tests_node(s, test_generation_chain))
    g.add_node("evaluate_tests", lambda s: evaluate_tests_node(s, evaluation_chain))

    g.add_conditional_edges(START, decision_to_extract, {
        "extract": "extract_code",
        "analyze": "code_analysis",
        "end": END
    })
    g.add_edge("extract_code", "code_analysis")
    g.add_edge("code_analysis", "generate_tests")
    g.add_edge("generate_tests", "evaluate_tests")
    return g.compile(name="testgen_agent")
