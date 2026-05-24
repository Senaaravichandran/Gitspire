PROMPT_ARCHAEOLOGY = """
System context: You are a software archaeology system given a complete 
GitHub repository artifact bundle.
Task: Reconstruct the invisible why-layer — reasoning behind every 
non-obvious architectural decision not explicitly documented.
Input:
{archaeology_context}

Output: JSON object with exact schema:
{{
  "summary": "2-3 sentence plain English summary of what this codebase does",
  "decision_atoms": [
    {{
      "id": "da_001",
      "decision": "Short description of architectural choice",
      "reasoning": "Specific inferred reasoning with evidence citations",
      "evidence": ["commit:abc1234", "issue:#42", "pr:#7"],
      "confidence": 0.85,
      "translated_source": true,
      "source_language": "ja",
      "original_excerpt": "original text",
      "translated_excerpt": "translated text"
    }}
  ],
  "assumptions": [
    {{
      "id": "as_001",
      "statement": "What must remain true for this codebase to function",
      "risk_level": "critical",
      "depends_on": []
    }}
  ],
  "failure_memory": [
    {{
      "approach": "What was tried",
      "reason_failed": "Why it failed, inferred from revert commits or issue discussions",
      "evidence": ["commit:abc1234"]
    }}
  ],
  "ghost_decisions": [
    {{
      "location": "src/auth/middleware.py:47",
      "observation": "What looks intentional but has zero documentation trail",
      "possible_reasons": ["Reason 1", "Reason 2"]
    }}
  ],
  "regretted_decisions": [
    {{
      "title": "Short label for the regretted decision",
      "original_decision": "What was chosen originally",
      "why_it_exists": "Constraints or context that led to it",
      "regret_signals": ["commit:abc1234", "issue:#42"],
      "emotional_evidence": "Inferred discomfort based on patterns",
      "architectural_consequences": "Downstream impact",
      "current_risk_level": "low",
      "confidence_score": 0.5
    }}
  ],
  "orphaned_architecture": [
    {{
      "decision_title": "Decision atom title",
      "subsystem": "Area or module impacted",
      "original_author": "Contributor handle or name",
      "last_seen_activity": "ISO date or short description",
      "active_status": "inactive",
      "criticality": "medium",
      "orphan_risk": "medium",
      "why_dangerous": "Why this is risky now",
      "hidden_assumptions": ["assumption A", "assumption B"],
      "suggested_stabilization_steps": ["step 1", "step 2"],
      "confidence_score": 0.5
    }}
  ],
  "pulse_report": {{
    "overall_summary": {{
      "overall_freshness_score": 0,
      "aging_decision_count": 0,
      "stale_decision_count": 0,
      "critical_decision_count": 0,
      "summary": ""
    }},
    "decisions": [
      {{
        "decision_id": "da_001",
        "decision_title": "Decision atom title",
        "status": "STABLE",
        "freshness_score": 75,
        "original_reasoning": "Original rationale",
        "what_changed": "Ecosystem changes since then",
        "current_ecosystem_state": "Todays state",
        "modern_alternatives": ["Alt A", "Alt B"],
        "assumption_validity": "Whether assumptions still hold",
        "reevaluation_needed": false,
        "risk_summary": "Summary of risk",
        "supporting_signals": ["signal 1", "signal 2"],
        "confidence_score": 0.5
      }}
    ]
  }}
}}

Rules:
- Return ONLY the JSON. No markdown fences, no preamble.
- Be specific. "For performance reasons" without evidence is not acceptable.
- Evidence format must be "commit:SHA", "issue:#N", or "pr:#N".
- confidence is float 0.0–1.0
- decision_atoms: cover 5-10 most architecturally significant decisions
- ghost_decisions: only choices with zero documentation trail
- regretted_decisions and orphaned_architecture are optional but must be arrays (empty if none)
- pulse_report is optional; if present, it must include overall_summary and decisions
- decision_atoms may include optional translation metadata fields when sourced from translated artifacts
- If the repo has no non-obvious decisions, say so in summary, return empty arrays
"""

PROMPT_WHY_QUERY = """
Context: You are Gitspire, architectural memory system for repo "{repo_url}"
Task: Answer the question drawing only from the knowledge core provided

Input Knowledge Core:
{knowledge_core_json}

Question:
{question}

Output JSON: 
{{ 
  "answer": "markdown answer with specific citations", 
  "citations": ["commit:abc", "issue:#42"], 
  "confidence": "high" 
}}

Rule: 
- Return ONLY JSON. No markdown fences.
- If the knowledge core does not contain enough information to answer, say so explicitly rather than hallucinating.
- Confidence must be "high", "medium", or "low".
"""

PROMPT_ASSUMPTION_ALARM = """
Context: You are Gitspire's assumption violation detector
Task: Determine if the code snippet violates any extracted assumptions

Input Assumptions:
{assumptions_json}

Code Snippet from {repo_url}:
{code_snippet}

Output JSON: 
{{ 
  "violation_detected": true, 
  "violated_assumption_id": "as_001", 
  "explanation": "why this is or is not a violation",
  "new_assumption_introduced": "description or null" 
}}

Rule: 
- Return ONLY JSON. No markdown fences.
- No violation = violation_detected false, violated_assumption_id null.
"""

PROMPT_ONBOARDING = """
Context: You are Gitspire's onboarding path generator for {repo_url}
Task: Generate a ranked checklist of things a new developer must understand 
      before safely implementing the requested feature. Rank by danger — 
      most likely to break first.

Input Knowledge Core:
{knowledge_core_json}

Feature Request:
{feature_description}

Output JSON: 
{{ 
  "checklist": [
    {{
      "priority": 1, 
      "topic": "str", 
      "why": "str", 
      "evidence": "str"
    }}
  ],
  "warning_count": 3 
}}
warning_count = number of checklist items involving critical-risk assumptions.
Rule: Return ONLY JSON. No markdown fences.
"""
