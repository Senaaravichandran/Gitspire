from api.models.responses import (KnowledgeCore, DecisionAtom, Assumption,
                                    FailureRecord, GhostDecision,
                                    RegrettedDecision, OrphanedArchitecture,
                                    PulseReport, PulseOverallSummary, PulseDecision)
from datetime import datetime, timezone

def parse_knowledge_core(repo_url: str, gemini_response: dict, translation_metadata: dict | None = None) -> KnowledgeCore:
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

    regretted_decisions_raw = gemini_response.get("regretted_decisions", [])
    if not isinstance(regretted_decisions_raw, list):
        regretted_decisions_raw = []

    orphaned_architecture_raw = gemini_response.get("orphaned_architecture", [])
    if not isinstance(orphaned_architecture_raw, list):
        orphaned_architecture_raw = []

    pulse_report_raw = gemini_response.get("pulse_report")

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
            confidence=float(da.get("confidence", 0.5)),
            translated_source=da.get("translated_source"),
            source_language=da.get("source_language"),
            original_excerpt=da.get("original_excerpt"),
            translated_excerpt=da.get("translated_excerpt")
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

    regretted_decisions = []
    for rd in regretted_decisions_raw:
        if not isinstance(rd, dict):
            continue
        regretted_decisions.append(RegrettedDecision(
            title=str(rd.get("title", "Unknown decision")),
            original_decision=str(rd.get("original_decision", "")),
            why_it_exists=str(rd.get("why_it_exists", "")),
            regret_signals=rd.get("regret_signals", []) if isinstance(rd.get("regret_signals"), list) else [],
            emotional_evidence=str(rd.get("emotional_evidence", "")),
            architectural_consequences=str(rd.get("architectural_consequences", "")),
            current_risk_level=str(rd.get("current_risk_level", "low")),
            confidence_score=float(rd.get("confidence_score", 0.5))
        ))

    orphaned_architecture = []
    for oa in orphaned_architecture_raw:
        if not isinstance(oa, dict):
            continue
        orphaned_architecture.append(OrphanedArchitecture(
            decision_title=str(oa.get("decision_title", "Unknown decision")),
            subsystem=str(oa.get("subsystem", "")),
            original_author=str(oa.get("original_author", "")),
            last_seen_activity=str(oa.get("last_seen_activity", "")),
            active_status=str(oa.get("active_status", "inactive")),
            criticality=str(oa.get("criticality", "medium")),
            orphan_risk=str(oa.get("orphan_risk", "medium")),
            why_dangerous=str(oa.get("why_dangerous", "")),
            hidden_assumptions=oa.get("hidden_assumptions", []) if isinstance(oa.get("hidden_assumptions"), list) else [],
            suggested_stabilization_steps=oa.get("suggested_stabilization_steps", []) if isinstance(oa.get("suggested_stabilization_steps"), list) else [],
            confidence_score=float(oa.get("confidence_score", 0.5))
        ))

    pulse_report = None
    try:
        if isinstance(pulse_report_raw, dict):
            overall_raw = pulse_report_raw.get("overall_summary")
            decisions_raw = pulse_report_raw.get("decisions", [])
            if isinstance(overall_raw, dict) and isinstance(decisions_raw, list):
                overall_summary = PulseOverallSummary(
                    overall_freshness_score=int(overall_raw.get("overall_freshness_score", 0)),
                    aging_decision_count=int(overall_raw.get("aging_decision_count", 0)),
                    stale_decision_count=int(overall_raw.get("stale_decision_count", 0)),
                    critical_decision_count=int(overall_raw.get("critical_decision_count", 0)),
                    summary=str(overall_raw.get("summary", ""))
                )

                pulse_decisions = []
                for pd in decisions_raw:
                    if not isinstance(pd, dict):
                        continue
                    pulse_decisions.append(PulseDecision(
                        decision_id=str(pd.get("decision_id", "")),
                        decision_title=str(pd.get("decision_title", "")),
                        status=str(pd.get("status", "STABLE")),
                        freshness_score=int(pd.get("freshness_score", 0)),
                        original_reasoning=str(pd.get("original_reasoning", "")),
                        what_changed=str(pd.get("what_changed", "")),
                        current_ecosystem_state=str(pd.get("current_ecosystem_state", "")),
                        modern_alternatives=pd.get("modern_alternatives", []) if isinstance(pd.get("modern_alternatives"), list) else [],
                        assumption_validity=str(pd.get("assumption_validity", "")),
                        reevaluation_needed=bool(pd.get("reevaluation_needed", False)),
                        risk_summary=str(pd.get("risk_summary", "")),
                        supporting_signals=pd.get("supporting_signals", []) if isinstance(pd.get("supporting_signals"), list) else [],
                        confidence_score=float(pd.get("confidence_score", 0.5))
                    ))

                pulse_report = PulseReport(
                    overall_summary=overall_summary,
                    decisions=pulse_decisions
                )
    except Exception:
        pulse_report = None

    analyzed_at = datetime.now(timezone.utc).isoformat()

    translation_metadata = translation_metadata or {}

    return KnowledgeCore(
        repo_url=repo_url,
        analyzed_at=analyzed_at,
        decision_atoms=decision_atoms,
        assumptions=assumptions,
        failure_memory=failure_memory,
        ghost_decisions=ghost_decisions,
        regretted_decisions=regretted_decisions,
        orphaned_architecture=orphaned_architecture,
        pulse_report=pulse_report,
        languages_detected=translation_metadata.get("languages_detected", []),
        translated_artifact_count=translation_metadata.get("translated_artifact_count", 0),
        language_distribution=translation_metadata.get("language_distribution", {}),
        translation_enabled=translation_metadata.get("translation_enabled", False),
        summary=summary
    )