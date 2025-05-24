from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from core.utils.schema import Code, CodeAnalysis, TestCodeEvaluation
from . import prompt_template as template
from langchain.chains import LLMChain
from langchain_core.output_parsers.json import JsonOutputParser
def get_model(model: str, temperature: float = 0.0) -> ChatGoogleGenerativeAI | ChatOpenAI:
    if "gemini" in model:
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature
        )
    if "gpt" in model:
        return ChatOpenAI(
            model=model,
            temperature=temperature
        )
    raise ValueError(f"Model {model} not supported")

def create_code_gen_chain(model: str, temperature: float = 0.0) -> LLMChain:
    model = get_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(template.CODE_GEN_TEMPLATE)
    chain = prompt | model.with_structured_output(Code)
    return chain

def create_routing_chain (model: str, actions_descriptions: str):
    """
    Creates a LangChain runnable sequence (chain) for routing user queries.
    Args:
        model (str): The name of language model for classify action paths.
        action_descriptions: Action Descriptions should have the format Action name: short description. 
            For example GENERATION: suitable for generating complex code. 
            Action name should contain only 1 word.
    """
    model = get_model(model)
    prompt = ChatPromptTemplate.from_template(template.ROUTER_TEMPLATE)
    prompt =prompt.partial(actions_descriptions=actions_descriptions)
    chain = prompt | model
    return chain


def create_code_analysis_chain(model: str,temperature: float = 0.0,) -> LLMChain:
    llm = get_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(template.CODE_ANALYSIS_TEMPLATE)
    chain = prompt | llm |JsonOutputParser(pydantic_object=CodeAnalysis)
    return chain
def create_test_generation_chain(model: str,temperature: float = 0.0,) -> LLMChain:
    llm = get_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(template.TEST_GENERATION_TEMPLATE)
    chain = prompt | llm
    return chain
def create_evaluation_chain(model: str,temperature: float = 0.0,) -> LLMChain:
    llm = get_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(template.EVALUATION_TEMPLATE)
    chain = prompt | llm | JsonOutputParser(pydantic_object=TestCodeEvaluation)
    return chain