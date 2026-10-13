from pathlib import Path

from src.infrastructure.cli.report_file_paths import ReportFilePaths
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class ReportFilePathsBuilder:
    """Compute where the reports of a document are written, without touching the disk."""

    DEFAULT_OUTPUT_DIRECTORY_NAME = "análisis"
    FILE_NAME_SUFFIX = "_analisis"
    WORD_EXTENSION = ".docx"
    JSON_EXTENSION = ".json"
    HTML_EXTENSION = ".html"

    def __init__(self, file_name_sanitizer: WindowsFileNameSanitizer) -> None:
        """Keep the sanitizer applied to the document stem and to the model name."""
        self._file_name_sanitizer = file_name_sanitizer

    def build(
        self, document_path: Path, output_directory: Path | None, model_name: str
    ) -> ReportFilePaths:
        """Return the report paths, defaulting to the analysis folder next to the document."""
        directory = self._resolve_directory(document_path, output_directory)
        base_name = self._build_base_name(document_path, model_name)
        return ReportFilePaths(
            word_path=directory / f"{base_name}{self.WORD_EXTENSION}",
            json_path=directory / f"{base_name}{self.JSON_EXTENSION}",
            html_path=directory / f"{base_name}{self.HTML_EXTENSION}",
        )

    def _resolve_directory(self, document_path: Path, output_directory: Path | None) -> Path:
        if output_directory is None:
            return document_path.parent / self.DEFAULT_OUTPUT_DIRECTORY_NAME
        return output_directory

    def _build_base_name(self, document_path: Path, model_name: str) -> str:
        sanitized_stem = self._file_name_sanitizer.sanitize(document_path.stem)
        base_name = f"{sanitized_stem}{self.FILE_NAME_SUFFIX}"
        sanitized_model_name = self._file_name_sanitizer.sanitize(model_name)
        if not sanitized_model_name:
            return base_name
        return f"{base_name}_{sanitized_model_name}"
