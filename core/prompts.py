PROMPT_ARCHAEOLOGY = """Extract core architecture decisions from repo. JSON only:

{archaeology_context}

{{"summary": "desc", "decision_atoms": [{{"id": "d1", "decision": "choice", "reasoning": "why", "evidence": ["commit:a"], "confidence": 0.8}}], "assumptions": [{{"id": "a1", "statement": "fact", "risk_level": "high", "depends_on": []}}], "failure_memory": [], "ghost_decisions": [], "regretted_decisions": [], "orphaned_architecture": [], "pulse_report": null}}"""

PROMPT_WHY_QUERY = """Answer using knowledge: {knowledge_core_json}

Q: {question}

{{"answer": "text", "citations": [], "confidence": "high"}}"""

PROMPT_ASSUMPTION_ALARM = """Check violation:
Assumptions: {assumptions_json}
Code: {code_snippet}

{{"violation_detected": false, "violated_assumption_id": null, "explanation": "ok", "new_assumption_introduced": null}}"""

PROMPT_ONBOARDING = """Checklist for {repo_url}:
Knowledge: {knowledge_core_json}
Feature: {feature_description}

{{"checklist": [{{"priority": 1, "topic": "x", "why": "y", "evidence": "z"}}], "warning_count": 0}}"""
