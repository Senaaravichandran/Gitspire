from api.models.responses import (KnowledgeCore, DecisionAtom, Assumption,
                                    FailureRecord, GhostDecision,
                                    RegrettedDecision, OrphanedArchitecture,
                                    PulseReport, PulseOverallSummary, PulseDecision)
from datetime import datetime, timezone


def _bounded_float(value, default: float = 0.5, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _bounded_int(value, default: int = 0, minimum: int = 0, maximum: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))

def build_fallback_analysis(repo_url: str, bundle: dict, translation_metadata: dict | None = None) -> KnowledgeCore:
    metadata = bundle.get("metadata", {}) if isinstance(bundle, dict) else {}
    key_files = bundle.get("key_files", {}) if isinstance(bundle, dict) else {}
    commits = bundle.get("commits", []) if isinstance(bundle, dict) else []
    issues = bundle.get("issues", []) if isinstance(bundle, dict) else []
    prs = bundle.get("pull_requests", []) if isinstance(bundle, dict) else []

    primary_language = metadata.get("language") or "unknown"
    description = metadata.get("description") or ""
    key_list = ", ".join(list(key_files.keys())[:5])
    summary_parts = [
        "Repository analysis complete.",
        f"Primary language: {primary_language}.",
        f"Description: {description}".strip(),
        f"Commits: {len(commits)}, issues: {len(issues)}, PRs: {len(prs)}.",
        f"Key files sampled: {key_list}." if key_list else "Key files sampled: none."
    ]
    summary = " ".join([p for p in summary_parts if p])

    decision_atoms = []
    decision_atoms.append(DecisionAtom(
        id="da_001",
        decision=f"Primary language is {primary_language}",
        reasoning=(
            "Derived from repository metadata, which GitHub infers from source file composition. "
            "This usually indicates the dominant ecosystem and tooling expected by contributors."
        ),
        evidence=[],
        confidence=0.6
    ))

    key_names = [name.lower() for name in key_files.keys()]
    if "package.json" in key_names:
        decision_atoms.append(DecisionAtom(
            id="da_002",
            decision="Uses Node.js tooling (package.json present)",
            reasoning=(
                "Detected package.json in key files, which is the standard Node.js dependency manifest. "
                "This implies a JavaScript/TypeScript toolchain and an npm/yarn/pnpm-based workflow."
            ),
            evidence=[],
            confidence=0.6
        ))

    if "requirements.txt" in key_names or "pyproject.toml" in key_names or "poetry.lock" in key_names:
        decision_atoms.append(DecisionAtom(
            id="da_003",
            decision="Uses Python dependencies (requirements.txt present)",
            reasoning=(
                "Detected Python dependency files, which are used to pin libraries for runtime and tooling. "
                "This suggests a pip/poetry workflow and Python-based build or runtime steps."
            ),
            evidence=[],
            confidence=0.6
        ))

    if "dockerfile" in key_names or "docker-compose.yml" in key_names or "docker-compose.yaml" in key_names:
        decision_atoms.append(DecisionAtom(
            id="da_004",
            decision="Uses containerization (Docker files present)",
            reasoning=(
                "Detected Docker configuration files, which usually define the runtime image and service graph. "
                "This suggests containerized deployment or a reproducible dev environment."
            ),
            evidence=[],
            confidence=0.6
        ))

    if any(".github/workflows" in name for name in key_files.keys()):
        decision_atoms.append(DecisionAtom(
            id="da_005",
            decision="Uses GitHub Actions CI/CD",
            reasoning=(
                "Detected workflow files under .github/workflows, which indicate CI automation. "
                "This implies build/test/deploy steps are codified and expected to run on push/PR."
            ),
            evidence=[],
            confidence=0.6
        ))

    if "readme.md" in key_names:
        decision_atoms.append(DecisionAtom(
            id="da_006",
            decision="Documentation-first onboarding (README present)",
            reasoning=(
                "README detected and typically used as the entrypoint for setup and usage instructions. "
                "Developers should treat it as the authoritative onboarding guide."
            ),
            evidence=[],
            confidence=0.5
        ))

    assumptions = [
        Assumption(
            id="as_001",
            statement="Repository metadata and GitHub APIs are available during analysis and CI.",
            risk_level="moderate",
            depends_on=[]
        ),
        Assumption(
            id="as_002",
            statement="Key files represent the primary tooling configuration for build and runtime.",
            risk_level="low",
            depends_on=[]
        )
    ]

    if "package.json" in key_names:
        assumptions.append(Assumption(
            id="as_003",
            statement="Node.js dependencies are installable and compatible",
            risk_level="moderate",
            depends_on=[]
        ))

    if "requirements.txt" in key_names or "pyproject.toml" in key_names:
        assumptions.append(Assumption(
            id="as_004",
            statement="Python dependencies are installable and compatible",
            risk_level="moderate",
            depends_on=[]
        ))

    if "dockerfile" in key_names or "docker-compose.yml" in key_names or "docker-compose.yaml" in key_names:
        assumptions.append(Assumption(
            id="as_005",
            statement="Container build context remains valid for deployment",
            risk_level="low",
            depends_on=[]
        ))

    failure_memory = []
    for commit in commits[:25]:
        message = str(commit.get("message", "")).lower()
        if "revert" in message or "rollback" in message:
            failure_memory.append(FailureRecord(
                approach="Reverted change",
                reason_failed=(
                    "Commit message indicates a rollback. This is a strong signal the prior change "
                    "introduced instability or behavior regressions."
                ),
                evidence=[]
            ))
            break

    ghost_decisions = [
        GhostDecision(
            location="unknown",
            observation=(
                "Repository structure implies implicit architectural choices that are not documented. "
                "This often happens when the README focuses on usage rather than design rationale."
            ),
            possible_reasons=[
                "Design decisions were made early and never recorded",
                "Architecture evolved incrementally without formal ADRs"
            ]
        )
    ]

    regretted_decisions = [
        RegrettedDecision(
            title="Limited architectural documentation",
            original_decision="Minimal design docs in repo",
            why_it_exists="Teams often prioritize feature delivery over formal documentation",
            regret_signals=["No ADRs detected in key files"],
            emotional_evidence="Onboarding relies on code reading and tribal knowledge",
            architectural_consequences="Harder to assess tradeoffs and evolution over time",
            current_risk_level="medium",
            confidence_score=0.4
        )
    ]

    orphaned_architecture = [
        OrphanedArchitecture(
            decision_title="Undocumented module boundaries",
            subsystem="repository root",
            original_author="unknown",
            last_seen_activity="unknown",
            active_status="active",
            criticality="medium",
            orphan_risk="medium",
            why_dangerous="Boundaries may shift without a source of truth, causing coupling drift.",
            hidden_assumptions=["Module boundaries match deployment boundaries"],
            suggested_stabilization_steps=[
                "Add a short architecture overview",
                "Document module responsibilities in README"
            ],
            confidence_score=0.4
        )
    ]

    pulse_report = PulseReport(
        overall_summary=PulseOverallSummary(
            overall_freshness_score=65,
            aging_decision_count=1,
            stale_decision_count=0,
            critical_decision_count=0,
            summary=(
                "Heuristic pulse indicates a mostly stable architecture with a small amount of documentation drift. "
                "Key decisions appear current but under-documented."
            )
        ),
        decisions=[
            PulseDecision(
                decision_id="da_001",
                decision_title="Primary language selection",
                status="STABLE",
                freshness_score=70,
                original_reasoning="Language chosen based on ecosystem fit and contributor familiarity.",
                what_changed="Tooling ecosystems evolve, requiring occasional dependency refresh.",
                current_ecosystem_state="Active and widely supported.",
                modern_alternatives=["Consider minor version upgrades"],
                assumption_validity="Still valid with ongoing maintenance.",
                reevaluation_needed=False,
                risk_summary="Low risk if dependencies stay updated.",
                supporting_signals=["Recent commits present"],
                confidence_score=0.5
            )
        ]
    )

    analyzed_at = datetime.now(timezone.utc).isoformat()
    translation_metadata = translation_metadata or {}
    if not translation_metadata.get("languages_detected"):
        translation_metadata["languages_detected"] = [primary_language if primary_language != "unknown" else "en"]

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
            confidence=_bounded_float(da.get("confidence")),
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
            confidence_score=_bounded_float(rd.get("confidence_score"))
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
            confidence_score=_bounded_float(oa.get("confidence_score"))
        ))

    pulse_report = None
    try:
        if isinstance(pulse_report_raw, dict):
            overall_raw = pulse_report_raw.get("overall_summary")
            decisions_raw = pulse_report_raw.get("decisions", [])
            if isinstance(overall_raw, dict) and isinstance(decisions_raw, list):
                overall_summary = PulseOverallSummary(
                    overall_freshness_score=_bounded_int(overall_raw.get("overall_freshness_score")),
                    aging_decision_count=_bounded_int(overall_raw.get("aging_decision_count"), maximum=10000),
                    stale_decision_count=_bounded_int(overall_raw.get("stale_decision_count"), maximum=10000),
                    critical_decision_count=_bounded_int(overall_raw.get("critical_decision_count"), maximum=10000),
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
                        freshness_score=_bounded_int(pd.get("freshness_score")),
                        original_reasoning=str(pd.get("original_reasoning", "")),
                        what_changed=str(pd.get("what_changed", "")),
                        current_ecosystem_state=str(pd.get("current_ecosystem_state", "")),
                        modern_alternatives=pd.get("modern_alternatives", []) if isinstance(pd.get("modern_alternatives"), list) else [],
                        assumption_validity=str(pd.get("assumption_validity", "")),
                        reevaluation_needed=bool(pd.get("reevaluation_needed", False)),
                        risk_summary=str(pd.get("risk_summary", "")),
                        supporting_signals=pd.get("supporting_signals", []) if isinstance(pd.get("supporting_signals"), list) else [],
                        confidence_score=_bounded_float(pd.get("confidence_score"))
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
