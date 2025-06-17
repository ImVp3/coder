from langchain.schema import Document
from langgraph.graph import MessagesState
from typing_extensions import TypedDict, List, Dict, Any, Optional, Annotated
import operator
from utils.schemas import Code, CodeAnalysis, TestCodeEvaluation, FlowStep

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
    flow: Annotated[List[FlowStep], operator.add]
    
class TestGenState(MessagesState):
    original_code: str
    analyzed_code: CodeAnalysis
    test_code: str
    evaluation: TestCodeEvaluation
    flow: Annotated[List[FlowStep], operator.add]
    max_generation_attempts: int
    generation_attempts: int
    
class SupervisorState(MessagesState):
    flow: Annotated[List[FlowStep], operator.add]
