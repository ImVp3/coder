from typing import Union
from langchain.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain.output_parsers import PydanticOutputParser

from utils.helpers import get_chat_model
from utils.schemas import Code, CodeAnalysis, TestCodeEvaluation
from . import prompts


def create_code_gen_chain(model: Union[str, BaseChatModel], temperature: float = 0.0) -> Runnable:
    """
    Creates a LangChain Runnable for code generation returning a structured Code object.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.CODE_GEN_TEMPLATE)
    return prompt | model.with_structured_output(Code)


def create_routing_chain(model: str|BaseChatModel, actions_descriptions: str) -> Runnable:
    """
    Creates a routing chain for choosing actions based on input messages.
    Action descriptions must follow format: ACTION_NAME: description.
    """
    model = get_chat_model(model)
    prompt = ChatPromptTemplate.from_template(prompts.ROUTER_TEMPLATE).partial(
        actions_descriptions=actions_descriptions
    )
    return prompt | model


def create_code_analysis_chain(model: str|BaseChatModel, temperature: float = 0.0) -> Runnable:
    """
    Creates a chain that analyzes code and returns a CodeAnalysis object.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.CODE_ANALYSIS_TEMPLATE)
    return prompt | model | PydanticOutputParser(pydantic_object=CodeAnalysis)


def create_test_generation_chain(model: str|BaseChatModel, temperature: float = 0.0) -> Runnable:
    """
    Creates a chain that generates unit test code from code analysis.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.TEST_GENERATION_TEMPLATE)
    return prompt | model


def create_evaluation_chain(model: str|BaseChatModel, temperature: float = 0.0) -> Runnable:
    """
    Creates a chain that evaluates generated tests and outputs a TestCodeEvaluation object.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.EVALUATION_TEMPLATE)
    return prompt | model | PydanticOutputParser(pydantic_object=TestCodeEvaluation)


def create_extract_code_chain(model: str|BaseChatModel, temperature: float = 0.0) -> Runnable:
    """
    Creates a chain that extracts code from messages.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.CODE_EXTRACTION_TEMPLATE)
    return prompt | model

def create_synthesis_chain(model: str|BaseChatModel, temperature: float = 0.0) -> Runnable:
    """
    Creates a chain that synthesizes the conversation into a final answer.
    """
    if isinstance(model, str):
        model = get_chat_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(prompts.SYNTHESIS_TEMPLATE)
    return prompt | model