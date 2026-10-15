from json import dumps, loads
from pathlib import Path
from uuid import uuid4

from src.infrastructure.adapters.llm_generator.ollama_server_lease import (
    OllamaServerLease,
)


class OllamaServerLeaseStore:
    """Persists and retrieves the Ollama server lease metadata file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> OllamaServerLease | None:
        """Read the lease record from disk or return None if missing or corrupt."""
        if not self._path.exists():
            return None
        try:
            content = self._path.read_text(encoding="utf-8")
            if not content.strip():
                return None
            data = loads(content)
            if not isinstance(data, dict):
                return None
            return OllamaServerLease.from_dict(data)
        except (OSError, ValueError, TypeError, KeyError):
            return None

    def write(self, lease: OllamaServerLease) -> None:
        """Atomically persist the lease record to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_file_path = self._path.with_name(f"{self._path.name}.{uuid4().hex}.tmp")
        try:
            temporary_file_path.write_text(dumps(lease.to_dict(), indent=2), encoding="utf-8")
            temporary_file_path.replace(self._path)
        finally:
            if temporary_file_path.exists():
                try:
                    temporary_file_path.unlink()
                except OSError:
                    pass

    def clear(self) -> None:
        """Remove the lease record file if it exists."""
        try:
            self._path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass
