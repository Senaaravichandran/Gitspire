import asyncio
import importlib

try:
    httpx = importlib.import_module("httpx")
except ImportError:
    print("Error: httpx is not installed. Install it with: pip install httpx")
    raise

"""Quick API smoke test for the current Gitspire response schema."""

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
            pulse_report = core.get("pulse_report") or {}
            pulse_decisions = pulse_report.get("decisions", []) if isinstance(pulse_report, dict) else []

            print(f"   Decision atoms: {len(core.get('decision_atoms', []))}")
            print(f"   Assumptions: {len(core.get('assumptions', []))}")
            print(f"   Failure records: {len(core.get('failure_memory', []))}")
            print(f"   Ghost decisions: {len(core.get('ghost_decisions', []))}")
            print(f"   Regretted decisions: {len(core.get('regretted_decisions', []))}")
            print(f"   Orphaned architecture: {len(core.get('orphaned_architecture', []))}")
            print(f"   Pulse decisions: {len(pulse_decisions)}")

            missing_keys = [
                key for key in [
                    'decision_atoms',
                    'assumptions',
                    'failure_memory',
                    'ghost_decisions',
                    'regretted_decisions',
                    'orphaned_architecture',
                    'pulse_report',
                ]
                if key not in core
            ]
            assert not missing_keys, f"Missing knowledge_core keys: {missing_keys}"
        else:
            print(f"   ⚠️  Error: {data.get('error')}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_api())
