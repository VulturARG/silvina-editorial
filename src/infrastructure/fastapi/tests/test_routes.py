from io import BytesIO
from os import environ
from pathlib import Path
from re import search
from tempfile import TemporaryDirectory
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
        self.temp_reports_dir = TemporaryDirectory()
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
        captured_kwargs: list[dict] = []

        def fake_execute(*args, **kwargs):
            captured_kwargs.append(kwargs)
            document_path = kwargs.get("document_path") or (args[0] if args else "")
            path = Path(document_path)
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

        match = search(r"/reports/([0-9a-f]{32})/test_analisis\.docx", response.text)
        self.assertIsNotNone(match, "Response should link to docx in hex sub-folder")
        assert match is not None
        analysis_folder = match.group(1)

        self.assertIn(f"/reports/{analysis_folder}/test_analisis.json", response.text)

        self.assertEqual(len(captured_paths), 1)
        self.assertFalse(captured_paths[0].exists(), "Temporary upload file should be unlinked")
        self.assertEqual(captured_kwargs[0].get("document_name"), "test.docx")

        expected_word_path = str(self.reports_dir / analysis_folder / "test_analisis.docx")
        expected_json_path = str(self.reports_dir / analysis_folder / "test_analisis.json")
        self.mock_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=expected_word_path
        )
        self.mock_json_export.execute.assert_called_once_with(
            report_input=fake_report, output_path=expected_json_path
        )

    def test_post_analyze_consecutive_uploads_produce_unique_folders(self) -> None:
        fake_report = ReportFixtures.make_report_input_dto()
        self.mock_analyze.execute.return_value = fake_report

        file_payload = b"valid docx binary content for test"
        response_one = self.client.post(
            "/analyze",
            files={
                "file": (
                    "paper.docx",
                    BytesIO(file_payload),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        response_two = self.client.post(
            "/analyze",
            files={
                "file": (
                    "paper.docx",
                    BytesIO(file_payload),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        self.assertEqual(response_one.status_code, 200)
        self.assertEqual(response_two.status_code, 200)

        match_one = search(r"/reports/([0-9a-f]{32})/paper_analisis\.docx", response_one.text)
        match_two = search(r"/reports/([0-9a-f]{32})/paper_analisis\.docx", response_two.text)
        self.assertIsNotNone(match_one)
        self.assertIsNotNone(match_two)
        assert match_one is not None
        assert match_two is not None

        folder_one = match_one.group(1)
        folder_two = match_two.group(1)
        self.assertNotEqual(folder_one, folder_two)

        export_calls = self.mock_export.execute.call_args_list
        self.assertEqual(len(export_calls), 2)
        self.assertNotEqual(
            export_calls[0].kwargs["output_path"],
            export_calls[1].kwargs["output_path"],
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

    def test_get_reports_success_with_subfolder_returns_file_content(self) -> None:
        analysis_directory = self.reports_dir / "a1b2c3d4e5f60718293a4b5c6d7e8f90"
        analysis_directory.mkdir(parents=True, exist_ok=True)
        dummy_file = analysis_directory / "dummy_analisis.docx"
        file_content = b"PK\x03\x04mock docx content"
        dummy_file.write_bytes(file_content)

        response = self.client.get("/reports/a1b2c3d4e5f60718293a4b5c6d7e8f90/dummy_analisis.docx")

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
        response_norm = self.client.get("/reports/../secret.txt")
        self.assertEqual(response_norm.status_code, 404)

        response_encoded = self.client.get("/reports/%2e%2e/secret.txt")
        self.assertEqual(response_encoded.status_code, 404)
        self.assertEqual(response_encoded.json(), {"detail": "Report not found"})

    def test_get_reports_directory_env_override(self) -> None:
        with patch.dict(environ, {"SILVINA_REPORTS_DIR": "/custom/reports"}):
            self.assertEqual(get_reports_directory(), Path("/custom/reports"))

    def test_get_reports_directory_default(self) -> None:
        with patch.dict(environ, {}, clear=False):
            environ.pop("SILVINA_REPORTS_DIR", None)
            expected = Path.home() / "Documents" / "Silvina" / "reports"
            self.assertEqual(get_reports_directory(), expected)

    def test_get_templates_returns_jinja2_templates(self) -> None:
        templates = get_templates()
        self.assertIsNotNone(templates.env)
