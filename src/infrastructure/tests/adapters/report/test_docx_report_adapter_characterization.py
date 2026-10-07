from json import loads
from os.path import dirname, join
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.resources.assets import ASSETS_DIR
from src.infrastructure.tests.adapters.report.characterization_report_input import (
    CharacterizationReportInput,
)
from src.infrastructure.tests.adapters.report.docx_fingerprint import (
    DocxFingerprintBuilder,
)
from src.infrastructure.tests.adapters.report.fixtures import ReportFixtures


class TestDocxReportAdapterCharacterization(TestCase):
    """Characterization tests pinning observable output of DocxReportAdapter."""

    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._golden_file_path = join(dirname(__file__), "fixtures", "docx_report_fingerprint.json")
        self._logo_path = join(ASSETS_DIR, "logo.jpg")
        self._settings = ReportFixtures.make_settings()
        self._adapter = DocxReportAdapter(
            docx_report_settings=self._settings,
            logo_path=self._logo_path,
        )
        self._fingerprint_builder = DocxFingerprintBuilder()
        self._report_input = CharacterizationReportInput.build()

    def test_export_matches_golden_fingerprint(self) -> None:
        output_path = join(self._temporary_directory.name, "exported_report.docx")
        export_succeeded = self._adapter.export(
            report_input=self._report_input,
            output_path=output_path,
        )
        self.assertTrue(export_succeeded)

        actual_fingerprint = self._fingerprint_builder.build(output_path)
        with open(self._golden_file_path, "r", encoding="utf-8") as golden_file:
            expected_fingerprint = loads(golden_file.read())

        self.assertEqual(actual_fingerprint, expected_fingerprint)

    def test_export_produces_identical_fingerprint_when_executed_twice(self) -> None:
        first_output_path = join(self._temporary_directory.name, "report_first_run.docx")
        second_output_path = join(self._temporary_directory.name, "report_second_run.docx")

        first_export_succeeded = self._adapter.export(
            report_input=self._report_input,
            output_path=first_output_path,
        )
        second_export_succeeded = self._adapter.export(
            report_input=self._report_input,
            output_path=second_output_path,
        )
        self.assertTrue(first_export_succeeded)
        self.assertTrue(second_export_succeeded)

        first_fingerprint = self._fingerprint_builder.build(first_output_path)
        second_fingerprint = self._fingerprint_builder.build(second_output_path)

        self.assertEqual(first_fingerprint, second_fingerprint)
