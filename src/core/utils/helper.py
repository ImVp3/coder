from .schema import Code

def parse_code_generation (code_generation: Code):
    code = code_generation.code
    imports = code_generation.imports
    prefix = code_generation.prefix
    res = f"{prefix}\n```python\n{imports}\n{code}\n```"
    return res  