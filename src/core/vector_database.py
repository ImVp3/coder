from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStore:
    def __init__(
        self,
        persistent_path: str = "A:/Code/coder/data",
        embeddings_model: str = "models/text-embedding-004",
        collection_name: str = "my_documents",
        chunk_config : dict = { "chunk_size" : 500, "chunk_overlap" : 20 }
    ):
        self.client = chromadb.PersistentClient(path=persistent_path)
        self.embeddings = GoogleGenerativeAIEmbeddings(model=embeddings_model)
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            **chunk_config
        )

    def load_document(self, path: str, split: bool = True ) -> list[Document]:
        loader = PyMuPDFLoader(path)
        docs = loader.load()
        if split:
            docs = self.text_splitter.split_documents(docs)
        return docs
    def add_documents(self, documents: list[Document], split: bool = True) -> list[str]:
        if split: 
            documents = self.text_splitter.split_documents(documents)
        return self.vector_store.add_documents(documents)
    def create_index(self, path: str) -> list[str]:
        documents = self.load_document(path)
        return self.add_documents(documents)
    def as_retriever(self):
        return self.vector_store.as_retriever()
    def list_source (self) -> list[str]:
        metadatas =  self.vector_store.get(include=["metadatas"])["metadatas"]
        sources = set(metadata["source"] for metadata in metadatas)
        return list(sources)
    def delete_documents_by_source (self, source: str):
        try:
            
            self.vector_store.delete(where={
                "source": {
                    "$in": [item for item in self.list_source() if source in item]
                    }
                })
            return (f"Deleted documents from {source} successfully.")
        except Exception as e:
            return (f"Error deleting documents from {source}: {str(e)}")


