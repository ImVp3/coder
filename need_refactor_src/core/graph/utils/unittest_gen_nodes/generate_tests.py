from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, AIMessage
import json
from ..state import UnitTestWorkflowState

# --- Constants cho generate_tests_node ---
GENERATE_NODE_NAME = "Generate Tests Node"
GENERATE_FLOW_SUCCESS = f"{GENERATE_NODE_NAME}: Test generation successful"
GENERATE_FLOW_FAILED_NO_ANALYSIS = f"{GENERATE_NODE_NAME}: Failed (No code analysis found)"
GENERATE_FLOW_FAILED_INVALID_ANALYSIS = f"{GENERATE_NODE_NAME}: Failed (Invalid code analysis format)"
GENERATE_FLOW_FAILED_LLM = f"{GENERATE_NODE_NAME}: Failed (LLM test generation error)"
GENERATE_FLOW_FAILED_SYNTAX_IN_TESTS = f"{GENERATE_NODE_NAME}: Failed (Generated tests have syntax errors)"
GENERATE_FLOW_FAILED_UNEXPECTED = f"{GENERATE_NODE_NAME}: Failed (Unexpected Error)"

MESSAGE_NO_CODE_ANALYSIS = "No code analysis found in state. Cannot generate tests."
MESSAGE_INVALID_ANALYSIS_FORMAT = "Code analysis data is missing 'components' or has an invalid format."
MESSAGE_SYNTAX_ERROR_IN_GENERATED_TESTS = "The LLM-generated test code has a syntax error."



def generate_tests(state: UnitTestWorkflowState, test_generation_chain ) -> Dict[str, Any]:
    """
    Generates unit test code based on the code analysis provided.
    Uses an LLM to write test cases for identified components.
    """
    analyzed_code: Optional[Dict[str, Any]] = state.get('analyzed_code')
    original_code: Optional[str] = state.get('original_code') 
    generation_attempts: int = state.get('generation_attempts', 0)    
    
    if not analyzed_code:
        error_system_message = SystemMessage(content=MESSAGE_NO_CODE_ANALYSIS)
        return {
            "messages": [error_system_message],
            "flow": [GENERATE_FLOW_FAILED_NO_ANALYSIS],
        }

    components_to_test = analyzed_code.get("components")
    if not components_to_test or not isinstance(components_to_test, list):
        error_system_message = SystemMessage(content=MESSAGE_INVALID_ANALYSIS_FORMAT)
        return {
            "messages":  [error_system_message],
            "flow":  [GENERATE_FLOW_FAILED_INVALID_ANALYSIS],
        }
    last_test_code = state.get("test_code", "")
    last_evaluation = json.dumps(state.get("evaluation"))
    if last_test_code and last_evaluation:
        feedback_msg = f"Previous generated test code:\n{last_test_code}\n\nPrevious evaluation for the test code:\n{last_evaluation}"
    else:
        feedback_msg = ""          
    
    test_codes = []

    for component in components_to_test:
        try:
            test_code = test_generation_chain.invoke({
                "original_code_snippet": original_code,
                "component_name": component["name"],
                "component_type": component["type"],
                "component_signature": component.get("signature", ""),
                "component_description": component.get("description", ""),
                "key_behaviors": component.get("key_behaviors", []),
                "edge_cases": component.get("edge_cases", []),
                "feedback": feedback_msg
            })
            test_codes.append(test_code.content)
        except Exception as e:
            error_system_message = SystemMessage(
                content=f"Error generating tests for component {component['name']}: {type(e).__name__} - {e}"
                )
            return {
                "messages": [error_system_message],
                "flow": [GENERATE_FLOW_FAILED_LLM],
            }

    if not test_codes:
        # This case means no components to test, or LLM failed for all without throwing an exception caught above
        no_tests_msg = "No test classes were generated. Check code analysis or LLM responses."
        error_system_message = SystemMessage(content=no_tests_msg)
        return {
            "messages": [error_system_message],
            "flow": [GENERATE_FLOW_FAILED_LLM], 
        }

    # Combine all generated test classes and necessary imports
    all_generated_tests_str =  "\n\n".join(test_codes)
    all_generated_tests_str += "\n\n# You might want to add a way to run these tests if needed for standalone execution\n"
    all_generated_tests_str += "# e.g., if __name__ == '__main__': unittest.main()\n"
    # NOTE: But for programmatic use (like coverage.py), this main block is often not needed or added later.
    return {
        "messages": [AIMessage(content=all_generated_tests_str)],
        "test_code": [all_generated_tests_str],
        "flow": [GENERATE_FLOW_SUCCESS],
        "generation_attempts": generation_attempts + 1,
    }
    