from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from docx import Document

from src.domain.dtos.apa_violation_dto import ApaViolationDTO
from src.domain.enums.apa_error_type import ApaErrorType
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterFieldTranslations(TestCase):
    """Verify the exported report reads DTO attributes, not dictionary keys."""

    def test_export_renders_grammar_score_and_apa_citation_text_attributes(self):
        violation = ApaViolationDTO(
            citation_text="(Smith, 2020)",
            error_type=ApaErrorType.CONJUNCTION_ERROR,
            location=5,
            explanation="Missing year",
            correction="(Smith, 2020)",
        )
        report_input = ReportFixtures.make_report_input_dto(
            grammar=ReportFixtures.make_grammar_mock(score=6.5),
            apa_validation=ReportFixtures.make_apa_validation_mock(violations=[violation]),
        )

        with TemporaryDirectory() as temporary_directory:
            output_path = join(temporary_directory, "report.docx")
            ReportFixtures.make_adapter().export(report_input=report_input, output_path=output_path)
            paragraph_texts = [paragraph.text for paragraph in Document(output_path).paragraphs]

        self.assertIn("Puntuación: 6.5/10", paragraph_texts)
        self.assertIn("1. Citación: (Smith, 2020)", paragraph_texts)
