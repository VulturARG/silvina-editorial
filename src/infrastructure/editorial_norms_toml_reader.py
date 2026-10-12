from pathlib import Path
from tomllib import TOMLDecodeError, load
from typing import Any

from src.domain.exceptions.editorial_norms_errors import (
    EditorialNormsFileInvalid,
    EditorialNormsFileNotFound,
)


class EditorialNormsTomlReader:
    """Reads a TOML editorial norms file into a dictionary of sections."""

    def __init__(self, editorial_norms_path: Path) -> None:
        """Store the path of the TOML editorial norms file to read."""
        self._editorial_norms_path = Path(editorial_norms_path)

    def load(self) -> dict[str, Any]:
        """Return the parsed norms, failing fast when the file is missing or malformed."""
        if not self._editorial_norms_path.is_file():
            raise EditorialNormsFileNotFound(str(self._editorial_norms_path))
        try:
            with self._editorial_norms_path.open("rb") as editorial_norms_file:
                return load(editorial_norms_file)
        except TOMLDecodeError as error:
            raise EditorialNormsFileInvalid(f"{self._editorial_norms_path}: {error}") from error
