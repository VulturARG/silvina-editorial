from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from docx import Document

from src.domain.enums.classification_confidence import ClassificationConfidence
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterClassificationConfidence(TestCase):
    """Integration test verifying Word report export with ClassificationConfidence."""

    def test_export_succeeds_and_renders_formatted_confidence_percentage(self):
        with TemporaryDirectory() as temporary_directory:
            output_path = str(Path(temporary_directory) / "test_report.docx")
            adapter = DocxReportAdapter(logo_path=None, settings=ReportFixtures.make_settings())
            classification = ReportFixtures.make_classification_mock()
            classification.confidence = ClassificationConfidence.FULL_SIGNAL_MATCH
            report_input = ReportFixtures.make_report_input_dto(classification=classification)

            export_result = adapter.export(report_input=report_input, output_path=output_path)

            self.assertTrue(export_result)
            document = Document(output_path)
            full_document_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            self.assertIn("90.0%", full_document_text)
