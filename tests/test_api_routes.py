import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

os.environ.setdefault("MISTRAL", "test-key")
os.environ.setdefault("FIREBASE_DATABASE_URL", "https://example.firebaseio.com")

from api.models.responses import KnowledgeCore
from api.routes import alarm, analyze, onboard, query


def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": str(exc.detail), "error_code": "HTTP_ERROR"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc), "error_code": "INTERNAL_ERROR"},
        )

    app.include_router(analyze.router, prefix="/api")
    app.include_router(query.router, prefix="/api")
    app.include_router(alarm.router, prefix="/api")
    app.include_router(onboard.router, prefix="/api")
    return app


def sample_knowledge_core_dict() -> dict:
    return {
        "repo_url": "https://github.com/example/repo",
        "analyzed_at": "2026-05-25T00:00:00+00:00",
        "decision_atoms": [
            {
                "id": "da_001",
                "decision": "Queue long-running jobs",
                "reasoning": "Protect request latency during spikes.",
                "evidence": ["commit:abc1234"],
                "confidence": 0.82,
            }
        ],
        "assumptions": [
            {
                "id": "as_001",
                "statement": "Workers can reach Redis at all times.",
                "risk_level": "critical",
                "depends_on": [],
            }
        ],
        "failure_memory": [
            {
                "approach": "Inline fan-out",
                "reason_failed": "Timed out under heavy load.",
                "evidence": ["issue:#18"],
            }
        ],
        "ghost_decisions": [
            {
                "location": "core/tasks.py:42",
                "observation": "Retry count is hard-coded with no explanation.",
                "possible_reasons": ["Historic infrastructure limit"],
            }
        ],
        "regretted_decisions": [
            {
                "title": "Custom retry queue",
                "original_decision": "Build a custom queue instead of a managed worker stack.",
                "why_it_exists": "Early dependency minimization.",
                "regret_signals": ["commit:def5678"],
                "emotional_evidence": "Repeated cleanup commits around queue behavior.",
                "architectural_consequences": "Queue edge cases leak into API code paths.",
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
                "why_dangerous": "Critical alerts depend on a subsystem with no active maintainer.",
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
                "summary": "Several important architectural decisions are aging.",
            },
            "decisions": [
                {
                    "decision_id": "da_001",
                    "decision_title": "Queue long-running jobs",
                    "status": "AGING",
                    "freshness_score": 62,
                    "original_reasoning": "Protect request latency during spikes.",
                    "what_changed": "Managed queues became cheaper and easier to operate.",
                    "current_ecosystem_state": "Hosted queue services fit the traffic model better.",
                    "modern_alternatives": ["Managed task queues"],
                    "assumption_validity": "Still valid, but less compelling than before.",
                    "reevaluation_needed": True,
                    "risk_summary": "Current workers are increasingly brittle to scale events.",
                    "supporting_signals": ["worker incidents rising"],
                    "confidence_score": 0.64,
                }
            ],
        },
        "languages_detected": ["en"],
        "translated_artifact_count": 0,
        "language_distribution": {"en": 1},
        "translation_enabled": False,
        "summary": "Sample summary for HTTP route tests.",
    }


class ApiRouteTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_test_app()

    def setUp(self):
        self.client = TestClient(self.app)
        self.core_dict = sample_knowledge_core_dict()
        self.core_model = KnowledgeCore.model_validate(self.core_dict)

    def test_analyze_endpoint_returns_extended_knowledge_core(self):
        with (
            patch.object(analyze.analyze_rate_limiter, "is_allowed", return_value=True),
            patch.object(analyze.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=None)),
            patch.object(analyze.github_client, "parse_repo_url", return_value=("example", "repo")),
            patch.object(
                analyze.github_client,
                "fetch_repository_bundle",
                new=AsyncMock(return_value={"metadata": {"description": "demo"}, "commits": [{"sha": "abc"}]}),
            ),
            patch.object(
                analyze.github_client,
                "build_archaeology_context",
                return_value=("context", {"languages_detected": ["en"], "translated_artifact_count": 0, "language_distribution": {"en": 1}, "translation_enabled": False}),
            ),
            patch.object(analyze.gemini_client, "analyze_repository", new=AsyncMock(return_value={"summary": self.core_dict["summary"]})),
            patch.object(analyze, "parse_knowledge_core", return_value=self.core_model),
            patch.object(analyze.firebase_client, "save_knowledge_core", new=AsyncMock()),
        ):
            response = self.client.post(
                "/api/analyze",
                json={"repo_url": "https://github.com/example/repo", "force_refresh": False},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertFalse(payload["cached"])
        self.assertIn("regretted_decisions", payload["knowledge_core"])
        self.assertIn("orphaned_architecture", payload["knowledge_core"])
        self.assertIn("pulse_report", payload["knowledge_core"])

    def test_analyze_endpoint_rejects_invalid_url(self):
        with patch.object(analyze.analyze_rate_limiter, "is_allowed", return_value=True):
            response = self.client.post(
                "/api/analyze",
                json={"repo_url": "https://example.com/not-github", "force_refresh": False},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "INVALID_URL")

    def test_analyze_endpoint_canonicalizes_git_url(self):
        cached_core = sample_knowledge_core_dict()
        with (
            patch.object(analyze.analyze_rate_limiter, "is_allowed", return_value=True),
            patch.object(analyze.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=cached_core)) as get_core,
        ):
            response = self.client.post(
                "/api/analyze",
                json={"repo_url": "https://www.github.com/example/repo.git/", "force_refresh": False},
            )

        self.assertEqual(response.status_code, 200)
        get_core.assert_awaited_once_with("https://github.com/example/repo")

    def test_analyze_endpoint_accepts_legacy_cached_assumptions_without_depends_on(self):
        legacy_cached_core = sample_knowledge_core_dict()
        legacy_cached_core["assumptions"] = [
            {
                "id": "as_legacy",
                "statement": "Legacy cached assumption without dependency links.",
                "risk_level": "moderate",
            }
        ]

        with (
            patch.object(analyze.analyze_rate_limiter, "is_allowed", return_value=True),
            patch.object(analyze.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=legacy_cached_core)),
        ):
            response = self.client.post(
                "/api/analyze",
                json={"repo_url": "https://github.com/example/repo", "force_refresh": False},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["cached"])
        self.assertEqual(payload["knowledge_core"]["assumptions"][0]["depends_on"], [])

    def test_query_endpoint_returns_answer_with_citations(self):
        with (
            patch.object(query.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=self.core_dict)),
            patch.object(query.firebase_client, "get_cached_query", new=AsyncMock(return_value=None)),
            patch.object(
                query.gemini_client,
                "answer_query",
                new=AsyncMock(return_value={"answer": "Because the queue protects latency.", "citations": ["commit:abc1234"], "confidence": "high"}),
            ),
            patch.object(query.firebase_client, "save_query_cache", new=AsyncMock()),
        ):
            response = self.client.post(
                "/api/query",
                json={"repo_url": self.core_dict["repo_url"], "question": "Why use the queue?"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["confidence"], "high")
        self.assertEqual(payload["citations"], ["commit:abc1234"])

    def test_alarm_endpoint_maps_violated_assumption(self):
        with (
            patch.object(alarm.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=self.core_dict)),
            patch.object(
                alarm.gemini_client,
                "check_alarm",
                new=AsyncMock(
                    return_value={
                        "violation_detected": True,
                        "violated_assumption_id": "as_001",
                        "explanation": "Redis was bypassed.",
                        "new_assumption_introduced": "A local queue is available.",
                    }
                ),
            ),
        ):
            response = self.client.post(
                "/api/alarm",
                json={"repo_url": self.core_dict["repo_url"], "code_snippet": "client = InMemoryQueue()"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["violation_detected"])
        self.assertEqual(payload["violated_assumption"]["id"], "as_001")
        self.assertEqual(payload["new_assumption_introduced"], "A local queue is available.")

    def test_onboard_endpoint_returns_ranked_checklist(self):
        with (
            patch.object(onboard.firebase_client, "get_knowledge_core", new=AsyncMock(return_value=self.core_dict)),
            patch.object(
                onboard.gemini_client,
                "generate_onboarding",
                new=AsyncMock(
                    return_value={
                        "checklist": [
                            {
                                "priority": 1,
                                "topic": "Queue ownership",
                                "why": "The queue is a critical architectural decision.",
                                "evidence": "commit:abc1234",
                            }
                        ],
                        "warning_count": 1,
                    }
                ),
            ),
        ):
            response = self.client.post(
                "/api/onboard",
                json={"repo_url": self.core_dict["repo_url"], "feature_description": "Add background job retries"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["warning_count"], 1)
        self.assertEqual(payload["checklist"][0]["topic"], "Queue ownership")


if __name__ == "__main__":
    unittest.main()
