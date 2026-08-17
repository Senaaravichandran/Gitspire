import asyncio
import json
import os
import unittest

from fastapi.testclient import TestClient
from starlette.requests import Request

os.environ.setdefault("MISTRAL", "test-key")

from main import app, generic_exception_handler


class ApplicationSecurityTests(unittest.TestCase):
    def test_health_response_includes_security_headers(self):
        response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertIn("camera=()", response.headers["permissions-policy"])

    def test_generic_error_does_not_expose_exception_message(self):
        request = Request({"type": "http", "method": "GET", "path": "/boom", "headers": []})
        response = asyncio.run(generic_exception_handler(request, RuntimeError("secret database detail")))
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(payload["error_code"], "INTERNAL_ERROR")
        self.assertNotIn("secret database detail", payload["error"])


if __name__ == "__main__":
    unittest.main()
