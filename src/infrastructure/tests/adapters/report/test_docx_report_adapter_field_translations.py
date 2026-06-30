from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.domain.dtos.apa_violation_dto import ApaViolationDTO
from src.domain.enums.apa_error_type import ApaErrorType
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterFieldTranslations(TestCase):
    """Verify DTO attribute access is used (not dict key access)."""

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_add_grammar_analysis_reads_report_input_grammar_directly(self, mock_document_class):
        mock_document_class.return_value = MagicMock()
        adapter = DocxReportAdapter(logo_path=None)

        grammar = ReportFixtures.make_grammar_mock(score=6.5)
        report_input = ReportFixtures.make_report_input_dto(grammar=grammar)

        adapter._add_grammar_analysis(mock_document_class.return_value, report_input)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_add_apa_validation_reads_citation_text_attribute(self, mock_document_class):
        mock_document_class.return_value = MagicMock()
        adapter = DocxReportAdapter(logo_path=None)

        violation = ApaViolationDTO(
            citation_text="(Smith, 2020)",
            error_type=ApaErrorType.CONJUNCTION_ERROR,
            location=5,
            explanation="Missing year",
            correction="(Smith, 2020)",
        )
        apa = ReportFixtures.make_apa_validation_mock(violations=[violation])
        report_input = ReportFixtures.make_report_input_dto(apa_validation=apa)

        adapter._add_apa_validation(mock_document_class.return_value, report_input)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_add_classification_reads_article_type_attribute(self, mock_document_class):
        mock_document_class.return_value = MagicMock()
        adapter = DocxReportAdapter(logo_path=None)

        classification = ReportFixtures.make_classification_mock(article_type_value="investigacion")
        report_input = ReportFixtures.make_report_input_dto(classification=classification)

        adapter._add_classification(mock_document_class.return_value, report_input)

    @patch("src.infrastructure.adapters.report.docx_report_adapter.Document")
    def test_add_document_info_derives_estimated_pages_from_word_count(self, mock_document_class):
        mock_document_class.return_value = MagicMock()
        adapter = DocxReportAdapter(logo_path=None)

        doc_content = ReportFixtures.make_doc_content_mock(word_count=500)
        report_input = ReportFixtures.make_report_input_dto(document_content=doc_content)

        adapter._add_document_info(mock_document_class.return_value, report_input)
