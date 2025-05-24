import json
from typing import  Dict, Any, List, Optional
from ..state import UnitTestWorkflowState
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage

EVALUATE_LLM_NODE_NAME = "Evaluate Tests Quality (LLM)"
# EVALUATE_LLM_FLOW_ASSESSMENT_MET = f"{EVALUATE_LLM_NODE_NAME}: Test quality assessment target met"
# EVALUATE_LLM_FLOW_ASSESSMENT_NOT_MET = f"{EVALUATE_LLM_NODE_NAME}: Test quality assessment target NOT met"
EVALUATE_LLM_FLOW_ASSESSMENT_GENERATED = f"{EVALUATE_LLM_NODE_NAME}: Test quality assessment generated with qualitative_assessment"
EVALUATE_LLM_FLOW_MAX_ATTEMPTS_REACHED = f"{EVALUATE_LLM_NODE_NAME}: Max attempts reached, assessment target NOT met" 
EVALUATE_LLM_FLOW_FAILED_NO_TESTS = f"{EVALUATE_LLM_NODE_NAME}: Failed (No generated tests to evaluate)"
EVALUATE_LLM_FLOW_FAILED_NO_CODE = f"{EVALUATE_LLM_NODE_NAME}: Failed (No original code to evaluate against)"
EVALUATE_LLM_FLOW_FAILED_NO_ANALYSIS = f"{EVALUATE_LLM_NODE_NAME}: Failed (No code analysis provided for evaluation)"
EVALUATE_LLM_FLOW_FAILED_LLM_EVAL = f"{EVALUATE_LLM_NODE_NAME}: Failed (LLM evaluation error)"
EVALUATE_LLM_FLOW_FAILED_UNEXPECTED = f"{EVALUATE_LLM_NODE_NAME}: Failed (Unexpected Error)"

MESSAGE_NO_GENERATED_TESTS = "No generated test code found in state. Cannot evaluate." # Cập nhật message
MESSAGE_NO_ORIGINAL_CODE_FOR_EVALUATION = "No original code found in state. Cannot evaluate." # Cập nhật message
MESSAGE_NO_CODE_ANALYSIS_FOR_EVALUATION = "Code analysis is missing, which is crucial for LLM-based test evaluation."
MESSAGE_LLM_EVALUATION_ERROR = "An error occurred during LLM-based test evaluation."

def evaluate_tests(state: UnitTestWorkflowState, eval_chain) -> Dict[str, Any]:
    """
    Evaluates the generated test code using an LLM to assess its quality,
    completeness, and likely coverage against the original code and its analysis.
    """
    messages: List[BaseMessage] = state.get('messages', [])
    test_code: Optional[str] = state.get('test_code')
    original_code: Optional[str] = state.get('original_code')
    analyzed_code: Optional[Dict[str, Any]] = state.get('analyzed_code')
    generation_attempts: int = state.get('generation_attempts')
    max_generation_attempts: int = state.get('max_generation_attempts', 3)
    current_flow: List[str] = state.get('flow', [])
    
    if not original_code:
        return {
            "messages": [SystemMessage(content=MESSAGE_NO_ORIGINAL_CODE_FOR_EVALUATION)],
            "flow": [EVALUATE_LLM_FLOW_FAILED_NO_CODE],
        }
    if not test_code:
        if generation_attempts>= max_generation_attempts:
            error_msg = f"{error_msg} Max attempts ({max_generation_attempts}) reached."
        else:
            error_msg = MESSAGE_NO_GENERATED_TESTS
        return {
            "messages": [SystemMessage(content=error_msg)],
            "flow": [EVALUATE_LLM_FLOW_FAILED_NO_TESTS],
        }
    if not analyzed_code:
        return {
            "messages": [SystemMessage(content=MESSAGE_NO_CODE_ANALYSIS_FOR_EVALUATION)],
            "flow": [EVALUATE_LLM_FLOW_FAILED_NO_ANALYSIS],
        }
    try: 
        code_analysis_str = json.dumps(analyzed_code, indent=2)
    except TypeError as e:
        error_msg = f"Could not serialize analyzed_code to JSON: {e}"
        return {
            "messages": [SystemMessage(content=error_msg)],
            "flow": [EVALUATE_LLM_FLOW_FAILED_UNEXPECTED],
        }
        
    llm_eval_result = eval_chain.invoke(
        {
        "original_code": original_code,
        "code_analysis_json": str(analyzed_code),
        "test_code": test_code
        }
    )
    if not llm_eval_result or not isinstance(llm_eval_result, dict):
        error_msg = "LLM evaluation returned no data or invalid format."
        return {
            "messages": [SystemMessage(content=error_msg)],
            "flow": [EVALUATE_LLM_FLOW_FAILED_LLM_EVAL],
        }

    return {
        "messages": [AIMessage(content=json.dumps(llm_eval_result))],
        "evaluation": llm_eval_result,
        "flow": [f"{EVALUATE_LLM_FLOW_ASSESSMENT_GENERATED} [{llm_eval_result.get('qualitative_assessment')}]" ],
    }
    