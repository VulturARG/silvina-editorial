from os import environ
from typing import Any

from src.domain.exceptions.settings_errors import SettingValueInvalid, SettingValueMissing


class SettingsValueResolver:
    """Resolves typed settings: an environment variable wins over the settings file value."""

    def __init__(self, settings: dict[str, Any]) -> None:
        """Store the parsed settings file sections."""
        self._settings = settings

    def read_integer(self, environment_name: str, section: str, key: str) -> int:
        """Return an integer setting from the environment variable or the settings file."""
        if environment_name in environ:
            return self._parse_environment_integer(environment_name)
        value = self._read_file_value(environment_name, section, key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise self._invalid_file_value(section, key, "an integer")
        return value

    def read_float(self, environment_name: str, section: str, key: str) -> float:
        """Return a float setting from the environment variable or the settings file."""
        if environment_name in environ:
            return self._parse_environment_float(environment_name)
        value = self._read_file_value(environment_name, section, key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise self._invalid_file_value(section, key, "a number")
        return float(value)

    def read_string(self, environment_name: str, section: str, key: str) -> str:
        """Return a text setting from the environment variable or the settings file."""
        if environment_name in environ:
            return environ[environment_name]
        value = self._read_file_value(environment_name, section, key)
        if not isinstance(value, str):
            raise self._invalid_file_value(section, key, "text")
        return value

    def _parse_environment_integer(self, environment_name: str) -> int:
        raw_value = environ[environment_name]
        try:
            return int(raw_value)
        except ValueError:
            raise self._invalid_environment_value(
                environment_name, raw_value, "an integer"
            ) from None

    def _parse_environment_float(self, environment_name: str) -> float:
        raw_value = environ[environment_name]
        try:
            return float(raw_value)
        except ValueError:
            raise self._invalid_environment_value(environment_name, raw_value, "a number") from None

    def _read_file_value(self, environment_name: str, section: str, key: str) -> Any:
        section_values = self._settings.get(section)
        if not isinstance(section_values, dict) or key not in section_values:
            raise SettingValueMissing(
                f"'{key}' in section [{section}] of the settings file "
                f"(it can also be set with the environment variable {environment_name})."
            )
        return section_values[key]

    def _invalid_file_value(self, section: str, key: str, expected: str) -> SettingValueInvalid:
        return SettingValueInvalid(
            f"'{key}' in section [{section}] of the settings file (expected {expected})."
        )

    def _invalid_environment_value(
        self, environment_name: str, raw_value: str, expected: str
    ) -> SettingValueInvalid:
        return SettingValueInvalid(
            f"environment variable {environment_name} is '{raw_value}' (expected {expected})."
        )
