from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain.schema.document import Document
def load_docs_from_url (url: str, max_depth: int):
    try:
        loader = RecursiveUrlLoader(
                                url=url, 
                                max_depth=2, 
                                extractor=lambda x: Soup(x, "html.parser").text
                            )
        docs = loader.load()
        status = f"Loaded {len(docs)} from {url} with depth = {max_depth}"
    except:
        docs = []
        status = f"Error: Can not load documents from {url}"
    return docs, status

def parse_code_generation (code_generation):
    code = code_generation.code
    imports = code_generation.imports
    prefix = code_generation.prefix
    res = f"{prefix}\n```python\n{imports}\n{code}\n```"
    return res     

def handle_url_btn (url_input: str, max_depth : int, vector_store ): 
    docs,status = load_docs_from_url(url=url_input, max_depth= max_depth)
    if len(docs):
        vector_store.add_documents(documents = docs, split = True)
    return status, get_source_list(vector_store)

def handle_file_btn(file_uploader, vector_store):
    if not file_uploader:
        return "No files uploaded.", get_source_list(vector_store)
    try:
        documents = []
        for file in file_uploader:
            docs = vector_store.load_document(file) 
            documents.extend(docs)
        vector_store.add_documents(documents)
        return f"Uploaded {len(file_uploader)} documents successfully.", get_source_list(vector_store)
    except Exception as e:
        return f"Error uploading documents: {str(e)}", get_source_list(vector_store)
def get_source_list(vector_store):
    sources = vector_store.list_source()
    return sorted(sources)
def handle_delete_source(source, vector_store):
    status = vector_store.delete_documents_by_source(source)
    sources = vector_store.list_source()
    return status, sorted(sources)
