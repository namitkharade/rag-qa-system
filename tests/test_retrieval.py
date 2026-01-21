#!/usr/bin/env python
"""Test script to verify ChromaDB retrieval is working."""

from vector_store import vector_store


def test_basic_retrieval():
    """Test basic retrieval from ChromaDB."""
    queries = [
        "permitted development rights",
        "building regulations",
        "Class A development"
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        try:
            results = vector_store.similarity_search(query, k=3)
            print(f"✅ Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                score = result.get('score', 'N/A')
                
                print(f"Result {i}:")
                print(f"  Content: {content[:200]}...")
                print(f"  Score: {score}")
                print(f"  Page: {metadata.get('page', 'N/A')}")
                print(f"  Is Table: {metadata.get('is_table', False)}")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 Testing ChromaDB Retrieval\n")
    test_basic_retrieval()
    print("\n✅ Testing complete!\n")
