from api.models.responses import (KnowledgeCore, DecisionAtom, Assumption, 
                                    FailureRecord, GhostDecision)
from datetime import datetime, timezone

def parse_knowledge_core(repo_url: str, gemini_response: dict) -> KnowledgeCore:
    # Handle base missing properties
    summary = gemini_response.get("summary", "No summary provided.")
    if not isinstance(summary, str):
        summary = str(summary)
        
    decision_atoms_raw = gemini_response.get("decision_atoms", [])
    if not isinstance(decision_atoms_raw, list):
        decision_atoms_raw = []
        
    assumptions_raw = gemini_response.get("assumptions", [])
    if not isinstance(assumptions_raw, list):
        assumptions_raw = []
        
    failure_memory_raw = gemini_response.get("failure_memory", [])
    if not isinstance(failure_memory_raw, list):
        failure_memory_raw = []
        
    ghost_decisions_raw = gemini_response.get("ghost_decisions", [])
    if not isinstance(ghost_decisions_raw, list):
        ghost_decisions_raw = []

    # Parse Decision Atoms
    decision_atoms = []
    for i, da in enumerate(decision_atoms_raw):
        if not isinstance(da, dict):
            continue
        decision_atoms.append(DecisionAtom(
            id=da.get("id", f"da_{i:03d}"),
            decision=str(da.get("decision", "Unknown decision")),
            reasoning=str(da.get("reasoning", "No reasoning provided")),
            evidence=da.get("evidence", []) if isinstance(da.get("evidence"), list) else [],
            confidence=float(da.get("confidence", 0.5))
        ))

    # Parse Assumptions
    assumptions = []
    for i, asmp in enumerate(assumptions_raw):
        if not isinstance(asmp, dict):
            continue
        assumptions.append(Assumption(
            id=asmp.get("id", f"as_{i:03d}"),
            statement=str(asmp.get("statement", "Unknown assumption")),
            risk_level=str(asmp.get("risk_level", "moderate")),
            depends_on=asmp.get("depends_on", []) if isinstance(asmp.get("depends_on"), list) else []
        ))

    # Parse Failure Memory
    failure_memory = []
    for fm in failure_memory_raw:
        if not isinstance(fm, dict):
            continue
        failure_memory.append(FailureRecord(
            approach=str(fm.get("approach", "Unknown approach")),
            reason_failed=str(fm.get("reason_failed", "Unknown failure reason")),
            evidence=fm.get("evidence", []) if isinstance(fm.get("evidence"), list) else []
        ))

    # Parse Ghost Decisions
    ghost_decisions = []
    for gd in ghost_decisions_raw:
        if not isinstance(gd, dict):
            continue
        ghost_decisions.append(GhostDecision(
            location=str(gd.get("location", "Unknown location")),
            observation=str(gd.get("observation", "Unknown observation")),
            possible_reasons=gd.get("possible_reasons", []) if isinstance(gd.get("possible_reasons"), list) else []
        ))

    analyzed_at = datetime.now(timezone.utc).isoformat()

    return KnowledgeCore(
        repo_url=repo_url,
        analyzed_at=analyzed_at,
        decision_atoms=decision_atoms,
        assumptions=assumptions,
        failure_memory=failure_memory,
        ghost_decisions=ghost_decisions,
        summary=summary
    )