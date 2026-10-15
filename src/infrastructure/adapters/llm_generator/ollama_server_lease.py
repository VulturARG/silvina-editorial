from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OllamaServerLease:
    """Represents the lease state of an Ollama server process started by the application."""

    server_process_id: int
    active_process_id: int | None
    last_use_epoch_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Convert the lease record into a plain dictionary."""
        return {
            "server_process_id": self.server_process_id,
            "active_process_id": self.active_process_id,
            "last_use_epoch_seconds": self.last_use_epoch_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OllamaServerLease":
        """Instantiate a lease record from a dictionary."""
        server_process_id = data["server_process_id"]
        active_process_id = data["active_process_id"]
        last_use_epoch_seconds = data["last_use_epoch_seconds"]
        if not isinstance(server_process_id, int):
            raise TypeError("server_process_id must be an integer")
        if active_process_id is not None and not isinstance(active_process_id, int):
            raise TypeError("active_process_id must be an integer or None")
        if not isinstance(last_use_epoch_seconds, (int, float)):
            raise TypeError("last_use_epoch_seconds must be a numeric value")
        return cls(
            server_process_id=server_process_id,
            active_process_id=active_process_id,
            last_use_epoch_seconds=float(last_use_epoch_seconds),
        )
