"""
Ingest regulatory PDF documents into ChromaDB with Parent Document Retriever strategy.

This script uses semantic chunking and hierarchical document storage to handle
complex regulatory documents with nested conditions (e.g., Class A, B, C rules).
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

# Must set this BEFORE importing chromadb to prevent default embedding function loading
os.environ["CHROMA_DEFAULT_EMBEDDING"] = "none"
# Disable ChromaDB telemetry to prevent warning messages
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import pymupdf4llm
# Import chromadb client directly to avoid Collection model loading default embedding
from chromadb.api import ClientAPI
from chromadb.config import Settings as ChromaSettings
from config import settings
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RegulatoryDocumentIngester:
    """
    Ingests regulatory PDF documents using Parent Document Retriever strategy.
    
    This approach maintains document hierarchy and context by:
    1. Storing large "parent" chunks with full context
    2. Creating smaller "child" chunks for precise retrieval
    3. Linking children back to their parent documents
    
    Perfect for hierarchical regulations with complex conditions.
    """
    
    def __init__(
        self,
        collection_name: str = None,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 400,
        chunk_overlap: int = 100
    ):
        """
        Initialize the ingester.
        
        Args:
            collection_name: ChromaDB collection name
            parent_chunk_size: Size of parent chunks (larger for context)
            child_chunk_size: Size of child chunks (smaller for precision)
            chunk_overlap: Overlap between chunks to maintain continuity
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embeddings FIRST (before ChromaDB client)
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize ChromaDB HTTP client using chromadb.HttpClient directly
        # This avoids importing Collection model which loads default embedding function
        import chromadb
        self.chroma_client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        
        # Initialize vector store for child chunks with explicit embedding function
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            collection_metadata={"hnsw:space": "cosine"}
        )
        
        # In-memory store for parent documents
        # In production, use a persistent store (Redis, PostgreSQL, etc.)
        self.docstore = InMemoryStore()
        
        # Text splitters for hierarchical chunking
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ".",     # Sentences
                " ",     # Words
                ""
            ]
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )
        
        # Parent Document Retriever
        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
        )
    
    def load_pdf(self, pdf_path: str) -> List[Any]:
        """
        Load PDF document using pymupdf4llm library.
        
        This method uses pymupdf4llm to accurately parse:
        - Complex layouts with preserved formatting
        - Tables in Markdown format
        - Headings and structured content
        - Multi-column documents
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Document objects with enhanced metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"Loading PDF with pymupdf4llm: {pdf_path}")
        print("Extracting text content from PDF...")
        
        # Extract markdown content from PDF using pymupdf4llm
        # This preserves tables, headings, and document structure
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        # Get page-level data for metadata
        import pymupdf
        pdf_doc = pymupdf.open(pdf_path)
        
        # Split by page markers or create documents per page
        documents = []
        
        # Split markdown by page if page markers exist
        # pymupdf4llm includes page markers like "-----\n\n" between pages
        pages = md_text.split('\n\n-----\n\n')
        
        for page_num, page_content in enumerate(pages, start=1):
            if not page_content.strip():
                continue
            
            # Detect if content contains tables (markdown tables have | characters)
            has_table = '|' in page_content and '---' in page_content
            
            doc = Document(
                page_content=page_content,
                metadata={
                    'page': page_num,
                    'is_table': has_table,
                    'element_type': 'table' if has_table else 'text',
                    'content_format': 'markdown',
                }
            )
            documents.append(doc)
        
        pdf_doc.close()
        
        print(f"Extracted {len(documents)} pages from PDF")
        print(f"Pages with tables: {sum(1 for doc in documents if doc.metadata.get('is_table', False))}")
        
        return documents
    
    def enhance_metadata(
        self,
        documents: List[Any],
        source_name: str,
        document_type: str = "regulation"
    ) -> List[Any]:
        """
        Enhance document metadata with additional context.
        Preserves table-specific metadata added during PDF parsing.
        
        Args:
            documents: List of Document objects
            source_name: Name of the source document
            document_type: Type of document (regulation, guideline, etc.)
            
        Returns:
            Documents with enhanced metadata
        """
        for i, doc in enumerate(documents):
            # Preserve existing metadata (especially table flags)
            existing_metadata = doc.metadata.copy()
            
            doc.metadata.update({
                "source_name": source_name,
                "document_type": document_type,
                "chunk_index": i,
                "total_chunks": len(documents),
                "ingestion_timestamp": str(uuid.uuid4()),
            })
            
            # Ensure table metadata is preserved
            if 'is_table' in existing_metadata:
                doc.metadata['is_table'] = existing_metadata['is_table']
            if 'element_type' in existing_metadata:
                doc.metadata['element_type'] = existing_metadata['element_type']
            if 'content_format' in existing_metadata:
                doc.metadata['content_format'] = existing_metadata['content_format']
            if 'contains_structured_rules' in existing_metadata:
                doc.metadata['contains_structured_rules'] = existing_metadata['contains_structured_rules']
        
        return documents
    
    def ingest_documents(
        self,
        documents: List[Any],
        use_parent_retriever: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest documents into ChromaDB with hierarchical chunking.
        Handles table chunks separately to preserve their structure.
        
        Args:
            documents: List of Document objects to ingest
            use_parent_retriever: Use Parent Document Retriever strategy
            
        Returns:
            Dictionary with ingestion statistics
        """
        # Separate table and non-table documents
        table_docs = [doc for doc in documents if doc.metadata.get('is_table', False)]
        non_table_docs = [doc for doc in documents if not doc.metadata.get('is_table', False)]
        
        print(f"Ingesting {len(documents)} documents: {len(table_docs)} tables, {len(non_table_docs)} text elements")
        
        if use_parent_retriever:
            print(f"Using Parent Document Retriever strategy")
            print(f"Parent chunk size: {self.parent_chunk_size}, Child chunk size: {self.child_chunk_size}")
            
            # For tables, store them directly without splitting to preserve structure
            if table_docs:
                print(f"Storing {len(table_docs)} table chunks directly (no splitting)...")
                table_texts = [doc.page_content for doc in table_docs]
                table_metadatas = [doc.metadata for doc in table_docs]
                self.vectorstore.add_texts(texts=table_texts, metadatas=table_metadatas)
            
            # For non-table docs, use Parent Document Retriever with chunking
            if non_table_docs:
                print(f"Processing {len(non_table_docs)} text elements with hierarchical chunking...")
                self.retriever.add_documents(non_table_docs)
            
            # Get statistics
            parent_docs = list(self.docstore.yield_keys())
            
            return {
                "strategy": "parent_document_retriever_with_tables",
                "total_elements": len(documents),
                "table_chunks": len(table_docs),
                "text_elements": len(non_table_docs),
                "parent_chunks": len(parent_docs),
                "parent_chunk_size": self.parent_chunk_size,
                "child_chunk_size": self.child_chunk_size,
                "collection_name": self.collection_name,
                "status": "success"
            }
        else:
            # Fallback: simple chunking without parent-child relationship
            print(f"Ingesting {len(documents)} documents with simple chunking...")
            
            chunks = self.parent_splitter.split_documents(documents)
            
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            
            self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
            
            return {
                "strategy": "simple_chunking",
                "total_pages": len(documents),
                "total_chunks": len(chunks),
                "chunk_size": self.parent_chunk_size,
                "collection_name": self.collection_name,
                "status": "success"
            }
    
    def ingest_pdf(
        self,
        pdf_path: str,
        source_name: str = None,
        document_type: str = "regulation",
        use_parent_retriever: bool = True
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Load PDF, enhance metadata, and ingest into ChromaDB.
        
        Args:
            pdf_path: Path to the PDF file
            source_name: Name of the source document
            document_type: Type of document
            use_parent_retriever: Use Parent Document Retriever strategy
            
        Returns:
            Dictionary with ingestion statistics
        """
        # Load PDF
        documents = self.load_pdf(pdf_path)
        
        # Use filename as source name if not provided
        if source_name is None:
            source_name = Path(pdf_path).name
        
        # Enhance metadata
        documents = self.enhance_metadata(documents, source_name, document_type)
        
        # Ingest documents
        stats = self.ingest_documents(documents, use_parent_retriever)
        
        # Add PDF path to stats
        stats["pdf_path"] = pdf_path
        stats["source_name"] = source_name
        
        return stats


def ingest_permitted_development_rights(pdf_path: str = None) -> Dict[str, Any]:
    """
    Ingest the Permitted Development Rights PDF.
    
    Args:
        pdf_path: Path to the PDF file. If None, uses default path.
        
    Returns:
        Dictionary with ingestion statistics
    """
    # Default path (adjust as needed)
    if pdf_path is None:
        pdf_path = "../240213 Permitted Development Rights.pdf"
    
    print("=" * 80)
    print("Ingesting Permitted Development Rights PDF")
    print("=" * 80)
    
    # Initialize ingester with settings optimized for regulations
    ingester = RegulatoryDocumentIngester(
        parent_chunk_size=2000,  # Large chunks to preserve hierarchical context
        child_chunk_size=400,    # Smaller chunks for precise retrieval
        chunk_overlap=100        # Overlap to maintain continuity
    )
    
    # Ingest the PDF
    stats = ingester.ingest_pdf(
        pdf_path=pdf_path,
        source_name="Permitted Development Rights",
        document_type="regulation",
        use_parent_retriever=True  # Use Parent Document Retriever strategy
    )
    
    print("\n" + "=" * 80)
    print("Ingestion Complete!")
    print("=" * 80)
    print(f"Strategy: {stats['strategy']}")
    print(f"Source: {stats['source_name']}")
    print(f"Total Elements: {stats.get('total_elements', stats.get('total_pages', 'N/A'))}")
    print(f"Table Chunks: {stats.get('table_chunks', 0)}")
    print(f"Text Elements: {stats.get('text_elements', 'N/A')}")
    print(f"Parent Chunks: {stats.get('parent_chunks', 'N/A')}")
    print(f"Parent Chunk Size: {stats.get('parent_chunk_size', 'N/A')}")
    print(f"Child Chunk Size: {stats.get('child_chunk_size', 'N/A')}")
    print(f"Collection: {stats['collection_name']}")
    print("=" * 80)
    
    return stats


if __name__ == "__main__":
    """
    Main execution: Ingest the Permitted Development Rights PDF.
    """
    import sys

    # Check if PDF path is provided as argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Ingest the document
        stats = ingest_permitted_development_rights(pdf_path)
        
        print("\n✅ Ingestion completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
