from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from langchain.schema import Document
from typing_extensions import List, Annotated
from operator import add

class Code(BaseModel):
    prefix: str = Field(..., description="The description of the code")
    imports: str = Field(..., description="The imports of the code")
    code: str = Field(..., description="The code of the code")

class State(MessagesState):
    """
    Represents the state of the graph.
    Attributes:
        error: binary flag for control flow to indicate if an error occurred
        generation: generated code solution
        iteration: number of tries
    """
    error: bool = False
    generation: Annotated[List[Code], add]
    iterations: int
    documentation: List[Document]
    flow: Annotated[List[str], add]