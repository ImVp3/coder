from langchain.schema import Document
from langgraph.graph import MessagesState
from typing_extensions import List, Annotated
import operator
from core.utils.schema import Code

class CodeGenState(MessagesState):
    """ 
    Represents the state of the code generation graph.
    Attributes:
        error: binary flag for control flow to indicate if an error occurred
        generation: generated code solution
        iteration: number of tries
    """
    error: bool = False
    generation: Annotated[List[Code], operator.add]
    iterations: int
    documentation: List[Document]
    flow: Annotated[List[str], operator.add]