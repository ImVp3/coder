from pydantic import Field, BaseModel

class Code(BaseModel):
    prefix: str = Field(..., description="The description of the code")
    imports: str = Field(..., description="The imports of the code")
    code: str = Field(..., description="The code of the code")