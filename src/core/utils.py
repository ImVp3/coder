from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .prompt_template import * 
from .schema import * 
from langchain.chains import LLMChain
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

def get_code_gen_chain(model: str, temperature: float = 0.0) -> LLMChain:
    model = get_model(model, temperature)
    prompt = ChatPromptTemplate.from_template(CODE_GEN_TEMPLATE)
    chain = prompt | model.with_structured_output(Code)
    return chain
