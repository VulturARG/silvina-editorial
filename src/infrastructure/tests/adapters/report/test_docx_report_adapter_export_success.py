from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures

SECTION_NAMES_IN_REPORT_ORDER = (
    "title_page_section",
    "executive_summary_section",
    "document_info_section",
    "classification_section",
    "quality_analysis_section",
    "editorial_suitability_section",
    "grammar_analysis_section",
    "apa_validation_section",
    "structure_validation_section",
    "citations_analysis_section",
    "recommendations_section",
    "footer_section",
)


class TestDocxReportAdapterExportSuccess(TestCase):
    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_returns_true_on_success(self, document_class_mock):
        document_class_mock.return_value = MagicMock()

        adapter = ReportFixtures.make_adapter()
        result = adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path="output.docx"
        )

        self.assertTrue(result)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_calls_document_save_with_correct_path(self, document_class_mock):
        document_mock = MagicMock()
        document_class_mock.return_value = document_mock

        adapter = ReportFixtures.make_adapter()
        adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path="output.docx"
        )

        document_mock.save.assert_called_once_with("output.docx")

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_renders_every_injected_section_once_in_report_order(self, document_class_mock):
        document_mock = MagicMock()
        document_class_mock.return_value = document_mock
        render_recorder = MagicMock()
        sections: dict[str, DocxReportSection] = {}
        for section_name in SECTION_NAMES_IN_REPORT_ORDER:
            section_double = MagicMock(spec=DocxReportSection)
            render_recorder.attach_mock(section_double.render, section_name)
            sections[section_name] = section_double
        adapter = ReportFixtures.make_adapter_with_sections(sections=sections)
        report_input = ReportFixtures.make_report_input_dto()

        adapter.export(report_input=report_input, output_path="out.docx")

        self.assertEqual(
            render_recorder.mock_calls,
            [
                getattr(call, section_name)(document=document_mock, report_input=report_input)
                for section_name in SECTION_NAMES_IN_REPORT_ORDER
            ],
        )
        document_mock.save.assert_called_once_with("out.docx")
