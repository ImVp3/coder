from typing import TypedDict, Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage , AIMessage
from ..state import UnitTestWorkflowState

# --- Constants ---
ANALYZE_NODE_NAME = "Analyze Code Node"
ANALYZE_FLOW_SUCCESS = f"{ANALYZE_NODE_NAME}: Analysis successful"

ANALYZE_FLOW_FAILED_NO_CODE = f"{ANALYZE_NODE_NAME}: Failed (No original code provided)"
ANALYZE_FLOW_FAILED_LLM = f"{ANALYZE_NODE_NAME}: Failed (LLM analysis error)"

MESSAGE_NO_ORIGINAL_CODE = "No original code found in state for analysis."
MESSAGE_FLOW_FAILED_LLM = "The original code provided has a syntax error, which prevents analysis."

def code_analysis(state: UnitTestWorkflowState, code_analysis_chain) -> UnitTestWorkflowState:
    """
    Analyze the code and provide a structured summary for generating unit tests.
    """
    original_code = state.get("original_code",None)
    if not original_code:
        return {
        "messages": [MESSAGE_NO_ORIGINAL_CODE],
        "flow": [ANALYZE_FLOW_FAILED_NO_CODE]
        }
    analyzed_code = code_analysis_chain.invoke({
        "code_to_analyze": original_code
    })
    if not analyzed_code:
        return {
        "messages": [MESSAGE_FLOW_FAILED_LLM],
        "flow": [ANALYZE_FLOW_FAILED_LLM]
        }
    return {
    "analyzed_code": analyzed_code,
    "messages": [AIMessage(content=str(analyzed_code))],
    "flow": [ANALYZE_FLOW_SUCCESS]
    }