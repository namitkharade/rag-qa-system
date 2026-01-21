"""
Test the citation functionality through the API.
Makes a request to the agent service to verify citations are returned.
"""

import json
import sys

import requests


def test_api_with_citations():
    """Test the agent API to verify citation functionality."""
    
    print("\n" + "=" * 80)
    print("TESTING CITATIONS VIA API")
    print("=" * 80)
    
    # API endpoint (agent service runs on port 8002 mapped to container's 8001)
    url = "http://localhost:8002/process"
    
    # Test payload
    payload = {
        "message": "Does this building extension comply with the 50% curtilage rule?",
        "user_id": "test_user_citations"
    }
    
    print(f"\n📍 API Endpoint: {url}")
    print(f"📝 Request Payload:")
    print(json.dumps(payload, indent=2))
    
    print("\n⚙️  Sending request...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 80)
            print("RESPONSE STRUCTURE")
            print("=" * 80)
            print(f"Keys in response: {list(result.keys())}")
            
            if "reasoning_steps" in result:
                print("\nReasoning Steps:")
                for i, step in enumerate(result["reasoning_steps"], 1):
                    print(f"  {i}. {step}")
            
            if "regulations" in result:
                print(f"\nRetrieved {len(result['regulations'])} regulations from ChromaDB")
            
            if result.get("geometry_analysis"):
                print("\nGeometry Analysis Available: Yes")
                print(f"   Preview: {result['geometry_analysis'][:150]}...")
            else:
                print("\nGeometry Analysis Available: No")
                print("   (No drawing data in Redis for this user_id)")
            
            print("\n" + "=" * 80)
            print("ANSWER (Checking for Citation Structure)")
            print("=" * 80)
            
            answer = result.get("answer", "")
            print(f"\nRaw answer (first 300 chars):")
            print(answer[:300] + "...\n")
            
            try:
                answer_json = json.loads(answer)
                
                print("SUCCESS: Answer is valid JSON with citations!")
                print("\n" + "=" * 80)
                print("PARSED CITATION STRUCTURE")
                print("=" * 80)
                
                if "answer" in answer_json:
                    print(f"\nAnswer Field:")
                    print(f"   {answer_json['answer'][:200]}...")
                
                if "citations" in answer_json:
                    citations = answer_json["citations"]
                    print(f"\nCitations: {len(citations)} found")
                    
                    for i, citation in enumerate(citations, 1):
                        print(f"\n   Citation #{i}:")
                        print(f"   ├─ Source: {citation.get('source', 'N/A')}")
                        print(f"   ├─ Reference: {citation.get('reference', 'N/A')}")
                        print(f"   ├─ Content: {citation.get('content', 'N/A')[:100]}...")
                        print(f"   └─ Relevance: {citation.get('relevance', 'N/A')[:100]}...")
                    
                    print("\nVERIFICATION COMPLETE: Citations are working correctly!")
                    
                else:
                    print("\nWARNING: No 'citations' field found in JSON response")
                
            except json.JSONDecodeError as e:
                print(f"WARNING: Answer is not valid JSON")
                print(f"   Error: {str(e)}")
                print("\n   This might happen if:")
                print("   - The LLM didn't follow the JSON format instruction")
                print("   - There's additional text before/after the JSON")
                print("   - The prompt needs refinement")
                
                if '{' in answer and '}' in answer:
                    start = answer.find('{')
                    end = answer.rfind('}') + 1
                    try:
                        extracted = json.loads(answer[start:end])
                        print("\nFound and extracted valid JSON from response:")
                        print(json.dumps(extracted, indent=2)[:500])
                    except:
                        pass
        
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: Cannot connect to agent service")
        print("   Make sure Docker containers are running:")
        print("   docker-compose up -d")
        
    except requests.exceptions.Timeout:
        print("Timeout: Request took too long")
        print("   The agent might be processing or ChromaDB might be slow")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        test_api_with_citations()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
