from pydantic import BaseModel

class DecisionAtom(BaseModel):
    id: str
    decision: str
    reasoning: str
    evidence: list[str]   # format: "commit:abc1234", "issue:#42", "pr:#7"
    confidence: float     # 0.0 to 1.0
    translated_source: bool | None = None
    source_language: str | None = None
    original_excerpt: str | None = None
    translated_excerpt: str | None = None

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

class RegrettedDecision(BaseModel):
    title: str
    original_decision: str
    why_it_exists: str
    regret_signals: list[str]
    emotional_evidence: str
    architectural_consequences: str
    current_risk_level: str   # "low" | "medium" | "high" | "critical"
    confidence_score: float

class OrphanedArchitecture(BaseModel):
    decision_title: str
    subsystem: str
    original_author: str
    last_seen_activity: str
    active_status: str        # "active" | "inactive" | "departed"
    criticality: str          # "low" | "medium" | "high" | "critical"
    orphan_risk: str          # "low" | "medium" | "high" | "critical"
    why_dangerous: str
    hidden_assumptions: list[str]
    suggested_stabilization_steps: list[str]
    confidence_score: float

class PulseDecision(BaseModel):
    decision_id: str
    decision_title: str
    status: str               # "FRESH" | "STABLE" | "AGING" | "STALE" | "CRITICAL_REEVALUATION"
    freshness_score: int
    original_reasoning: str
    what_changed: str
    current_ecosystem_state: str
    modern_alternatives: list[str]
    assumption_validity: str
    reevaluation_needed: bool
    risk_summary: str
    supporting_signals: list[str]
    confidence_score: float

class PulseOverallSummary(BaseModel):
    overall_freshness_score: int
    aging_decision_count: int
    stale_decision_count: int
    critical_decision_count: int
    summary: str

class PulseReport(BaseModel):
    overall_summary: PulseOverallSummary
    decisions: list[PulseDecision]

class KnowledgeCore(BaseModel):
    repo_url: str
    analyzed_at: str      # ISO timestamp
    decision_atoms: list[DecisionAtom]
    assumptions: list[Assumption]
    failure_memory: list[FailureRecord]
    ghost_decisions: list[GhostDecision]
    regretted_decisions: list[RegrettedDecision] = []
    orphaned_architecture: list[OrphanedArchitecture] = []
    pulse_report: PulseReport | None = None
    languages_detected: list[str] = []
    translated_artifact_count: int = 0
    language_distribution: dict = {}
    translation_enabled: bool = False
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