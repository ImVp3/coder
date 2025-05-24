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
    
class UnitTestWorkflowState(TypedDict):
    original_code: str             
    code_analysis: Optional[Dict[str, Any]] 
    flow : Annotated[List[str], operator.add]
    generated_test_code: Optional[str] 
    current_coverage: Optional[float]   
    coverage_achieved: bool             
    generation_attempts: int          
    max_generation_attempts: int       

    error_message: Optional[str]       
    final_summary: Optional[str]        