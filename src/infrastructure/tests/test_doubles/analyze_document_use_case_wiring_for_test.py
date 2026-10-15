from pathlib import Path

from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.tests.dtos.editorial_norms_builder_for_test import (
    build_editorial_norms_for_test,
)
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)


class AnalyzeDocumentUseCaseWiringForTest(AnalyzeDocumentUseCaseWiring):
    """Wires the use case with the environment configuration read from a given settings file."""

    def __init__(self, settings_file_path: Path) -> None:
        """Store the settings file the environment configuration is read from."""
        super().__init__()
        self._settings_file_path = settings_file_path

    def _get_env_config(self) -> EnvConfig:
        if self._env_config_instance is None:
            self._env_config_instance = EnvConfig(settings_file_path=self._settings_file_path)
        return self._env_config_instance

    def _get_editorial_norms(self) -> EditorialNormsDTO:
        return build_editorial_norms_for_test()
