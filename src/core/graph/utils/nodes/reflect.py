from langchain.chains.llm import LLMChain
from langchain.schema.messages import AIMessage
from core.utils.schema import Code
from core.graph.utils.state import State
from typing_extensions import List
from langchain.schema.messages import BaseMessage

STEP_NAME = "Reflect"
def reflect(state: State, code_gen_chain: LLMChain, framework: str) -> dict:
    """
    Performs a reflection step upon encountering an error during code generation.

    This node is typically triggered after a failed `code_check`. It invokes
    the provided `code_gen_chain` with the current message history (which should
    include the error message from the check) and context.

    It assumes the `code_gen_chain`, when prompted with the error context,
    will provide reflective text or analysis within the `prefix` field of its
    structured `Code` output.

    This reflection text is then appended to the message history as a new
    `AIMessage`, preserving the conversation context for the subsequent
    generation attempt. The iteration count remains unchanged.

    Args:
        state: The current graph state, containing messages, iterations,
            documentation, and previous generations.
        code_gen_chain: The LLMChain instance configured to generate
                        structured `Code` output. It's reused here for reflection.
        framework: The target coding framework (e.g., 'python').

    Returns:
        A dictionary containing updates for the graph state:
        - 'messages': The original messages list appended with the new
                    reflection AIMessage.
        - 'flow': A list containing the name of this node ("Reflect").
    """
    messages: List[BaseMessage] = state['messages']
    documentation_list: List[str] = [doc.page_content for doc in state.get('documentation', []) if hasattr(doc, 'page_content')]
    documentation: str = "\n".join(documentation_list)

    reflection_code: Code = code_gen_chain.invoke(
        {"context": documentation, "question": messages, "framework": framework}
    )
    reflection_message = AIMessage(
        content=f"Reflection on the error: {reflection_code.prefix}"
    )
    return {
        "messages": reflection_message, 
        "flow": [STEP_NAME]
        }
