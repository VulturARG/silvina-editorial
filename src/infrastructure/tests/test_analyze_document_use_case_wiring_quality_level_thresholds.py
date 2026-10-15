from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
from src.infrastructure.tests.test_doubles.analyze_document_use_case_wiring_for_test import (
    AnalyzeDocumentUseCaseWiringForTest,
)
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import (
    CompleteTestSettings,
)


class TestAnalyzeDocumentUseCaseWiringQualityLevelThresholds(TestCase):
    @staticmethod
    def _complete_environment() -> dict[str, str]:
        return {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"

    def _write_settings(self, overrides: dict[str, int | float | str | None] | None = None) -> None:
        self._settings_file_path.write_text(
            CompleteTestSettings.toml_text(overrides), encoding="utf-8"
        )

    def test_quality_analyzer_is_built_with_thresholds_from_the_settings_file(self):
        self._write_settings()

        with patch.dict(environ, self._complete_environment(), clear=True):
            wiring = AnalyzeDocumentUseCaseWiringForTest(self._settings_file_path)
            analyzer = wiring._get_quality_analyzer()

        self.assertEqual(
            analyzer._quality_level_thresholds,
            QualityLevelThresholdsDTO(
                excellent_threshold=9.4,
                good_threshold=7.6,
                acceptable_threshold=5.8,
                needs_improvement_threshold=3.2,
            ),
        )
