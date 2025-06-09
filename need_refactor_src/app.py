from dotenv import load_dotenv, find_dotenv
import sys
import os

load_dotenv(find_dotenv())

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from demo.main import ChatUI 
from core.graph.codegen_graph import CodeGenGraph
from core.database.vector_store import VectorStore
from core.graph.overall_graph import OverallGraph

if __name__ == "__main__":
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
    VECTORSTORE_PATH= os.getenv("VECTORSTORE_PATH")
    VECTORSTORE_COLLECTION= os.getenv("VECTORSTORE_COLLECTION")

    
    vector_database = VectorStore(
        persistent_path= VECTORSTORE_PATH,
        collection_name= VECTORSTORE_COLLECTION
    ) 
    code_gen_graph = CodeGenGraph(
        model=DEFAULT_MODEL,
        retriever= vector_database.as_retriever()) 
    overall_graph = OverallGraph(
        codegen_graph= code_gen_graph,
        model_name= DEFAULT_MODEL)
    ui = ChatUI(
        vector_store= vector_database,
        graph= overall_graph
    )
    app = ui.create_ui()
    app.launch(server_port=8080)
    