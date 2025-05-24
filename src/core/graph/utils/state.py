from langchain.schema import Document
from langgraph.graph import MessagesState
from typing_extensions import TypedDict, List, Dict, Any, Optional, Annotated
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
    
class UnitTestWorkflowState(MessagesState):
    original_code: str
    analyzed_code: str
    test_code: str
    evaluation: dict
    flow: Annotated[List[str], operator.add]
    max_generation_attempts: int
    generation_attempts: int