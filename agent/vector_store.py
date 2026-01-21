import chromadb
from config import settings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


class VectorStore:
    """Manages the persistent Vector DB (ChromaDB) for regulatory PDFs."""
    
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            tenant="default_tenant",
            database="default_database"
        )
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings
        )
    
    def similarity_search(self, query: str, k: int = 5):
        """Search for relevant regulatory documents."""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
    
    def add_documents(self, documents, metadatas=None):
        """Add regulatory documents to the persistent Vector DB."""
        self.vectorstore.add_texts(
            texts=documents,
            metadatas=metadatas
        )


vector_store = VectorStore()
