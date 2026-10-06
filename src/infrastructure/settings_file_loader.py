from pathlib import Path
from tomllib import TOMLDecodeError, load
from typing import Any

from src.domain.exceptions.settings_errors import (
    SettingsFileInvalid,
    SettingsFileNotFound,
)


class SettingsFileLoader:
    """Reads a TOML settings file into a nested dictionary of sections."""

    def __init__(self, settings_file_path: Path) -> None:
        """Store the path of the TOML settings file to read."""
        self._settings_file_path = settings_file_path

    def load(self) -> dict[str, Any]:
        """Return the parsed settings, failing fast when the file is missing or malformed."""
        if not self._settings_file_path.is_file():
            raise SettingsFileNotFound(str(self._settings_file_path))
        try:
            with self._settings_file_path.open("rb") as settings_file:
                return load(settings_file)
        except TOMLDecodeError as error:
            raise SettingsFileInvalid(f"{self._settings_file_path}: {error}") from error
