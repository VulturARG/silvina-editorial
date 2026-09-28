from unittest import TestCase

from fastapi import APIRouter
from fastapi.testclient import TestClient

from src.domain.exceptions.base_src_error import (
    SrcBaseNotAuthorized,
    SrcBaseWarning,
)
from src.domain.exceptions.document_errors import (
    DocumentNotFound,
    DocumentTooLarge,
    DocumentUnreadable,
)
from src.infrastructure.fastapi.fastapi_app import create_app


class TestFastApiExceptionHandlers(TestCase):
    """Integration tests for FastAPI application setup and exception handlers."""

    def setUp(self) -> None:
        self.app = create_app(auto_open_browser=False)

        # Test router to raise specific exceptions
        self.router = APIRouter(prefix="/test-exceptions")

        @self.router.get("/unreadable")
        def raise_unreadable():
            raise DocumentUnreadable()

        @self.router.get("/too-large")
        def raise_too_large():
            raise DocumentTooLarge()

        @self.router.get("/not-found")
        def raise_not_found():
            raise DocumentNotFound()

        @self.router.get("/not-authorized")
        def raise_not_authorized():
            raise SrcBaseNotAuthorized()

        @self.router.get("/warning")
        def raise_warning():
            raise SrcBaseWarning()

        @self.router.get("/unexpected")
        def raise_unexpected():
            raise RuntimeError("Unexpected pipeline crash")

        self.app.include_router(self.router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_document_unreadable_returns_400_and_error_partial(self) -> None:
        response = self.client.get("/test-exceptions/unreadable")

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document could not be read.", response.text)
        self.assertIn("Error de validación:", response.text)
        self.assertIn("error-callout", response.text)

    def test_document_too_large_returns_400_and_error_partial(self) -> None:
        response = self.client.get("/test-exceptions/too-large")

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document file exceeds the maximum allowed size.", response.text)
        self.assertIn("Error de validación:", response.text)
        self.assertIn("error-callout", response.text)

    def test_src_base_not_found_returns_404_and_error_partial(self) -> None:
        response = self.client.get("/test-exceptions/not-found")

        self.assertEqual(response.status_code, 404)
        self.assertIn("The document file could not be found.", response.text)
        self.assertIn("Error de validación:", response.text)
        self.assertIn("error-callout", response.text)

    def test_src_base_not_authorized_returns_403_and_error_partial(self) -> None:
        response = self.client.get("/test-exceptions/not-authorized")

        self.assertEqual(response.status_code, 403)
        self.assertIn("Error de validación:", response.text)
        self.assertIn("error-callout", response.text)

    def test_src_base_warning_returns_400_and_error_partial(self) -> None:
        response = self.client.get("/test-exceptions/warning")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Error de validación:", response.text)
        self.assertIn("error-callout", response.text)

    def test_unexpected_exception_returns_500_and_error_partial_without_traceback(self) -> None:
        response = self.client.get("/test-exceptions/unexpected")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Error al procesar el documento: Unexpected pipeline crash", response.text)
        self.assertNotIn("Traceback (most recent call last)", response.text)
        self.assertIn("error-callout", response.text)

    def test_static_files_are_mounted_and_accessible(self) -> None:
        response = self.client.get("/static/css/silvina.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn("--primary-color", response.text)
