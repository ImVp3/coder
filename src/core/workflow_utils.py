from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from . import prompt_template as prt
from .schema import Code, State
from .utils import get_model

code_gen_prompt = ChatPromptTemplate.from_template(prt.CODE_GEN_TEMPLATE)

def code_gen_chain (model: str, temperature: float = 0.0) -> LLMChain:
    model = get_model(model, temperature)
    chain = code_gen_prompt | model.with_structured_output(Code)
    return chain

def generate(state: State, code_gen_chain: LLMChain, framework: str):
    messages = state["messages"]
    iterations = state["iterations"]
    
    if state["error"] == True:
        messages += [
            (
                "user",
                "Now, try again. Invoke the code tool to structure the output with a prefix, imports, and code block:",
            )
        ]
    code_solution = code_gen_chain.invoke(
        {"context": "\n".join(state["documentation"]), "question": messages, "framework": framework}
    )
    messages += [
        (
            "assistant",
            f"{code_solution.prefix} \n Imports: {code_solution.imports} \n Code: {code_solution.code}",
        )
    ]
    iterations = iterations + 1
    return {"generation": [code_solution], "messages": messages, "iterations": iterations, "flow": ["Generate"]}

def code_check(state: State):
    messages = state["messages"]
    code_solution = state["generation"][-1]
    iterations = state["iterations"]

    imports = code_solution.imports
    code = code_solution.code

    # Check imports
    try:
        if imports:
            exec(imports)
    except ImportError as e:
        flow ="Import Check: Failed"
        error_message = [("user", f"Your solution failed the import test: {e}")]
        return {
            "messages": error_message,
            "iterations": iterations,
            "error": True,
            "flow": [flow]
        }
    try:
        exec(imports + "\n" + code)
    except Exception as e:
        flow ="Code Block Check: Failed"
        error_message = [("user", f"Your solution failed the code execution test: {e}")]
        return {
            "messages": error_message,
            "iterations": iterations,
            "error": True,
        }
    flow = "Code Check: Passed"
    return {
        "messages": messages,
        "iterations": iterations,
        "error": False,
        "flow": [flow]
    }

def reflect(state: State, code_gen_chain: LLMChain, framework: str):
    messages = state["messages"]
    iterations = state["iterations"]
    code_solution = state["generation"][-1]

    reflections = code_gen_chain.invoke(
        {"context": "\n".join(state["documentation"]), "question": messages, "framework": framework}
    )
    messages = [("assistant", f"Here are reflections on the error: {reflections}")]
    return { "messages": messages, "iterations": iterations, "flow": ["Reflect"]}

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