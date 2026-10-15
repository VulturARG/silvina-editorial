from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.tests.test_doubles.complete_test_environment import (
    CompleteTestEnvironment,
)
from src.infrastructure.tests.test_doubles.complete_test_settings import (
    CompleteTestSettings,
)


class TestEnvConfigQualityLevelThresholds(TestCase):
    @staticmethod
    def _complete_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
        environment = {
            **CompleteTestEnvironment.application_variables(),
            "METRICS_DATABASE_PATH": "/custom/path/metrics.db",
            "LOG_FILE_PATH": "/custom/path/silvina.log",
        }
        if overrides:
            environment.update(overrides)
        return environment

    def setUp(self):
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._settings_file_path = Path(self._temporary_directory.name) / "settings.toml"
        self._settings_file_path.write_text(CompleteTestSettings.toml_text(), encoding="utf-8")

    def test_get_quality_level_thresholds_maps_every_field_from_the_settings_file(self):
        expected = CompleteTestSettings.expected_values()
        with patch.dict(environ, self._complete_environment(), clear=True):
            config = EnvConfig(settings_file_path=self._settings_file_path)
            thresholds = config.get_quality_level_thresholds()

        self.assertIsInstance(thresholds, QualityLevelThresholdsDTO)
        self.assertEqual(
            thresholds,
            QualityLevelThresholdsDTO(
                excellent_threshold=expected["quality_level_excellent_threshold"],
                good_threshold=expected["quality_level_good_threshold"],
                acceptable_threshold=expected["quality_level_acceptable_threshold"],
                needs_improvement_threshold=expected["quality_level_needs_improvement_threshold"],
            ),
        )
