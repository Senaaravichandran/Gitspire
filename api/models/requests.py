from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    repo_url: str
    force_refresh: bool = False

class QueryRequest(BaseModel):
    repo_url: str
    question: str  # max 500 chars enforced in route

class AlarmRequest(BaseModel):
    repo_url: str
    code_snippet: str  # max 10,000 chars enforced in route

class OnboardRequest(BaseModel):
    repo_url: str
    feature_description: str