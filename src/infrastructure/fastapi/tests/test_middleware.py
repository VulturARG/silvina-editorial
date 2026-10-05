from unittest import TestCase

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.fastapi_app import create_app
from src.infrastructure.fastapi.src.middleware.request_timing_middleware import (
    RequestTimingMiddleware,
)

LOGGER_NAME = "src.infrastructure.fastapi.src.middleware.request_timing_middleware"


class TestRequestTimingMiddleware(TestCase):
    """Unit and integration tests for RequestTimingMiddleware in FastAPI."""

    def _build_test_application(self) -> FastAPI:
        application = FastAPI()
        application.add_middleware(RequestTimingMiddleware)

        @application.get("/ok")
        def ok_endpoint() -> dict[str, str]:
            return {"status": "ok"}

        @application.post("/echo")
        def echo_endpoint() -> dict[str, str]:
            return {"status": "echoed"}

        @application.get("/boom")
        def boom_endpoint() -> None:
            raise RuntimeError("Deliberate failure")

        return application

    def test_get_ok_logs_request_method_path_and_status(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            response = client.get("/ok")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("request method=GET path=/ok status=200", captured_logs.output[0])

    def test_post_logs_request_method_post(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            response = client.post("/echo")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("request method=POST path=/echo status=200", captured_logs.output[0])

    def test_unknown_route_logs_status_404(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            response = client.get("/nonexistent")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("request method=GET path=/nonexistent status=404", captured_logs.output[0])

    def test_failing_route_logs_status_500_and_client_receives_500(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            response = client.get("/boom")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("request method=GET path=/boom status=500", captured_logs.output[0])

    def test_duration_is_logged_in_milliseconds(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            client.get("/ok")

        self.assertEqual(len(captured_logs.output), 1)
        self.assertRegex(captured_logs.output[0], r"duration_ms=\d+\.\d")

    def test_query_string_is_excluded_from_log_and_path_is_clean(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            client.get("/ok?secret=abc123")

        self.assertEqual(len(captured_logs.output), 1)
        self.assertNotIn("secret", captured_logs.output[0])
        self.assertNotIn("abc123", captured_logs.output[0])
        self.assertIn("path=/ok", captured_logs.output[0])
        self.assertNotIn("path=/ok?", captured_logs.output[0])

    def test_response_body_and_status_are_unchanged_by_middleware(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=False)

        response = client.get("/ok")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_exception_is_propagated_when_raising_server_exceptions(self) -> None:
        application = self._build_test_application()
        client = TestClient(application, raise_server_exceptions=True)

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured_logs:
            with self.assertRaises(RuntimeError):
                client.get("/boom")

        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("request method=GET path=/boom status=500", captured_logs.output[0])

    def test_lifespan_events_do_not_log_request_records(self) -> None:
        application = self._build_test_application()

        with self.assertNoLogs(LOGGER_NAME, level="INFO"):
            with TestClient(application):
                pass

    def test_create_app_registers_request_timing_middleware(self) -> None:
        application = create_app(auto_open_browser=False)

        has_middleware = any(
            middleware.cls is RequestTimingMiddleware for middleware in application.user_middleware
        )

        self.assertTrue(has_middleware)
