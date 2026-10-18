from pathlib import Path

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.cli.report_file_paths import ReportFilePaths
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class ReportFilePathsBuilder:
    """Compute where the reports of a document are written, without touching the disk."""

    DEFAULT_OUTPUT_DIRECTORY_NAME = "análisis"
    FILE_NAME_SUFFIX = "_analisis"
    PROMPT_SOURCE_PREFIX = "_"
    PROMPT_PART_SEPARATOR = "+"
    WORD_EXTENSION = ".docx"
    JSON_EXTENSION = ".json"
    HTML_EXTENSION = ".html"

    def __init__(self, file_name_sanitizer: WindowsFileNameSanitizer) -> None:
        """Keep the sanitizer applied to the document stem and to the model name."""
        self._file_name_sanitizer = file_name_sanitizer

    def build(
        self,
        document_path: Path,
        output_directory: Path | None,
        model_name: str,
        prompt_source: PromptSourceDTO | None = None,
    ) -> ReportFilePaths:
        """Return the report paths, defaulting to the analysis folder next to the document."""
        directory = self._resolve_directory(document_path, output_directory)
        base_name = self._build_base_name(document_path, model_name, prompt_source)
        return ReportFilePaths(
            word_path=directory / f"{base_name}{self.WORD_EXTENSION}",
            json_path=directory / f"{base_name}{self.JSON_EXTENSION}",
            html_path=directory / f"{base_name}{self.HTML_EXTENSION}",
        )

    def _resolve_directory(self, document_path: Path, output_directory: Path | None) -> Path:
        if output_directory is None:
            return document_path.parent / self.DEFAULT_OUTPUT_DIRECTORY_NAME
        return output_directory

    def _build_base_name(
        self, document_path: Path, model_name: str, prompt_source: PromptSourceDTO | None
    ) -> str:
        sanitized_stem = self._file_name_sanitizer.sanitize(document_path.stem)
        base_name = f"{sanitized_stem}{self.FILE_NAME_SUFFIX}"
        sanitized_model_name = self._file_name_sanitizer.sanitize(model_name)
        if sanitized_model_name:
            base_name = f"{base_name}_{sanitized_model_name}"
        return f"{base_name}{self._build_prompt_source_suffix(prompt_source)}"

    def _build_prompt_source_suffix(self, prompt_source: PromptSourceDTO | None) -> str:
        parts = self._prompt_source_parts(prompt_source)
        if not parts:
            return ""
        return f"{self.PROMPT_SOURCE_PREFIX}{self.PROMPT_PART_SEPARATOR.join(parts)}"

    def _prompt_source_parts(self, prompt_source: PromptSourceDTO | None) -> list[str]:
        if prompt_source is None:
            return []
        raw_parts = list(prompt_source.replaced_prompt_names)
        if prompt_source.base_label != PromptSourceDTO.DEFAULT_BASE_LABEL:
            raw_parts.insert(0, prompt_source.base_label)
        sanitized_parts = [self._file_name_sanitizer.sanitize(part) for part in raw_parts]
        return [part for part in sanitized_parts if part]
