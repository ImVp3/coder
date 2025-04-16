CODE_GEN_TEMPLATE = """ 
You are a coding assistant with expertise in {framework}. 
Here is a full set of {framework} documentation: 
{context}
---

Answer the user question based on the above provided documentation. 
Ensure any code you provide can be executed with all required imports and variables defined. 
Structure your answer with a description of the code solution. 
Then list the imports. And finally list the functioning code block. 
Here is the user question:
{question}
"""

REFLECT_TEMPLATE = """
Now, try again. 
Invoke the code tool to structure the output with a prefix, imports, and code block:
"""
