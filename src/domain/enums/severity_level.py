from enum import Enum


class SeverityLevel(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def label(self) -> str:
        """Return the Spanish label shown to the user for this severity."""
        labels = {
            SeverityLevel.INFO: "Información",
            SeverityLevel.WARNING: "Advertencia",
            SeverityLevel.ERROR: "Error",
            SeverityLevel.CRITICAL: "Crítico",
        }
        return labels[self]
