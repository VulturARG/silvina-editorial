from io import BytesIO
from unittest import TestCase

from fastapi.testclient import TestClient

from src.infrastructure.fastapi.fastapi_app import create_app


class TestHtmxErrorHandling(TestCase):
    """Unit and integration tests for HTMX error handling script and response behavior."""

    def setUp(self) -> None:
        self.app = create_app(auto_open_browser=False)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_index_page_contains_htmx_error_handling_script_after_htmx(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        expected_script_tag = '<script src="/static/js/htmx_error_handling.js"></script>'
        self.assertIn(expected_script_tag, response.text)
        htmx_script_index = response.text.index("https://unpkg.com/htmx.org")
        error_script_index = response.text.index(expected_script_tag)
        self.assertGreater(error_script_index, htmx_script_index)

    def test_static_file_htmx_error_handling_serves_javascript_with_expected_tokens(self) -> None:
        response = self.client.get("/static/js/htmx_error_handling.js")

        self.assertEqual(response.status_code, 200)
        content_type = response.headers.get("content-type", "")
        self.assertIn("javascript", content_type.lower())
        self.assertIn("htmx:beforeSwap", response.text)
        self.assertIn("shouldSwap", response.text)
        self.assertIn("isError", response.text)
        self.assertIn("text/html", response.text)

    def test_static_file_registers_listener_on_document(self) -> None:
        response = self.client.get("/static/js/htmx_error_handling.js")

        self.assertEqual(response.status_code, 200)
        self.assertIn('document.addEventListener("htmx:beforeSwap"', response.text)

    def test_application_error_response_returns_html_with_error_callout(self) -> None:
        payload = {"file": ("invalid_document.txt", BytesIO(b"invalid content"), "text/plain")}
        response = self.client.post("/analyze", files=payload)

        self.assertGreaterEqual(response.status_code, 400)
        content_type = response.headers.get("content-type", "")
        self.assertTrue(content_type.startswith("text/html"))
        self.assertIn("error-callout", response.text)
