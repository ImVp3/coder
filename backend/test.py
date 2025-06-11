from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from agents.supervisor_agent import build_supervisor_agent
from utils.helpers import get_chat_model, get_retriever, get_last_message_content, pretty_print_messages

supervisor_model = get_chat_model(model_name="gemini-2.0-flash")
worker_model = get_chat_model(model_name="gemini-2.0-flash")
retriever = get_retriever(persistent_path="A:/Code/coder/data")
supervisor_graph = build_supervisor_agent(
    supervisor_model=supervisor_model,
    worker_model=worker_model,
    retriever=retriever
)

input = "Write a function to calculate the factorial of a number. After that, write a unit test for the function."
output = supervisor_graph.invoke({
    "messages": [{"role": "user", "content": input}],
})
pretty_print_messages(output["messages"])
'''
Output:
{'messages': [HumanMessage(content='Write a function to calculate the factorial of a number', additional_kwargs={}, response_metadata={}, id='023427d7-95d8-4dde-82c9-8aad324e1016'), AIMessage(content='', additional_kwargs={'function_call': {'name': 'transfer_to_codegen_agent', 'arguments': '{}'}}, response_metadata={'prompt_feedback': {'block_reason': 0, 'safety_ratings': []}, 'finish_reason': 'STOP', 'safety_ratings': []}, name='supervisor', id='run--327d612a-531f-467c-ac54-52602eb42dd9-0', tool_calls=[{'name': 'transfer_to_codegen_agent', 'args': {}, 'id': 'bd9d0777-29a9-451f-9690-d6faf932f49e', 'type': 'tool_call'}], usage_metadata={'input_tokens': 122, 'output_tokens': 7, 'total_tokens': 129, 'input_token_details': {'cache_read': 0}}), ToolMessage(content='Successfully transferred to codegen_agent', name='transfer_to_codegen_agent', id='dabb579f-6851-47a6-80eb-94f830aab1e8', tool_call_id='bd9d0777-29a9-451f-9690-d6faf932f49e'), AIMessage(content='This code defines a recursive function to calculate the factorial of a number n. \nImports:\n\nCode:\ndef factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)', additional_kwargs={}, response_metadata={}, id='a44634af-4de8-4756-9559-a1a1c9625413'), AIMessage(content='', additional_kwargs={}, response_metadata={'prompt_feedback': {'block_reason': 0, 'safety_ratings': []}, 'finish_reason': 'STOP', 'safety_ratings': []}, name='supervisor', id='run--c263e485-ce7f-45e1-86ba-7363f1d85b76-0', usage_metadata={'input_tokens': 200, 'output_tokens': 0, 'total_tokens': 200, 'input_token_details': {'cache_read': 0}})]}
'''