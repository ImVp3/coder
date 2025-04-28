from core.graph.utils.state import State
from langchain.chains import LLMChain
from langchain.schema.messages import HumanMessage, AIMessage

GENERATION_RETRY = "Now, try again. Invoke the code tool to structure the output with a prefix, imports, and code block:"
STEP_NAME = "Generate"
def generate(state: State, code_gen_chain: LLMChain, framework: str):
    """
    Generates code based on the current state, documentation, and framework using an LLMChain.

    If the previous step resulted in an error, it adds a retry prompt to the messages.
    It processes documentation, invokes the code generation chain, updates the message history,
    increments the iteration count, and returns the updated state components.

    Args:
        state: The current graph state, containing messages, iterations, documentation, and error status.
        code_gen_chain: The LLMChain responsible for generating structured code output (Code object).
        framework: The target coding framework (e.g., 'python', 'react').

    Returns:
        A dictionary containing updates for the graph state:
        - 'generation': A list containing the newly generated Code object.
        - 'messages': The updated list of messages.
        - 'iterations': The incremented iteration count.
        - 'flow': A list containing the name of this node ("Generate").
    """
    messages = state["messages"]
    iterations = state["iterations"]
    documents = "\n".join([doc.page_content for doc in state.get('documentation', []) if hasattr(doc, 'page_content')])
    if state["error"] == True:
        messages += [HumanMessage(content= GENERATION_RETRY)]
    code_solution = code_gen_chain.invoke(
        {"context": documents , "question": messages, "framework": framework}
    )
    messages += [AIMessage(content =f"{code_solution.prefix} \n Imports: {code_solution.imports} \n Code: {code_solution.code}")]
    iterations += 1
    return { 
            "generation": [code_solution], 
            "messages": messages, 
            "iterations": iterations, 
            "flow": [STEP_NAME]
            }
