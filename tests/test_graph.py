#!/usr/bin/env python
"""
Test script for the LangGraph compliance workflow.

Tests the three-node graph:
1. retrieve_regulations: Query ChromaDB
2. inspect_drawing: Analyze geometry from Redis
3. synthesize: Combine both contexts
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from graph import check_compliance


def test_compliance_check():
    """Test the full compliance workflow."""
    
    print("\n" + "=" * 80)
    print("LANGRAPH COMPLIANCE WORKFLOW TEST")
    print("=" * 80)
    
    questions = [
        "Does this building comply with the 50% curtilage rule?",
        "Are the walls at least 2m from the plot boundary?",
        "What are the key regulatory requirements for this extension?",
        "Check all compliance rules for permitted development."
    ]
    
    user_id = "test_user"
    
    print(f"\nUser ID: {user_id}")
    print("\nPrerequisites:")
    print("  1. Redis must be running")
    print("  2. Drawing data must be uploaded for user '{}'".format(user_id))
    print("  3. ChromaDB must have regulatory documents indexed")
    print("  4. Set OPENAI_API_KEY in environment")
    
    # Ask user which question to test
    print("\n" + "-" * 80)
    print("Select a question to test:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print(f"  {len(questions) + 1}. Custom question")
    
    try:
        choice = input("\nEnter choice (1-{}): ".format(len(questions) + 1)).strip()
        choice_num = int(choice)
        
        if choice_num == len(questions) + 1:
            question = input("\nEnter your custom question: ").strip()
        elif 1 <= choice_num <= len(questions):
            question = questions[choice_num - 1]
        else:
            print("Invalid choice. Using first question.")
            question = questions[0]
    
    except (ValueError, KeyboardInterrupt):
        print("\nUsing default question.")
        question = questions[0]
    
    print("\n" + "=" * 80)
    print("EXECUTING WORKFLOW")
    print("=" * 80)
    print(f"\nQuestion: {question}\n")
    
    try:
        result = check_compliance(question, user_id)
        
        print("\n" + "=" * 80)
        print("NODE 1: RETRIEVE REGULATIONS")
        print("=" * 80)
        print(f"\nRetrieved {len(result['regulations'])} regulatory documents:\n")
        for i, reg in enumerate(result['regulations'][:3], 1):
            print(f"{i}. {reg.get('metadata', {}).get('source_name', 'Unknown')}")
            print(f"   Score: {reg.get('score', 'N/A'):.4f}")
            print(f"   Preview: {reg['content'][:150]}...\n")
        
        print("\n" + "=" * 80)
        print("NODE 2: INSPECT DRAWING")
        print("=" * 80)
        if result['drawing_available']:
            print("\nDrawing data retrieved from Redis")
            if result['geometry_analysis']:
                print("\nGeometric Analysis:")
                print(result['geometry_analysis'])
        else:
            print("\nNo drawing data available in Redis")
            print("   Upload drawing first using: POST /upload_drawing")
        
        print("\n" + "=" * 80)
        print("NODE 3: SYNTHESIZE")
        print("=" * 80)
        print("\nFinal Answer:\n")
        print(result['answer'])
        
        print("\n" + "=" * 80)
        print("REASONING STEPS")
        print("=" * 80)
        for step in result['reasoning_steps']:
            print(f"  {step}")
        
        print("\n" + "=" * 80)
        print("Workflow completed successfully!")
        print("=" * 80 + "\n")
        
        return result
    
    except Exception as e:
        print(f"\nError during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def setup_test_data():
    """Helper to set up test data in Redis."""
    import redis
    
    print("\n" + "=" * 80)
    print("SETUP TEST DATA")
    print("=" * 80)
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        if not r.ping():
            print("\nCannot connect to Redis. Make sure Redis is running.")
            return False
        
        print("\nConnected to Redis")
        
        drawing_path = Path(__file__).parent.parent / "240314_Drawing.json"
        
        if not drawing_path.exists():
            print(f"\nDrawing file not found: {drawing_path}")
            print("   Using synthetic sample data...")
            
            sample_drawing = [
                {
                    "type": "POLYLINE",
                    "layer": "Plot Boundary",
                    "points": [
                        [-13160.59, 19584.96],
                        [-3160.59, 19584.96],
                        [-3160.59, 44584.96],
                        [-13160.59, 44584.96]
                    ],
                    "closed": True
                },
                {
                    "type": "POLYLINE",
                    "layer": "Walls",
                    "points": [
                        [-9660.59, 29584.96],
                        [-10660.59, 29584.96],
                        [-10660.59, 22084.96],
                        [-8560.59, 22084.96],
                        [-8560.59, 29584.96]
                    ],
                    "closed": True
                }
            ]
        else:
            print(f"\n📁 Loading drawing from: {drawing_path}")
            with open(drawing_path, 'r') as f:
                sample_drawing = json.load(f)
        
        # Store in Redis
        user_id = "test_user"
        key = f"session:{user_id}:drawing"
        
        r.setex(key, 3600, json.dumps(sample_drawing))
        
        print(f"\n✅ Stored drawing in Redis")
        print(f"   Key: {key}")
        print(f"   TTL: 3600 seconds (1 hour)")
        print(f"   Objects: {len(sample_drawing)}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error setting up test data: {str(e)}")
        return False


def main():
    """Main test runner."""
    
    print("\n" + "=" * 80)
    print("LANGRAPH COMPLIANCE GRAPH - TEST SUITE")
    print("=" * 80)
    
    # Ask if user wants to setup test data
    setup = input("\nSetup test data in Redis? (y/n): ").strip().lower()
    
    if setup == 'y':
        if not setup_test_data():
            print("\n⚠️  Test data setup failed. You may need to set up manually.")
            print("   Continuing anyway...\n")
    
    # Run the test
    input("\nPress Enter to start the workflow test...")
    result = test_compliance_check()
    
    if result:
        print("\n✨ Test completed successfully!")
    else:
        print("\n⚠️  Test encountered errors.")


if __name__ == "__main__":
    main()
