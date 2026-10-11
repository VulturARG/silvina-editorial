from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from src.infrastructure.adapters.report.docx_page_decoration import DocxPageDecoration
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures

PAGE_DECORATION_NAMES_IN_APPLY_ORDER = (
    "first_decoration",
    "second_decoration",
    "third_decoration",
)
SECTION_NAMES_IN_RENDER_ORDER = (
    "first_section",
    "second_section",
    "third_section",
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
    def test_export_applies_every_decoration_then_renders_every_section_in_order(
        self, document_class_mock
    ):
        document_mock = MagicMock()
        document_class_mock.return_value = document_mock
        call_recorder = MagicMock()
        page_decorations = []
        for decoration_name in PAGE_DECORATION_NAMES_IN_APPLY_ORDER:
            decoration_double = MagicMock(spec=DocxPageDecoration)
            call_recorder.attach_mock(decoration_double.apply, decoration_name)
            page_decorations.append(decoration_double)
        sections = []
        for section_name in SECTION_NAMES_IN_RENDER_ORDER:
            section_double = MagicMock(spec=DocxReportSection)
            call_recorder.attach_mock(section_double.render, section_name)
            sections.append(section_double)
        adapter = DocxReportAdapter(page_decorations=page_decorations, sections=sections)
        report_input = ReportFixtures.make_report_input_dto()

        adapter.export(report_input=report_input, output_path="out.docx")

        self.assertEqual(
            call_recorder.mock_calls,
            [
                getattr(call, decoration_name)(document=document_mock)
                for decoration_name in PAGE_DECORATION_NAMES_IN_APPLY_ORDER
            ]
            + [
                getattr(call, section_name)(document=document_mock, report_input=report_input)
                for section_name in SECTION_NAMES_IN_RENDER_ORDER
            ],
        )
        document_mock.save.assert_called_once_with("out.docx")

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_saves_document_when_no_decorations_or_sections(self, document_class_mock):
        document_mock = MagicMock()
        document_class_mock.return_value = document_mock
        adapter = DocxReportAdapter(page_decorations=(), sections=())

        result = adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path="empty.docx"
        )

        self.assertTrue(result)
        document_mock.save.assert_called_once_with("empty.docx")
