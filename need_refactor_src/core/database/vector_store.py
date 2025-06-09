from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional, Any
class VectorStore:
    """
    Manages a ChromaDB vector store for document storage and retrieval.

    Handles loading, splitting, embedding, adding, and deleting documents,
    primarily focusing on PDF files initially.

    Attributes:
        client: The ChromaDB persistent client instance.
        embeddings: The embedding model instance (Google Generative AI).
        vector_store: The LangChain Chroma vector store instance.
        text_splitter: The text splitter instance for chunking documents.
    """
    def __init__(
        self,
        persistent_path: str = "A:/Code/coder/data",
        embeddings_model: str = "models/text-embedding-004",
        collection_name: str = "my_documents",
        chunk_config: dict = {"chunk_size": 500, "chunk_overlap": 20}
    ):
        """
        Initializes the VectorStore.

        Args:
            persistent_path: Path to the directory for storing ChromaDB data.
            embeddings_model: Name of the Google Generative AI embedding model.
            collection_name: Name of the collection within ChromaDB.
            chunk_config: Dictionary with 'chunk_size' and 'chunk_overlap'
                            for the text splitter.
        """
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

    def load_document(self, path: str) -> list[Document]:
        """
        Loads documents from a PDF file path and optionally splits them.

        Args:
            path: The path to the PDF file.
            split: Whether to split the loaded documents using the configured text splitter. Defaults to True.

        Returns:
            A list of LangChain Document objects (split or unsplit).
            Returns an empty list if loading fails.
        """
        loader = PyMuPDFLoader(path)
        docs = loader.load()
        return docs

    def add_documents(self, documents: list[Document], split: bool = True) -> list[str]:
        """
        Adds a list of documents to the vector store, optionally splitting them first.

        Args:
            documents: A list of LangChain Document objects.
            split: Whether to split the documents before adding. Defaults to False,
            assuming documents might already be split or splitting is handled elsewhere.

        Returns:
            A list of IDs for the added documents. Returns an empty list on failure.
        """
        if split:
            documents = self.text_splitter.split_documents(documents)
        return self.vector_store.add_documents(documents)

    def create_index(self, path: str) -> list[str]:
        """
        Loads, splits (by default in load_document), and adds documents from a file path.
        This is a convenience method combining load_document and add_documents.

        Args:
            path: The path to the PDF file.

        Returns:
            A list of IDs for the added document chunks.
        """
        documents = self.load_document(path)
        return self.add_documents(documents)

    def as_retriever(self):
        """
        Returns the vector store configured as a LangChain Retriever.

        Args:
            search_kwargs: Optional dictionary of keyword arguments to pass to the
                            retriever's search methods (e.g., {'k': 5, 'filter': ...}).

        Returns:
            A LangChain Retriever instance.
        """
        return self.vector_store.as_retriever()

    def list_source(self) -> list[str]:
        """
        Retrieves a list of unique source identifiers from the document metadata.

        Returns:
            A list of unique source strings present in the collection.
            Returns an empty list if the collection is empty or an error occurs.
        """
        metadatas = self.vector_store.get(include=["metadatas"])["metadatas"]
        sources = set(metadata["source"] for metadata in metadatas)
        return list(sources)
    def delete_documents_by_source(self, source: str):
        """
        Deletes all document chunks where the 'source' metadata field exactly matches
        the provided source string.

        Args:
            source: The exact source identifier (e.g., file path) of the documents to delete.

        Returns:
            A status message indicating success or failure.
        """
        try:
            self.vector_store.delete(where={"source": source})
            return f"Attempted deletion for documents with exact source '{source}'."
        except Exception as e:
            return f"Error deleting documents from source '{source}': {str(e)}"
    def similarity_search(self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Performs a similarity search against the vector store.

        Args:
            query: The text query to search for.
            k: The number of similar documents to return. Defaults to 4.
            filter: Optional dictionary for metadata filtering during search.
                    Example: {"source": "specific_document.pdf"}

        Returns:
            A list of LangChain Document objects most similar to the query,
            respecting the k limit and filter. Returns empty list on error.
        """
        try:
            results = self.vector_store.similarity_search(query=query, k=k, filter=filter)
            return results
        except Exception as e:
            return []
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Retrieves basic information about the collection, primarily the document count.

        Returns:
            A dictionary containing information like the number of documents (chunks).
            Example: {'count': 150}
            Returns {'count': 0, 'error': 'message'} on failure.
        """
        try:
            count = self.vector_store.count()
            return {"count": count}
        except Exception as e:
            return {"count": 0, "error": str(e)}
    def clear_collection(self) -> str:
        """
        Deletes ALL documents (chunks) from the collection. Use with caution!

        This retrieves all document IDs and then deletes them. It does not delete
        the collection itself, only its contents.

        Returns:
            A status message indicating success or failure.
        """
        try:
            ids_to_delete = self.vector_store.get()['ids']
            self.vector_store.delete(ids=ids_to_delete)
            # Verify deletion
            new_count = self.vector_store.count()
            if new_count == 0:
                return f"Successfully cleared all {len(ids_to_delete)} documents from collection '{self.collection_name}'."
            else:
                return f"Error: Failed to clear all documents from collection '{self.collection_name}'. {new_count} items remain."
        except Exception as e:
            return f"Error clearing collection '{self.collection_name}': {str(e)}"
