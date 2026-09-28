"""End-to-end tests for FastAPI web interface workflow."""

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.infrastructure.fastapi.fastapi_app import create_app
from src.infrastructure.fastapi.src.config.dependencies import (
    get_analyze_document_use_case,
    get_export_report_use_case,
    get_json_export_report_use_case,
    get_reports_directory,
)
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestFastApiE2E(unittest.TestCase):
    """E2E verification for complete user journey through FastAPI web interface."""

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

    def test_complete_e2e_workflow(self) -> None:
        """Verify the full E2E user journey:

        1. GET / -> landing page with upload form and HTMX indicators.
        2. POST /analyze -> document analysis, report generation, and results rendering.
        3. GET /reports/{filename} -> download generated Word and JSON reports, 404 for missing.
        """
        # -------------------------------------------------------------
        # Step 1: GET / (landing page)
        # -------------------------------------------------------------
        index_response = self.client.get("/")
        self.assertEqual(index_response.status_code, 200)
        self.assertIn("Silvina - Asistente Editorial EUMIC", index_response.text)
        self.assertIn("<form", index_response.text)
        self.assertIn('hx-post="/analyze"', index_response.text)
        self.assertIn("hx-indicator", index_response.text)
        self.assertIn('id="loading-indicator"', index_response.text)

        # -------------------------------------------------------------
        # Step 2: POST /analyze (submit .docx for analysis)
        # -------------------------------------------------------------
        fake_report = ReportFixtures.make_report_input_dto()
        expected_word_filename = "paper_sample_analisis.docx"
        expected_json_filename = "paper_sample_analisis.json"
        expected_word_path = self.reports_dir / expected_word_filename
        expected_json_path = self.reports_dir / expected_json_filename

        mock_word_bytes = b"PK\x03\x04mock docx report payload"
        mock_json_bytes = b'{"analysis": "mock json content"}'

        def fake_export_side_effect(report_input, output_path):
            Path(output_path).write_bytes(mock_word_bytes)

        def fake_json_export_side_effect(report_input, output_path):
            Path(output_path).write_bytes(mock_json_bytes)

        self.mock_analyze.execute.return_value = fake_report
        self.mock_export.execute.side_effect = fake_export_side_effect
        self.mock_json_export.execute.side_effect = fake_json_export_side_effect

        upload_payload = b"PK\x03\x04sample document binary content"
        analyze_response = self.client.post(
            "/analyze",
            files={
                "file": (
                    "paper_sample.docx",
                    BytesIO(upload_payload),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        self.assertEqual(analyze_response.status_code, 200)

        # Assert results rendering elements:
        # Verdict banner
        self.assertIn("status-banner approved", analyze_response.text)
        self.assertIn("APTO PARA PUBLICACIÓN", analyze_response.text)
        # Title
        self.assertIn(fake_report.document_content.title, analyze_response.text)
        # Scores
        self.assertIn("Gramática y Ortografía", analyze_response.text)
        self.assertIn("Calidad Semántica", analyze_response.text)
        self.assertIn("7.5", analyze_response.text)
        self.assertIn("8.0", analyze_response.text)
        # Error metrics
        self.assertIn("Errores gramaticales", analyze_response.text)
        self.assertIn("Errores APA 7", analyze_response.text)
        self.assertIn("Citas sin referencia", analyze_response.text)
        self.assertIn("Secciones faltantes", analyze_response.text)
        # Download buttons and filenames in download links
        self.assertIn(f"/reports/{expected_word_filename}", analyze_response.text)
        self.assertIn(f"/reports/{expected_json_filename}", analyze_response.text)
        self.assertIn("Descargar Informe Word (.docx)", analyze_response.text)
        self.assertIn("Descargar Datos Técnicos (.json)", analyze_response.text)

        # Verify export use cases were invoked with report_input and output_path
        self.mock_analyze.execute.assert_called_once()
        self.mock_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=str(expected_word_path)
        )
        self.mock_json_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=str(expected_json_path)
        )

        # -------------------------------------------------------------
        # Step 3: GET /reports/{filename} (download generated reports)
        # -------------------------------------------------------------
        # Request Word report
        word_response = self.client.get(f"/reports/{expected_word_filename}")
        self.assertEqual(word_response.status_code, 200)
        self.assertEqual(word_response.content, mock_word_bytes)
        self.assertEqual(word_response.headers.get("content-type"), "application/octet-stream")
        self.assertIn(
            f'filename="{expected_word_filename}"',
            word_response.headers.get("content-disposition", ""),
        )

        # Request JSON report
        json_response = self.client.get(f"/reports/{expected_json_filename}")
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.content, mock_json_bytes)
        self.assertEqual(json_response.headers.get("content-type"), "application/octet-stream")
        self.assertIn(
            f'filename="{expected_json_filename}"',
            json_response.headers.get("content-disposition", ""),
        )

        # Request non-existent report
        not_found_response = self.client.get("/reports/non_existent.docx")
        self.assertEqual(not_found_response.status_code, 404)
        self.assertEqual(not_found_response.json(), {"detail": "Report not found"})

    def test_error_flow_invalid_file_extension(self) -> None:
        """Submit invalid.txt to POST /analyze -> returns 400 with domain error partial."""
        response = self.client.post(
            "/analyze",
            files={"file": ("invalid.txt", BytesIO(b"plain text content"), "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error-callout", response.text)
        self.assertIn(
            "The document type is invalid. Only .docx files are supported.", response.text
        )
        self.mock_analyze.execute.assert_not_called()

    def test_error_flow_missing_file(self) -> None:
        """Submit missing file to POST /analyze -> returns 400 with domain error partial."""
        response = self.client.post("/analyze")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error-callout", response.text)
        self.assertIn("The document has no readable content.", response.text)
        self.mock_analyze.execute.assert_not_called()
