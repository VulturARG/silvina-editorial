from collections.abc import Mapping
from pathlib import Path

from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.html_report_wiring import HtmlReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring
from src.infrastructure.wirings.overridable_analyze_document_use_case_wiring import (
    OverridableAnalyzeDocumentUseCaseWiring,
)


class CliAnalysisServicesWiring:
    """Composition root for the services of one command line analysis run."""

    def __init__(
        self,
        environment_overrides: Mapping[str, str | None],
        prompt_file_overrides: Mapping[str, Path | None] | None = None,
    ) -> None:
        """Keep the overrides applied to the configuration and prompts of this run."""
        self._environment_overrides = environment_overrides
        self._prompt_file_overrides = prompt_file_overrides

    def create_services(self) -> CliAnalysisServices:
        """Return the analysis and export use cases sharing one overridden configuration."""
        analyze_document_use_case_wiring = self._analyze_document_use_case_wiring()
        return CliAnalysisServices(
            analyze_document_use_case=analyze_document_use_case_wiring.create_use_case(),
            word_report_use_case=self._word_report_use_case(),
            json_report_use_case=self._json_report_use_case(),
            html_report_use_case=self._html_report_use_case(),
            model_name=analyze_document_use_case_wiring.get_active_model_name(),
        )

    def _analyze_document_use_case_wiring(self) -> OverridableAnalyzeDocumentUseCaseWiring:
        return OverridableAnalyzeDocumentUseCaseWiring(
            self._environment_overrides, self._prompt_file_overrides
        )

    def _word_report_use_case(self) -> ExportReportUseCase:
        return ExportReportWiring().create_use_case()

    def _json_report_use_case(self) -> ExportReportUseCase:
        return JsonReportWiring().create_use_case()

    def _html_report_use_case(self) -> ExportReportUseCase:
        return HtmlReportWiring().create_use_case()
