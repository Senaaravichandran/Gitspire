"""
Quick API test to verify Gitspire is working perfectly
"""
import httpx
import asyncio

async def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Gitspire API...\n")
    
    # Test 1: Health check
    print("1️⃣ Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        print("   ✅ Health check passed!\n")
    
    # Test 2: Analyze endpoint (small repo)
    print("2️⃣ Testing analyze endpoint...")
    print("   (This may take 10-30 seconds for Gemini analysis...)")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/api/analyze",
            json={
                "repo_url": "https://github.com/octocat/Hello-World",
                "force_refresh": False
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        
        if data.get("success"):
            print(f"   ✅ Analysis successful!")
            print(f"   Cached: {data.get('cached', False)}")
            core = data.get("knowledge_core", {})
            print(f"   Decisions: {len(core.get('decisions', []))}")
            print(f"   Assumptions: {len(core.get('assumptions', []))}")
            print(f"   Ghosts: {len(core.get('ghosts', []))}")
        else:
            print(f"   ⚠️  Error: {data.get('error')}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_api())
