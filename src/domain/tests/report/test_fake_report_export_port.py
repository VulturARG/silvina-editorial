from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.report_errors import ReportExportUnavailable
from src.domain.report.report_export_port import ReportExportPort
from src.domain.tests.report.fake_report_export_port import FakeReportExportPort


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
    }
    defaults.update(overrides)
    return ReportInputDTO(**defaults)


class TestFakeReportExportPort(TestCase):
    def test_satisfies_port_contract_without_type_error(self):
        fake = FakeReportExportPort()
        self.assertIsInstance(fake, ReportExportPort)

    def test_returns_configured_true_value(self):
        fake = FakeReportExportPort(return_value=True)
        result = fake.export(report_input=_make_report_input_dto(), output_path="out.docx")
        self.assertTrue(result)

    def test_returns_configured_false_value(self):
        fake = FakeReportExportPort(return_value=False)
        result = fake.export(report_input=_make_report_input_dto(), output_path="out.docx")
        self.assertFalse(result)

    def test_raises_configured_exception(self):
        fake = FakeReportExportPort(raise_error=ReportExportUnavailable())
        with self.assertRaises(ReportExportUnavailable):
            fake.export(report_input=_make_report_input_dto(), output_path="out.docx")
