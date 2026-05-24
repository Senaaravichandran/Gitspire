import unittest

from core.parser import parse_knowledge_core


class ParseKnowledgeCoreTests(unittest.TestCase):

	def test_parses_extended_analysis_surfaces(self):
		core = parse_knowledge_core(
			"https://github.com/example/repo",
			{
				"summary": "Repository summary.",
				"decision_atoms": [
					{
						"id": "da_001",
						"decision": "Use background jobs",
						"reasoning": "Avoid blocking requests.",
						"evidence": ["commit:abc1234"],
						"confidence": 0.8,
					}
				],
				"assumptions": [
					{
						"id": "as_001",
						"statement": "Redis is available",
						"risk_level": "critical",
						"depends_on": [],
					}
				],
				"failure_memory": [
					{
						"approach": "Synchronous fan-out",
						"reason_failed": "Timeouts under load",
						"evidence": ["issue:#12"],
					}
				],
				"ghost_decisions": [
					{
						"location": "core/tasks.py:42",
						"observation": "Retry count is hard-coded",
						"possible_reasons": ["Historic infra limit"],
					}
				],
				"regretted_decisions": [
					{
						"title": "Custom retry queue",
						"original_decision": "Build a queue instead of using Celery",
						"why_it_exists": "Keep dependencies low early on",
						"regret_signals": ["commit:def5678", "issue:#9"],
						"emotional_evidence": "Frequent cleanup commits around the queue",
						"architectural_consequences": "Operational edge cases keep leaking into the API layer",
						"current_risk_level": "high",
						"confidence_score": 0.67,
					}
				],
				"orphaned_architecture": [
					{
						"decision_title": "In-house metrics collector",
						"subsystem": "observability",
						"original_author": "alice",
						"last_seen_activity": "2024-02-10",
						"active_status": "departed",
						"criticality": "high",
						"orphan_risk": "critical",
						"why_dangerous": "No active maintainer for critical alerts path",
						"hidden_assumptions": ["Collector process is always running"],
						"suggested_stabilization_steps": ["Document ownership", "Add health probes"],
						"confidence_score": 0.73,
					}
				],
				"pulse_report": {
					"overall_summary": {
						"overall_freshness_score": 71,
						"aging_decision_count": 2,
						"stale_decision_count": 1,
						"critical_decision_count": 1,
						"summary": "Several decisions need review.",
					},
					"decisions": [
						{
							"decision_id": "da_001",
							"decision_title": "Use background jobs",
							"status": "AGING",
							"freshness_score": 62,
							"original_reasoning": "Keep request latency predictable",
							"what_changed": "Traffic patterns shifted",
							"current_ecosystem_state": "Hosted queues are cheaper",
							"modern_alternatives": ["Managed task queues"],
							"assumption_validity": "Still mostly valid",
							"reevaluation_needed": True,
							"risk_summary": "Current workers are hard to scale",
							"supporting_signals": ["worker incidents rising"],
							"confidence_score": 0.64,
						}
					],
				},
			},
			{
				"languages_detected": ["en", "ja"],
				"translated_artifact_count": 3,
				"language_distribution": {"en": 4, "ja": 3},
				"translation_enabled": True,
			},
		)

		self.assertEqual(core.summary, "Repository summary.")
		self.assertEqual(len(core.regretted_decisions), 1)
		self.assertEqual(core.regretted_decisions[0].title, "Custom retry queue")
		self.assertEqual(len(core.orphaned_architecture), 1)
		self.assertEqual(core.orphaned_architecture[0].active_status, "departed")
		self.assertIsNotNone(core.pulse_report)
		self.assertEqual(core.pulse_report.overall_summary.overall_freshness_score, 71)
		self.assertEqual(core.pulse_report.decisions[0].status, "AGING")
		self.assertEqual(core.languages_detected, ["en", "ja"])
		self.assertTrue(core.translation_enabled)

	def test_falls_back_for_malformed_optional_surfaces(self):
		core = parse_knowledge_core(
			"https://github.com/example/repo",
			{
				"summary": 123,
				"decision_atoms": "bad-shape",
				"regretted_decisions": "bad-shape",
				"orphaned_architecture": [
					{
						"decision_title": "Legacy cron",
						"subsystem": "jobs",
					}
				],
				"pulse_report": {
					"overall_summary": "bad-shape",
					"decisions": "bad-shape",
				},
			},
		)

		self.assertEqual(core.summary, "123")
		self.assertEqual(core.decision_atoms, [])
		self.assertEqual(core.regretted_decisions, [])
		self.assertEqual(len(core.orphaned_architecture), 1)
		self.assertEqual(core.orphaned_architecture[0].decision_title, "Legacy cron")
		self.assertIsNone(core.pulse_report)


if __name__ == "__main__":
	unittest.main()
