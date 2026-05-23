from pydantic import BaseModel

class DecisionAtom(BaseModel):
    id: str
    decision: str
    reasoning: str
    evidence: list[str]   # format: "commit:abc1234", "issue:#42", "pr:#7"
    confidence: float     # 0.0 to 1.0

class Assumption(BaseModel):
    id: str
    statement: str
    risk_level: str       # "critical" | "moderate" | "low"
    depends_on: list[str] # IDs of other assumptions

class FailureRecord(BaseModel):
    approach: str
    reason_failed: str
    evidence: list[str]

class GhostDecision(BaseModel):
    location: str         # "src/auth/middleware.py:47"
    observation: str
    possible_reasons: list[str]

class KnowledgeCore(BaseModel):
    repo_url: str
    analyzed_at: str      # ISO timestamp
    decision_atoms: list[DecisionAtom]
    assumptions: list[Assumption]
    failure_memory: list[FailureRecord]
    ghost_decisions: list[GhostDecision]
    summary: str          # 2-3 sentence plain English summary

class AnalyzeResponse(BaseModel):
    success: bool
    knowledge_core: KnowledgeCore | None
    error: str | None
    cached: bool = False

class QueryResponse(BaseModel):
    success: bool
    answer: str
    citations: list[str]
    confidence: str       # "high" | "medium" | "low"

class AlarmResponse(BaseModel):
    success: bool
    violation_detected: bool
    violated_assumption: Assumption | None
    explanation: str
    new_assumption_introduced: str | None

class OnboardResponse(BaseModel):
    success: bool
    checklist: list[dict]  # {"priority": int, "topic": str, "why": str, "evidence": str}
    warning_count: int