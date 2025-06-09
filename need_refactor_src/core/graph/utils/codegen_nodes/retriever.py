import logging
from typing import Dict, Any, List
from functools import partial
from langchain.schema.document import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

from ..state import CodeGenState

EMPTY_DOCUMENT_CONTENT = "No specific documentation provided."
FLOW_NAME = "Retrieve"
empty_document = Document(page_content= EMPTY_DOCUMENT_CONTENT)
def retrieve_docs(state: CodeGenState, retriever: BaseRetriever) -> CodeGenState:
    """
    Retrieves documents relevant to the user's query using the provided retriever
    and updates the state.
    Args:
        state: The current graph state. Expected to contain the user query
                under the 1st message content.
        retriever: The LangChain retriever instance (e.g., from a vector store)
                    configured for searching.
    Returns:
        A dictionary to update the state, containing the key 'documents'
        with a list of retrieved Document objects.
    """
    messages = state.get("messages", [])
    if messages:
        user_query = messages[0].content
    else:
        user_query = None
    if not user_query:
        return {"documentation": [empty_document], "flow": [FLOW_NAME]}
    # --- Use the retriever ---
    try:
        retrieved_docs: List[Document] = retriever.invoke(user_query)
    except Exception as e:
        return {"documentation": [empty_document], "flow": [FLOW_NAME]} 

    # --- Return the update for the state ---
    return {"documentation": retrieved_docs, "flow": [FLOW_NAME]}