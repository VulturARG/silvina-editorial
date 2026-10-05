from os import environ
from unittest import TestCase
from unittest.mock import patch

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring


class TestExportReportWiring(TestCase):
    def test_create_use_case_returns_export_report_use_case_instance(self):
        result = ExportReportWiring().create_use_case()
        self.assertIsInstance(result, ExportReportUseCase)

    def test_create_use_case_wires_docx_report_adapter_as_port(self):
        result = ExportReportWiring().create_use_case()
        self.assertIsInstance(result._report_export_port, DocxReportAdapter)

    def test_create_use_case_injects_report_words_per_page_from_env(self):
        with patch.dict(environ, {"REPORT_WORDS_PER_PAGE": "300"}):
            result = ExportReportWiring().create_use_case()
        assert isinstance(result._report_export_port, DocxReportAdapter)
        self.assertEqual(result._report_export_port._docx_report_settings.words_per_page, 300)

    def test_create_use_case_injects_app_name_and_version_from_env(self):
        with patch.dict(
            environ,
            {"TESTING": "True", "SILVINA_APP_NAME": "Custom App", "SILVINA_VERSION": "1.0"},
        ):
            result = ExportReportWiring().create_use_case()
        assert isinstance(result._report_export_port, DocxReportAdapter)
        settings = result._report_export_port._docx_report_settings
        self.assertEqual(settings.app_name, "Custom App")
        self.assertEqual(settings.app_version, "1.0")

    def test_create_use_case_injects_score_thresholds_from_env(self):
        with patch.dict(
            environ,
            {"REPORT_SCORE_HIGH_THRESHOLD": "9.0", "REPORT_SCORE_MEDIUM_THRESHOLD": "5.0"},
        ):
            result = ExportReportWiring().create_use_case()
        assert isinstance(result._report_export_port, DocxReportAdapter)
        settings = result._report_export_port._docx_report_settings
        self.assertAlmostEqual(settings.score_high_threshold, 9.0)
        self.assertAlmostEqual(settings.score_medium_threshold, 5.0)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.DOCX_AVAILABLE", False)
    def test_create_use_case_raises_report_export_unavailable_when_docx_missing(self):
        with self.assertRaises(ReportExportUnavailable):
            ExportReportWiring().create_use_case()
