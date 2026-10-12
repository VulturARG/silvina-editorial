from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.report_input_dto import ReportInputDTO

PUBLISHABLE_REASON = (
    "El documento cumple con todos los estándares de calidad, estructura y formato APA 7 "
    "requeridos por las normas EUMIC."
)


def _make_report_input_dto(**overrides) -> ReportInputDTO:
    quality = MagicMock()
    quality.overall_score = 8.0
    grammar = MagicMock()
    grammar.score = 8.0
    structure = MagicMock()
    structure.is_valid = True
    citations = MagicMock()
    citations.total_citations = 5
    apa_validation = MagicMock()
    apa_validation.violations = []

    defaults = {
        "filename": "test.docx",
        "document_content": MagicMock(),
        "classification": MagicMock(),
        "quality": quality,
        "grammar": grammar,
        "structure": structure,
        "citations": citations,
        "apa_validation": apa_validation,
        "recommendations": [],
        "verdict": MagicMock(),
        "eumic_violations": [],
    }
    defaults.update(overrides)
    return ReportInputDTO(**defaults)


class TestReportInputDTO(TestCase):
    def test_constructs_with_all_ten_fields(self):
        dto = _make_report_input_dto()
        self.assertEqual(dto.filename, "test.docx")

    def test_is_frozen_raises_on_field_reassignment(self):
        dto = _make_report_input_dto()
        with self.assertRaises(FrozenInstanceError):
            dto.filename = "other.docx"  # type: ignore[misc]

    def test_is_publishable_true_when_all_thresholds_met(self):
        dto = _make_report_input_dto()
        self.assertTrue(dto.is_publishable(7.0))

    def test_is_publishable_false_when_no_citations(self):
        citations = MagicMock()
        citations.total_citations = 0
        dto = _make_report_input_dto(citations=citations)
        self.assertFalse(dto.is_publishable(7.0))

    def test_is_publishable_false_when_quality_below_threshold(self):
        quality = MagicMock()
        quality.overall_score = 5.0
        dto = _make_report_input_dto(quality=quality)
        self.assertFalse(dto.is_publishable(7.0))

    def test_is_publishable_false_when_apa_violations_present(self):
        apa = MagicMock()
        apa.violations = [MagicMock()]
        dto = _make_report_input_dto(apa_validation=apa)
        self.assertFalse(dto.is_publishable(7.0))

    def test_is_publishable_uses_the_threshold_argument(self):
        dto = _make_report_input_dto()
        self.assertTrue(dto.is_publishable(7.0))
        self.assertFalse(dto.is_publishable(9.0))

    def test_publishability_reason_mentions_quality_score_when_low(self):
        quality = MagicMock()
        quality.overall_score = 5.0
        dto = _make_report_input_dto(quality=quality)
        self.assertIn("5.0/10", dto.publishability_reason(7.0))

    def test_publishability_reason_no_citations_message(self):
        citations = MagicMock()
        citations.total_citations = 0
        dto = _make_report_input_dto(citations=citations)
        self.assertIn("No se detectaron citas APA", dto.publishability_reason(7.0))

    def test_publishability_reason_confirms_compliance_when_publishable(self):
        dto = _make_report_input_dto()
        self.assertEqual(dto.publishability_reason(7.0), PUBLISHABLE_REASON)

    def test_publishability_reason_changes_with_the_threshold_argument(self):
        dto = _make_report_input_dto()
        self.assertEqual(dto.publishability_reason(7.0), PUBLISHABLE_REASON)
        self.assertEqual(
            dto.publishability_reason(9.0),
            "El documento requiere revisión. Calidad: 8.0/10, Gramática: 8.0/10, Errores APA: 0.",
        )
