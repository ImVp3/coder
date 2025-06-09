from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, AIMessage
import json
from langgraph.types import Command
from langgraph.graph import END
from ..state import UnitTestWorkflowState

NODE_NAME = "Extract Code Node"
EXTRACT_FLOW_SUCCESS = f"{NODE_NAME}: Code extraction successful"
EXTRACT_FLOW_FAILED_NO_CODE = f"{NODE_NAME}: Failed (No code extracted from the query)"
def extract_code(state: UnitTestWorkflowState, code_extractor_chain ) -> Dict[str, Any]:
    """
    Extracts code snippets from the state for further processing.
    """
    query = state.get("messages")

    if query: 
        original_code = code_extractor_chain.invoke({"message": query}).content
        if original_code != "NONE":
            return {
                "original_code": original_code,
                "flow": [EXTRACT_FLOW_SUCCESS],
            }
    return Command(
        update= {
            "messages": [AIMessage(content="No code extracted from the messages. Make sure that your messages contain code snippets or relevant information.")],
            "flow": [EXTRACT_FLOW_FAILED_NO_CODE],
        },
        goto= END
    )