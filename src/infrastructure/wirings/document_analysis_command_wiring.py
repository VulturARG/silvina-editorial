from collections.abc import Callable, Mapping
from pathlib import Path

from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand
from src.infrastructure.cli.document_name_prompter import DocumentNamePrompter
from src.infrastructure.cli.report_file_paths_builder import ReportFilePathsBuilder
from src.infrastructure.cli.source_document_locator import SourceDocumentLocator
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer
from src.infrastructure.wirings.cli_analysis_services_wiring import (
    CliAnalysisServicesWiring,
)


class DocumentAnalysisCommandWiring:
    """Composition root for the command line document analysis."""

    def create_command(self) -> DocumentAnalysisCommand:
        """Return the command wired with the console adapters and the analysis services factory."""
        return DocumentAnalysisCommand(
            document_name_prompter=self._document_name_prompter(),
            source_document_locator=self._source_document_locator(),
            report_file_paths_builder=self._report_file_paths_builder(),
            console_step_announcer=self._console_step_announcer(),
            services_factory=self._services_factory(),
        )

    def _document_name_prompter(self) -> DocumentNamePrompter:
        return DocumentNamePrompter()

    def _source_document_locator(self) -> SourceDocumentLocator:
        return SourceDocumentLocator()

    def _report_file_paths_builder(self) -> ReportFilePathsBuilder:
        return ReportFilePathsBuilder(file_name_sanitizer=WindowsFileNameSanitizer())

    def _console_step_announcer(self) -> ConsoleStepAnnouncer:
        return ConsoleStepAnnouncer()

    def _services_factory(
        self,
    ) -> Callable[[Mapping[str, str | None], Mapping[str, Path | None]], CliAnalysisServices]:
        return self._create_services

    def _create_services(
        self,
        environment_overrides: Mapping[str, str | None],
        prompt_file_overrides: Mapping[str, Path | None],
    ) -> CliAnalysisServices:
        return CliAnalysisServicesWiring(
            environment_overrides, prompt_file_overrides
        ).create_services()
