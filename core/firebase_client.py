import hashlib
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, db

class FirebaseClient:

    def __init__(self):
        if not firebase_admin._apps:
            cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "")
                })
            else:
                # If credentials path is not provided or file doesn't exist, we skip init.
                # In production, this might crash if it's required.
                print("Warning: Firebase credentials not found, DB calls will fail.")

    def _repo_key(self, repo_url: str) -> str:
        # SHA256 hash of URL → first 16 hex chars
        # Firebase keys cannot contain . / [ ] $ # or whitespace
        return hashlib.sha256(repo_url.encode()).hexdigest()[:16]

    async def get_knowledge_core(self, repo_url: str) -> dict | None:
        try:
            key = self._repo_key(repo_url)
            ref = db.reference(f'/knowledge_cores/{key}')
            data = ref.get()
            
            if not data:
                return None
                
            analyzed_at_str = data.get("analyzed_at")
            if not analyzed_at_str:
                return None
                
            try:
                analyzed_at = datetime.fromisoformat(analyzed_at_str)
                # Ensure it's timezone aware for comparison
                if analyzed_at.tzinfo is None:
                    analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)
                    
                now = datetime.now(timezone.utc)
                if now - analyzed_at > timedelta(hours=24):
                    return None
            except ValueError:
                return None
                
            return data
        except Exception as e:
            print(f"Error reading from Firebase: {e}")
            return None

    async def save_knowledge_core(self, repo_url: str, knowledge_core: dict):
        try:
            key = self._repo_key(repo_url)
            knowledge_core["analyzed_at"] = datetime.now(timezone.utc).isoformat()
            
            ref = db.reference(f'/knowledge_cores/{key}')
            ref.set(knowledge_core)
        except Exception as e:
            print(f"Error saving to Firebase: {e}")

    async def get_cached_query(self, repo_url: str, question_hash: str) -> dict | None:
        try:
            repo_key = self._repo_key(repo_url)
            ref = db.reference(f'/query_cache/{repo_key}/{question_hash}')
            return ref.get()
        except Exception as e:
            print(f"Error reading query cache from Firebase: {e}")
            return None

    async def save_query_cache(self, repo_url: str, question_hash: str, response: dict):
        try:
            repo_key = self._repo_key(repo_url)
            ref = db.reference(f'/query_cache/{repo_key}/{question_hash}')
            ref.set(response)
        except Exception as e:
            print(f"Error saving query cache to Firebase: {e}")