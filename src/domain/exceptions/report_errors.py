from src.domain.exceptions.base_src_error import SrcBaseWarning


class ReportExportWarning(SrcBaseWarning):
    """Base class for all Report Export warnings."""


class ReportExportUnavailable(ReportExportWarning):
    """Raised when the report export service cannot start (python-docx not installed)."""

    MESSAGE = "The report export service is unavailable (python-docx not installed)."
