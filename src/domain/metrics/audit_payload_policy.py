from hashlib import sha256

from src.domain.enums.app_mode import AppMode


class AuditPayloadPolicy:
    """Policy governing payload redaction based on application operational mode."""

    def __init__(self, app_mode: AppMode) -> None:
        self._app_mode = app_mode

    def apply(self, payload: str) -> str:
        """Apply redaction policy to payload based on application operational mode."""
        if self._app_mode == AppMode.DEBUG:
            return payload

        character_count = len(payload)
        payload_hash = sha256(payload.encode("utf-8", errors="replace")).hexdigest()
        return f"[REDACTED chars={character_count} sha256={payload_hash}]"
