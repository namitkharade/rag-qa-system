#!/usr/bin/env python
"""
PDF Ingestion script that handles single files or entire directories.
Supports both specific PDF files and bulk ingestion from a folder.
Run this after setting up your environment.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ingest import ingest_permitted_development_rights, test_retrieval


def find_pdfs_in_folder(folder_path: str) -> list:
    """Find all PDF files in a folder recursively."""
    folder = Path(folder_path)
    if not folder.exists():
        return []
    
    pdf_files = list(folder.glob("**/*.pdf"))
    return sorted([str(p) for p in pdf_files])


def ingest_folder(folder_path: str):
    """Ingest all PDFs from a folder."""
    pdf_files = find_pdfs_in_folder(folder_path)
    
    if not pdf_files:
        print(f"❌ No PDF files found in {folder_path}")
        return
    
    print(f"\n📂 Found {len(pdf_files)} PDF file(s) to ingest\n")
    
    total_pages = 0
    ingested_files = 0
    failed_files = []
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"[{idx}/{len(pdf_files)}] Ingesting: {Path(pdf_path).name}")
            stats = ingest_permitted_development_rights(pdf_path)
            
            total_pages += stats.get('total_pages', 0)
            ingested_files += 1
            
            print(f"      ✅ Success | Pages: {stats['total_pages']}")
        except Exception as e:
            print(f"      ❌ Failed: {str(e)}")
            failed_files.append((pdf_path, str(e)))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Ingestion Summary")
    print("=" * 80)
    print(f"✅ Successfully ingested: {ingested_files} file(s)")
    print(f"📄 Total pages processed: {total_pages}")
    
    if failed_files:
        print(f"\n⚠️  Failed files ({len(failed_files)}):")
        for file, error in failed_files:
            print(f"   - {Path(file).name}: {error}")
    
    if ingested_files > 0:
        # Test retrieval
        print("\n📊 Testing retrieval with sample queries...\n")
        
        test_queries = [
            "What are the main topics covered?",
            "What are the key conditions and requirements?",
            "What size or dimension limits are mentioned?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            results = test_retrieval(query, k=2)
            print("-" * 80)
        
        print("\n✅ All PDFs ingested successfully!")
        print("You can now query the agent with questions about the documents!\n")


def main():
    """Run the ingestion pipeline."""
    
    print("\n🚀 Starting PDF Ingestion Pipeline\n")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set it in your .env file or export it:\n")
        print("  export OPENAI_API_KEY=sk-your-key-here\n")
        sys.exit(1)
    
    # Determine what to ingest
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        # Try to find PDF folder or file
        possible_paths = [
            "../pdfs",
            "../../pdfs",
            "./pdfs",
            "../240213 Permitted Development Rights.pdf",
            "../../240213 Permitted Development Rights.pdf",
            "./240213 Permitted Development Rights.pdf",
        ]
        
        target_path = None
        for path in possible_paths:
            if os.path.exists(path):
                target_path = path
                break
        
        if target_path is None:
            print("❌ Error: Could not find PDF folder or file")
            print("Please specify the path:\n")
            print("  python ingest_pdf.py /path/to/pdfs/folder")
            print("  python ingest_pdf.py /path/to/document.pdf\n")
            sys.exit(1)
    
    try:
        target_path = os.path.abspath(target_path)
        
        if os.path.isdir(target_path):
            # Ingest entire folder
            ingest_folder(target_path)
        else:
            # Ingest single file
            if not target_path.lower().endswith('.pdf'):
                print(f"❌ Error: {target_path} is not a PDF file")
                sys.exit(1)
            
            print(f"📄 Ingesting: {Path(target_path).name}\n")
            stats = ingest_permitted_development_rights(target_path)
            
            # Test retrieval
            print("\n📊 Testing retrieval with sample queries...\n")
            
            test_queries = [
                "What are the main topics covered?",
                "What are the key conditions and requirements?",
                "What size or dimension limits are mentioned?"
            ]
            
            for query in test_queries:
                print(f"\n🔍 Query: {query}")
                results = test_retrieval(query, k=2)
                print("-" * 80)
            
            print("\n✅ Ingestion completed successfully!")
            print(f"📁 Collection: {stats['collection_name']}")
            print(f"📄 Total Pages: {stats['total_pages']}")
            print(f"📦 Parent Chunks: {stats.get('parent_chunks', 'N/A')}")
            print("\nYou can now query the agent with questions about the regulations!\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check the path and try again.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
