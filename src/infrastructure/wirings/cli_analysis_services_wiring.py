from collections.abc import Mapping
from pathlib import Path

from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.application.export_report_use_case import ExportReportUseCase
from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.wirings.ensure_language_model_server_use_case_wiring import (
    EnsureLanguageModelServerUseCaseWiring,
)
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.html_report_wiring import HtmlReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring
from src.infrastructure.wirings.overridable_analyze_document_use_case_wiring import (
    OverridableAnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.overridable_warm_up_language_model_use_case_wiring import (
    OverridableWarmUpLanguageModelUseCaseWiring,
)
from src.infrastructure.wirings.release_language_model_server_use_case_wiring import (
    ReleaseLanguageModelServerUseCaseWiring,
)


class CliAnalysisServicesWiring:
    """Composition root for the services of one command line analysis run."""

    def __init__(
        self,
        environment_overrides: Mapping[str, str | None],
        prompt_file_overrides: Mapping[str, Path | None] | None = None,
        prompts_root: Path | None = None,
    ) -> None:
        """Keep the overrides and the custom prompts root applied to this run."""
        self._environment_overrides = environment_overrides
        self._prompt_file_overrides = prompt_file_overrides
        self._prompts_root = prompts_root

    def create_services(self) -> CliAnalysisServices:
        """Return the analysis and export use cases sharing one overridden configuration."""
        analyze_document_use_case_wiring = self._analyze_document_use_case_wiring()
        return CliAnalysisServices(
            analyze_document_use_case=analyze_document_use_case_wiring.create_use_case(),
            word_report_use_case=self._word_report_use_case(),
            json_report_use_case=self._json_report_use_case(),
            html_report_use_case=self._html_report_use_case(),
            ensure_language_model_server_use_case=self._ensure_language_model_server_use_case(),
            release_language_model_server_use_case=self._release_language_model_server_use_case(),
            warm_up_language_model_use_case=self._warm_up_language_model_use_case(),
            model_name=analyze_document_use_case_wiring.get_active_model_name(),
            uses_local_language_model=analyze_document_use_case_wiring.uses_local_language_model(),
            warms_up_language_model=analyze_document_use_case_wiring.warms_up_language_model(),
        )

    def _analyze_document_use_case_wiring(self) -> OverridableAnalyzeDocumentUseCaseWiring:
        return OverridableAnalyzeDocumentUseCaseWiring(
            self._environment_overrides,
            self._prompt_file_overrides,
            prompts_root=self._prompts_root,
        )

    def _ensure_language_model_server_use_case(self) -> EnsureLanguageModelServerUseCase:
        return EnsureLanguageModelServerUseCaseWiring(
            self._environment_overrides
        ).get_ensure_language_model_server_use_case()

    def _release_language_model_server_use_case(self) -> ReleaseLanguageModelServerUseCase:
        return ReleaseLanguageModelServerUseCaseWiring(
            self._environment_overrides
        ).get_release_language_model_server_use_case()

    def _warm_up_language_model_use_case(self) -> WarmUpLanguageModelUseCase:
        return OverridableWarmUpLanguageModelUseCaseWiring(
            self._environment_overrides
        ).get_warm_up_language_model_use_case()

    def _word_report_use_case(self) -> ExportReportUseCase:
        return ExportReportWiring().create_use_case()

    def _json_report_use_case(self) -> ExportReportUseCase:
        return JsonReportWiring().create_use_case()

    def _html_report_use_case(self) -> ExportReportUseCase:
        return HtmlReportWiring().create_use_case()
