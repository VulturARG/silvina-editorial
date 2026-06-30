from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterExportSuccess(TestCase):
    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_returns_true_on_success(self, mock_document_class):
        mock_document_class.return_value = MagicMock()

        adapter = DocxReportAdapter(logo_path=None)
        result = adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path="output.docx"
        )

        self.assertTrue(result)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_calls_doc_save_with_correct_path(self, mock_document_class):
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        adapter = DocxReportAdapter(logo_path=None)
        adapter.export(
            report_input=ReportFixtures.make_report_input_dto(), output_path="output.docx"
        )

        mock_doc.save.assert_called_once_with("output.docx")

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_export_calls_all_thirteen_add_methods(self, mock_document_class):
        mock_document_class.return_value = MagicMock()

        adapter = DocxReportAdapter(logo_path=None)
        report_input = ReportFixtures.make_report_input_dto()

        with (
            patch.object(adapter, "_add_title_page") as m_title,
            patch.object(adapter, "_add_header_logo") as m_logo,
            patch.object(adapter, "_add_page_numbers") as m_pages,
            patch.object(adapter, "_add_executive_summary") as m_exec,
            patch.object(adapter, "_add_document_info") as m_doc_info,
            patch.object(adapter, "_add_classification") as m_class,
            patch.object(adapter, "_add_quality_analysis") as m_quality,
            patch.object(adapter, "_add_grammar_analysis") as m_grammar,
            patch.object(adapter, "_add_apa_validation") as m_apa,
            patch.object(adapter, "_add_structure_validation") as m_struct,
            patch.object(adapter, "_add_citations_analysis") as m_citations,
            patch.object(adapter, "_add_recommendations") as m_recs,
            patch.object(adapter, "_add_footer") as m_footer,
        ):
            adapter.export(report_input=report_input, output_path="out.docx")

            m_title.assert_called_once()
            m_logo.assert_called_once()
            m_pages.assert_called_once()
            m_exec.assert_called_once()
            m_doc_info.assert_called_once()
            m_class.assert_called_once()
            m_quality.assert_called_once()
            m_grammar.assert_called_once()
            m_apa.assert_called_once()
            m_struct.assert_called_once()
            m_citations.assert_called_once()
            m_recs.assert_called_once()
            m_footer.assert_called_once()
