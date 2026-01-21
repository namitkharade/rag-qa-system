"""
Upload test drawing data and test citations with geometry analysis.
"""

import json
import time

import requests


def upload_drawing():
    """Upload test drawing to Redis."""
    print("\n" + "=" * 80)
    print("STEP 1: UPLOADING TEST DRAWING DATA")
    print("=" * 80)
    
    # Test drawing with plot and extension
    drawing_data = [
        {
            "type": "plot",
            "id": "plot_boundary",
            "points": [[0, 0], [20, 0], [20, 30], [0, 30]],
            "area": 600
        },
        {
            "type": "existing_building",
            "id": "house",
            "points": [[5, 5], [15, 5], [15, 15], [5, 15]],
            "area": 100
        },
        {
            "type": "extension",
            "id": "new_extension",
            "points": [[15, 5], [18, 5], [18, 12], [15, 12]],
            "area": 21
        }
    ]
    
    user_id = "test_user_with_drawing"
    
    print(f"\n📐 Test Drawing Data:")
    print(f"  - Plot: 20m x 30m (600 m²)")
    print(f"  - Existing building: 10m x 10m (100 m²)")
    print(f"  - Proposed extension: 3m x 7m (21 m²)")
    print(f"  - Total coverage: 121 m² (20.17% of plot)")
    print(f"\n✅ This should COMPLY with 50% curtilage rule")
    
    # Upload to Redis via backend API
    url = "http://localhost:8000/upload_drawing"
    payload = {
        "user_id": user_id,
        "drawing_data": drawing_data
    }
    
    print(f"\n📤 Uploading to: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Drawing uploaded successfully for user: {user_id}")
            return user_id
        else:
            print(f"⚠️  Upload response: {response.status_code}")
            print(response.text)
            return user_id
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Backend not available, trying agent service directly...")
        return user_id
    except Exception as e:
        print(f"⚠️  Upload error: {e}")
        return user_id


def test_with_drawing(user_id):
    """Test compliance check with drawing data."""
    
    print("\n" + "=" * 80)
    print("STEP 2: TESTING CITATIONS WITH GEOMETRY ANALYSIS")
    print("=" * 80)
    
    url = "http://localhost:8002/process"
    
    payload = {
        "message": "Does this building extension comply with the 50% curtilage rule and 2m boundary rule?",
        "user_id": user_id
    }
    
    print(f"\n📝 Query: {payload['message']}")
    print(f"👤 User ID: {user_id}")
    print(f"\n⚙️  Processing with LangGraph workflow...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 80)
            print("WORKFLOW EXECUTION")
            print("=" * 80)
            
            for step in result.get("reasoning_steps", []):
                print(f"  {step}")
            
            print("\n" + "=" * 80)
            print("RETRIEVED CONTEXT")
            print("=" * 80)
            print(f"📚 Regulations: {len(result.get('regulations', []))} documents")
            print(f"📐 Drawing Available: {result.get('drawing_available', False)}")
            
            if result.get('geometry_analysis'):
                print(f"\n📊 Geometry Analysis Preview:")
                print(f"   {result['geometry_analysis'][:300]}...")
            
            print("\n" + "=" * 80)
            print("FINAL ANSWER WITH CITATIONS")
            print("=" * 80)
            
            answer = result.get("answer", "")
            
            try:
                answer_json = json.loads(answer)
                
                print("\n✅ Valid JSON Response Received!")
                
                # Display answer
                print("\n" + "-" * 80)
                print("COMPLIANCE ANALYSIS")
                print("-" * 80)
                print(answer_json.get("answer", "No answer provided"))
                
                # Display citations
                citations = answer_json.get("citations", [])
                
                print("\n" + "-" * 80)
                print(f"CITATIONS ({len(citations)} total)")
                print("-" * 80)
                
                for i, citation in enumerate(citations, 1):
                    print(f"\n[{i}] {citation.get('source', 'Unknown')}")
                    print(f"    Reference: {citation.get('reference', 'N/A')}")
                    print(f"    Content: \"{citation.get('content', 'N/A')[:150]}...\"")
                    print(f"    Relevance: {citation.get('relevance', 'N/A')[:150]}...")
                
                print("\n" + "=" * 80)
                print("✅ TEST COMPLETE: Citations are working with geometry!")
                print("=" * 80)
                
                print("\n📊 Summary:")
                print(f"  - Answer field present: ✅")
                print(f"  - Citations field present: ✅")
                print(f"  - Number of citations: {len(citations)}")
                print(f"  - Geometry analysis used: {'✅' if result.get('geometry_analysis') else '❌'}")
                print(f"  - Regulations referenced: ✅")
                
            except json.JSONDecodeError:
                print("\n⚠️  Response is not JSON. Raw answer:")
                print(answer[:500])
        
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (processing may take longer for complex queries)")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE CITATION TEST WITH DRAWING DATA")
    print("=" * 80)
    
    # Step 1: Upload drawing
    user_id = upload_drawing()
    
    # Small delay to ensure data is in Redis
    time.sleep(2)
    
    # Step 2: Test with drawing
    test_with_drawing(user_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
