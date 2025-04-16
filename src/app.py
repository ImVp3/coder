from dotenv import load_dotenv, find_dotenv
import sys
import os

load_dotenv(find_dotenv())

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ui.interface import ChatUI  
from src.ui.interface import ChatUI
from src.core.vector_database import * 
from src.core.graph import CodeGenGraph

if __name__ == "__main__":
    vector_database = VectorStore(
        persistent_path= "A:/Code/coder/data/chromadb",
        collection_name="test"
    ) 
    graph = CodeGenGraph(model="gemini-2.0-flash-lite")  
    ui = ChatUI(
        vector_store= vector_database,
        graph= graph
    )
    app = ui.create_ui()
    app.launch(server_port=8080)