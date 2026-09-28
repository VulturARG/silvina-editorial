from io import BytesIO
import os
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.infrastructure.env_config import EnvConfig
from src.infrastructure.fastapi.fastapi_app import create_app
from src.infrastructure.fastapi.src.config.dependencies import (
    get_analyze_document_use_case,
    get_env_config,
    get_export_report_use_case,
    get_json_export_report_use_case,
    get_reports_directory,
    get_templates,
)
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestFastApiRoutes(TestCase):
    """Unit and integration tests for FastAPI routes (page, analyze, reports)."""

    def setUp(self) -> None:
        self.temp_reports_dir = tempfile.TemporaryDirectory()
        self.reports_dir = Path(self.temp_reports_dir.name)

        self.mock_analyze = MagicMock()
        self.mock_export = MagicMock()
        self.mock_json_export = MagicMock()

        self.app = create_app(auto_open_browser=False)
        self.app.dependency_overrides[get_reports_directory] = lambda: self.reports_dir
        self.app.dependency_overrides[get_analyze_document_use_case] = lambda: self.mock_analyze
        self.app.dependency_overrides[get_export_report_use_case] = lambda: self.mock_export
        self.app.dependency_overrides[get_json_export_report_use_case] = lambda: (
            self.mock_json_export
        )

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        self.temp_reports_dir.cleanup()

    def test_get_index_page_returns_200_and_form(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Silvina - Asistente Editorial EUMIC", response.text)
        self.assertIn('hx-post="/analyze"', response.text)
        self.assertIn("<form", response.text)

    def test_post_analyze_success(self) -> None:
        fake_report = ReportFixtures.make_report_input_dto()
        captured_paths: list[Path] = []

        def fake_execute(*args, **kwargs):
            doc_path = kwargs.get("document_path") or (args[0] if args else "")
            path = Path(doc_path)
            captured_paths.append(path)
            self.assertTrue(path.exists(), "Temporary upload file should exist during execution")
            return fake_report

        self.mock_analyze.execute.side_effect = fake_execute

        file_payload = b"valid docx binary content for test"
        response = self.client.post(
            "/analyze",
            files={
                "file": (
                    "test.docx",
                    BytesIO(file_payload),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(fake_report.document_content.title, response.text)
        self.assertIn("/reports/test_analisis.docx", response.text)
        self.assertIn("/reports/test_analisis.json", response.text)

        self.assertEqual(len(captured_paths), 1)
        self.assertFalse(captured_paths[0].exists(), "Temporary upload file should be unlinked")

        expected_word_path = str(self.reports_dir / "test_analisis.docx")
        expected_json_path = str(self.reports_dir / "test_analisis.json")
        self.mock_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=expected_word_path
        )
        self.mock_json_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=expected_json_path
        )

    def test_post_analyze_invalid_type_returns_400(self) -> None:
        response = self.client.post(
            "/analyze",
            files={"file": ("test.txt", BytesIO(b"plain text"), "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "The document type is invalid. Only .docx files are supported.", response.text
        )
        self.assertIn("error-callout", response.text)
        self.mock_analyze.execute.assert_not_called()

    def test_post_analyze_legacy_doc_returns_400(self) -> None:
        response = self.client.post(
            "/analyze",
            files={"file": ("test.doc", BytesIO(b"legacy content"), "application/msword")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document could not be read.", response.text)
        self.assertIn("error-callout", response.text)
        self.mock_analyze.execute.assert_not_called()

    def test_post_analyze_oversized_file_returns_400(self) -> None:
        mock_env = EnvConfig()
        mock_env.upload_max_size_bytes = 100
        self.app.dependency_overrides[get_env_config] = lambda: mock_env

        response = self.client.post(
            "/analyze",
            files={
                "file": (
                    "test.docx",
                    BytesIO(b"a" * 200),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document file exceeds the maximum allowed size.", response.text)
        self.assertIn("error-callout", response.text)
        self.mock_analyze.execute.assert_not_called()

    def test_post_analyze_missing_file_returns_400(self) -> None:
        response = self.client.post("/analyze")

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document has no readable content.", response.text)
        self.assertIn("error-callout", response.text)
        self.mock_analyze.execute.assert_not_called()

    def test_post_analyze_empty_filename_returns_400(self) -> None:
        response = self.client.post(
            "/analyze",
            files={"file": ("", BytesIO(b""), "application/octet-stream")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("The document has no readable content.", response.text)
        self.assertIn("error-callout", response.text)
        self.mock_analyze.execute.assert_not_called()

    def test_get_reports_success_returns_file_content(self) -> None:
        dummy_file = self.reports_dir / "dummy_analisis.docx"
        file_content = b"PK\x03\x04mock docx content"
        dummy_file.write_bytes(file_content)

        response = self.client.get("/reports/dummy_analisis.docx")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, file_content)
        self.assertEqual(response.headers.get("content-type"), "application/octet-stream")
        self.assertIn(
            'filename="dummy_analisis.docx"', response.headers.get("content-disposition", "")
        )

    def test_get_reports_not_found(self) -> None:
        response = self.client.get("/reports/nonexistent.docx")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Report not found"})

    def test_get_reports_path_traversal_returns_404(self) -> None:
        # Standard traversal normalized by client
        response_norm = self.client.get("/reports/../secret.txt")
        self.assertEqual(response_norm.status_code, 404)

        # URL-encoded traversal reaching the endpoint logic
        response_encoded = self.client.get("/reports/%2e%2e/secret.txt")
        self.assertEqual(response_encoded.status_code, 404)
        self.assertEqual(response_encoded.json(), {"detail": "Report not found"})

    def test_get_reports_directory_env_override(self) -> None:
        with patch.dict(os.environ, {"SILVINA_REPORTS_DIR": "/custom/reports"}):
            self.assertEqual(get_reports_directory(), Path("/custom/reports"))

    def test_get_reports_directory_default(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SILVINA_REPORTS_DIR", None)
            expected = Path.home() / "Documents" / "Silvina" / "reports"
            self.assertEqual(get_reports_directory(), expected)

    def test_get_templates_returns_jinja2_templates(self) -> None:
        templates = get_templates()
        self.assertIsNotNone(templates.env)
