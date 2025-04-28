from .state import State

def decide_to_finish(state: State, max_iterations: int, reflect: bool):
    error = state["error"]
    iterations = state["iterations"]

    if error == False or iterations == max_iterations:
        return "end"
    else:
        if reflect == True:
            return "reflect"
        else:
            return "generate"