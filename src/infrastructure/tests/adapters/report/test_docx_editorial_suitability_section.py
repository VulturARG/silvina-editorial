from unittest import TestCase

from docx import Document

from src.domain.dtos.editorial_suitability_dto import EditorialSuitabilityDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.enums.quality_level import QualityLevel
from src.infrastructure.adapters.report.docx_report_section import DocxReportSection
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxEditorialSuitabilitySection(TestCase):
    def setUp(self) -> None:
        self.section = ReportFixtures.make_editorial_suitability_section()
        self.document = Document()

    def _paragraph_texts(self) -> list[str]:
        return [paragraph.text for paragraph in self.document.paragraphs]

    def _report_input_with_suitability(self, contribution_phrase: str) -> ReportInputDTO:
        suitability = EditorialSuitabilityDTO(
            contribution_verdict="SUSTENTADA",
            contribution_phrase=contribution_phrase,
            contribution_observation="Contribución sustentada.",
            alignment_verdict="ALINEADO",
            alignment_lines="Línea 1 y 2.",
            alignment_justification="Se relaciona directamente con las líneas mencionadas.",
        )
        quality = QualityResultDTO(
            overall_score=8.0,
            quality_level=QualityLevel.GOOD,
            editorial_suitability=suitability,
        )
        return ReportFixtures.make_report_input_dto(quality=quality)

    def test_is_docx_report_section(self) -> None:
        self.assertIsInstance(self.section, DocxReportSection)

    def test_render_adds_nothing_when_suitability_is_absent(self) -> None:
        quality = QualityResultDTO(overall_score=8.0, quality_level=QualityLevel.GOOD)
        report_input = ReportFixtures.make_report_input_dto(quality=quality)

        self.section.render(document=self.document, report_input=report_input)

        self.assertEqual(self._paragraph_texts(), [])

    def test_render_adds_contribution_and_alignment_blocks(self) -> None:
        report_input = self._report_input_with_suitability(
            contribution_phrase="Propone un marco de análisis original."
        )

        self.section.render(document=self.document, report_input=report_input)

        self.assertEqual(
            self._paragraph_texts(),
            [
                "🎯 PERTINENCIA EDITORIAL",
                "Contribución",
                "Veredicto: SUSTENTADA",
                "Aporte identificado: Propone un marco de análisis original.",
                "Observación: Contribución sustentada.",
                "Alineación con líneas de investigación",
                "Veredicto: ALINEADO",
                "Líneas relacionadas: Línea 1 y 2.",
                "Justificación: Se relaciona directamente con las líneas mencionadas.",
            ],
        )

    def test_render_omits_contribution_phrase_when_empty(self) -> None:
        report_input = self._report_input_with_suitability(contribution_phrase="")

        self.section.render(document=self.document, report_input=report_input)

        self.assertFalse(
            any(text.startswith("Aporte identificado") for text in self._paragraph_texts())
        )
