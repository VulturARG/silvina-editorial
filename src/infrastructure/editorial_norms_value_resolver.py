from typing import Any

from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormInvalid,
    EditorialNormMissing,
)


class EditorialNormsValueResolver:
    """Resolves typed editorial norms values from parsed configuration dictionaries."""

    def __init__(self, norms: dict[str, Any]) -> None:
        """Store the parsed editorial norms sections."""
        self._norms = norms

    def read_integer(self, section: str, key: str) -> int:
        """Return an integer editorial norm from the specified section and key."""
        value = self._read_norm_value(section, key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise EditorialNormInvalid(
                f"'{key}' in section [{section}] of the editorial norms file (expected an integer)."
            )
        return value

    def read_float(self, section: str, key: str) -> float:
        """Return a float editorial norm from the specified section and key."""
        value = self._read_norm_value(section, key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EditorialNormInvalid(
                f"'{key}' in section [{section}] of the editorial norms file (expected a number)."
            )
        return float(value)

    def read_string_list(self, section: str, key: str) -> tuple[str, ...]:
        """Return a non-empty tuple of non-blank strings from the specified section and key."""
        value = self._read_norm_value(section, key)
        if not isinstance(value, list) or len(value) == 0:
            raise EditorialNormInvalid(
                f"'{key}' in section [{section}] of the editorial norms file (expected a non-empty list of text)."
            )
        for element in value:
            if not isinstance(element, str) or not element.strip():
                raise EditorialNormInvalid(
                    f"'{key}' in section [{section}] of the editorial norms file contains an invalid or blank string element."
                )
        return tuple(value)

    def _read_norm_value(self, section: str, key: str) -> Any:
        section_values = self._norms.get(section)
        if not isinstance(section_values, dict):
            raise EditorialNormMissing(
                f"'{key}' in section [{section}] of the editorial norms file."
            )
        if key not in section_values:
            raise EditorialNormMissing(
                f"'{key}' in section [{section}] of the editorial norms file."
            )
        return section_values[key]
