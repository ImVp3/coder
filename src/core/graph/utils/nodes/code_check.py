from typing_extensions import Dict, Any, List, Optional
import ast
from langchain.schema.messages import BaseMessage, SystemMessage, HumanMessage
from langchain.schema.document import Document

from core.utils.schema import Code
from core.graph.utils.state import State

NODE_NAME = "Code Check"
FLOW_PASSED = f"{NODE_NAME}: Passed"
FLOW_FAILED_SYNTAX = f"{NODE_NAME}: Failed (SyntaxError)"
FLOW_FAILED_UNEXPECTED = f"{NODE_NAME}: Failed (Unexpected Error)"
FLOW_NO_GENERATION = f"{NODE_NAME}: No Generation Found"
FLOW_INVALID_FORMAT = f"{NODE_NAME}: Invalid Generation Format"
FLOW_EMPTY_CODE = f"{NODE_NAME}: Empty Code/Imports"
MESSAGE_NO_GENERATION = f"{NODE_NAME}: No code generation found in state."
MESSAGE_INVALID_FORMAT = f"{NODE_NAME}: Latest generation is not a valid Code object."
MESSAGE_EMPTY_CODE = f"Static Check: No code or imports found in the latest generation."

def static_syntax_check_v2(state: State) -> State:
    """
    Performs a static syntax check on the latest generated code using `ast.parse`.

    This function extracts the latest code generation (expected to be a `Code` object
    or a dict that can be validated into one) from the state's 'generation' list.
    It handles cases where no generation exists, the generation is invalid, or
    the code/imports are empty.

    It attempts to parse the combined imports and code using Python's `ast` module.
    - If parsing succeeds, it sets the 'error' flag to False.
    - If a `SyntaxError` occurs, it sets 'error' to True and adds a detailed
        `HumanMessage` to the messages list, formatted to help an LLM correct the error.
    - If any other exception occurs during parsing, it sets 'error' to True and adds
        a `SystemMessage` indicating an unexpected check failure.

    Args:
        state: The current state dictionary, expected to contain keys like
            'messages' (List[BaseMessage]), 'generation' (List[Code] or List[Dict]),
            'iterations' (int), 'documentation' (List[Document]), and 'flow' (List[str]).

    Returns:
        A dictionary representing the updated state. It includes:
        - 'messages': The original messages plus any new error message generated.
        - 'generation': The original list of generations (passed through).
        - 'iterations': The original iteration count (passed through).
        - 'documentation': The original documentation list (passed through).
        - 'error': A boolean flag indicating if a syntax error was found (True) or not (False).
        - 'flow': The original flow list appended with the outcome of this check.
    """
    
    current_messages: List[BaseMessage] = state.get('messages', [])  
    generations: List[Code] = state.get('generation', [])
    iterations: int = state.get('iterations', 0)
    documentation: List[Document] = state.get('documentation', [])
    current_flow: List[str] = state.get('flow', [])
    #--- 1. Handle missing or invalid generation ---
    if not generations:
        error_message = SystemMessage(content=MESSAGE_NO_GENERATION)
        return {
            "messages": current_messages + [error_message],
            "generation": generations,
            "iterations": iterations,
            "documentation": documentation,
            "error": True,
            "flow": current_flow + [FLOW_NO_GENERATION],
        }

    #Get the latest code generation and validate it
    try:
        latest_code_solution = Code.model_validate(generations[-1]) 
    except Exception:
        if isinstance(generations[-1], Code):
            latest_code_solution = generations[-1]
        else:
            error_message = SystemMessage(
                content= MESSAGE_INVALID_FORMAT)
            return {
                "messages": current_messages + [error_message],
                "generation": generations,
                "iterations": iterations,
                "documentation": documentation,
                "error": True,
                "flow": current_flow + [FLOW_INVALID_FORMAT],
            }
    # --- 2. Handle emty code/imports
    imports = latest_code_solution.imports
    code = latest_code_solution.code
    if not code and not imports:
        error_message = SystemMessage(
            content= MESSAGE_EMPTY_CODE)
        return {
            "messages": current_messages + [error_message],
            "generation": generations,
            "iterations": iterations,
            "documentation": documentation,
            "error": True,
            "flow": current_flow + [FLOW_EMPTY_CODE],
        }
    # --- 3. Perform Static syntax check ---
    full_code = f"{imports}\n{code}"

    error_flag = False
    error_message_obj: Optional[BaseMessage] = None
    flow_message = ""

    try:
        ast.parse(full_code)
        flow_message = "Static Syntax Check: Passed"
        error_flag = False
    except SyntaxError as e:
        flow_message = "Static Syntax Check: Failed"
        error_flag = True
        # Format syntax error details for the LLM
        code_line = e.text.strip() if e.text else "Unavailable"
        error_content = (
            f"Your solution has a syntax error (static check):\n"
            f"Line: {e.lineno}\n"
            f"Offset: {e.offset}\n"
            f"Error: {e.msg}\n"
            f"Code Snippet:\n```python\n{code_line}\n```"
        )
        error_message_obj = HumanMessage(content=error_content) # Use HumanMessage so the LLM treats this as feedback to act upon
    except Exception as e:
        flow_message = FLOW_FAILED_UNEXPECTED
        error_flag = True
        error_message_obj = SystemMessage(content=f"An unexpected error occurred during static syntax check: {type(e).__name__} - {e}")

    # --- 5. Prepare and return updated state ---
    updated_messages = list(current_messages) 
    if error_message_obj:
        updated_messages.append(error_message_obj)
    return {
        "messages": updated_messages,
        "generation": generations,  # Pass through original generations
        "iterations": iterations,  # Pass through original iterations
        "documentation": documentation, # Pass through original documentation
        "error": error_flag, # Set error status based on check
        "flow": current_flow + [flow_message], # Append check result to flow
    }