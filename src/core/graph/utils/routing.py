from .state import CodeGenState
from .helper import create_routing_chain
from typing_extensions import Literal

def decide_to_finish(state: CodeGenState, max_iterations: int, reflect: bool):
    error = state["error"]
    iterations = state["iterations"]

    if error == False or iterations == max_iterations:
        print("->".join(state["flow"]))
        return "end"
    else:
        if reflect == True:
            return "reflect"
        else:
            return "generate"

def decide_to_route (state, model:str) -> Literal["COMPLEX_GENERATION", "GENERATION", "DEFAULT"]: 
    query = state["messages"][-1].content
    action_descriptions = """
    GENERATION: suitable for generating complex code with latest importing.
    DEFAULT: suitable for casual questions.
    """
    routing_chain =create_routing_chain(model=model, actions_descriptions=action_descriptions)
    return routing_chain.invoke({"question": query}).content
    