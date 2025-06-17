from typing import List, Optional, Literal, Union, Any
from pydantic import BaseModel, Field

class Code(BaseModel):
    prefix: str = Field(..., description="The description of the code")
    imports: str = Field(..., description="The imports of the code")
    code: str = Field(..., description="The code of the code")

class Parameter(BaseModel):
    name: str 
    type: Optional[str] = None 

class MethodDetails(BaseModel):
    signature: Optional[str] = None 
    description: Optional[str] = None 
    parameters: List[Parameter] = Field(default_factory=list)
    returns: Optional[str] = None
    key_behaviors: List[str] = Field(default_factory=list) 
    edge_cases: List[str] = Field(default_factory=list)

class Method(MethodDetails):
    name: str 

class FunctionComponent(MethodDetails):
    type: Literal["function"] 
    name: str 

class ClassComponent(BaseModel):
    type: Literal["class"] 
    name: str 
    description: Optional[str] = None 
    methods: List[Method] = Field(default_factory=list) 

Component = Union[FunctionComponent, ClassComponent]

class CodeAnalysis(BaseModel):
    summary: Optional[str] = None 
    components: List[Component] = Field(default_factory=list, discriminator='type' if hasattr(Field, 'discriminator') else None) # Mặc định là danh sách rỗng
    dependencies: List[str] = Field(default_factory=list) 
    
class TestCodeEvaluation(BaseModel):
    qualitative_assessment: Literal["low", "medium", "high"]
    confidence_score: float 
    positive_feedback: List[str] = Field(default_factory=list) 
    areas_for_improvement: List[str] = Field(default_factory=list) 
    other_suggestions: List[str] = Field(default_factory=list)

class FlowStep(BaseModel):
    step: str
    agent: str 