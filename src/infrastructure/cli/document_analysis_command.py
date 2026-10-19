from collections.abc import Callable, Mapping
from logging import getLogger
from pathlib import Path

from src.application.export_report_use_case import ExportReportUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.document_errors import DocumentInvalidType, DocumentNotFound
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_name_prompter import DocumentNamePrompter
from src.infrastructure.cli.report_file_paths import ReportFilePaths
from src.infrastructure.cli.report_file_paths_builder import ReportFilePathsBuilder
from src.infrastructure.cli.source_document_locator import SourceDocumentLocator

logger = getLogger(__name__)


class DocumentAnalysisCommand:
    """Analyze a Word document from the command line and export its Word, JSON and HTML reports."""

    SUCCESS_STATUS = 0
    FAILURE_STATUS = 1
    INVALID_DOCUMENT_STATUS = 2
    INTERRUPTED_STATUS = 130
    WORD_SAVE_FAILED_MESSAGE = "No se pudo guardar el informe Word (DOCX)"
    JSON_SAVE_FAILED_MESSAGE = "No se pudo guardar el informe JSON"
    HTML_SAVE_FAILED_MESSAGE = "No se pudo guardar el informe HTML"
    MISSING_DOCUMENT_NAME_MESSAGE = "No se indicó el nombre del documento"
    INTERRUPTED_MESSAGE = "Análisis interrumpido por el usuario"
    RELEASE_FAILED_MESSAGE = "No se pudo liberar el servidor del modelo de lenguaje"

    def __init__(
        self,
        document_name_prompter: DocumentNamePrompter,
        source_document_locator: SourceDocumentLocator,
        report_file_paths_builder: ReportFilePathsBuilder,
        console_step_announcer: ConsoleStepAnnouncer,
        services_factory: Callable[
            [Mapping[str, str | None], Mapping[str, Path | None], Path | None],
            CliAnalysisServices,
        ],
    ) -> None:
        """Keep the collaborators used by each step of the analysis run."""
        self._document_name_prompter = document_name_prompter
        self._source_document_locator = source_document_locator
        self._report_file_paths_builder = report_file_paths_builder
        self._console_step_announcer = console_step_announcer
        self._services_factory = services_factory

    def run(self, arguments: CommandLineArguments) -> int:
        """Run every step of the analysis and return the process exit status."""
        try:
            return self._run_steps(arguments)
        except KeyboardInterrupt:
            self._console_step_announcer.announce_error(self.INTERRUPTED_MESSAGE)
            return self.INTERRUPTED_STATUS

    def _run_steps(self, arguments: CommandLineArguments) -> int:
        document_name = self._resolve_document_name(arguments)
        if not document_name.strip():
            self._console_step_announcer.announce_error(self.MISSING_DOCUMENT_NAME_MESSAGE)
            return self.INVALID_DOCUMENT_STATUS
        try:
            document_path = self._locate_document(document_name, arguments.input_directory)
        except DocumentNotFound as error:
            self._console_step_announcer.announce_error(f"El documento no existe: {error.detail}")
            return self.INVALID_DOCUMENT_STATUS
        except DocumentInvalidType as error:
            self._console_step_announcer.announce_error(
                f"El documento debe ser un archivo Word (.docx): {error.detail}"
            )
            return self.INVALID_DOCUMENT_STATUS
        try:
            with self._console_step_announcer.step(
                "Preparando la configuración y los casos de uso"
            ):
                services = self._services_factory(
                    arguments.environment_overrides(),
                    arguments.prompt_file_overrides(),
                    arguments.prompts_directory,
                )
        except Exception as error:
            self._console_step_announcer.announce_error(self._describe_error(error))
            return self.FAILURE_STATUS
        logger.info("Prompt source: %s", services.prompt_source.describe())
        try:
            try:
                status = self._analyze_and_export(
                    services, document_path, arguments.output_directory
                )
            except BaseSrcError as error:
                self._console_step_announcer.announce_error(error.dict()["error"])
                status = self.FAILURE_STATUS
            except Exception as error:
                self._console_step_announcer.announce_error(f"Error inesperado: {error}")
                status = self.FAILURE_STATUS
        finally:
            release_succeeded = self._release_language_model_server(services)
        if status == self.SUCCESS_STATUS and not release_succeeded:
            return self.FAILURE_STATUS
        return status

    def _resolve_document_name(self, arguments: CommandLineArguments) -> str:
        if arguments.document_name is not None:
            return arguments.document_name
        with self._console_step_announcer.step("Solicitando el nombre del documento"):
            document_name = self._document_name_prompter.ask()
        return document_name

    def _locate_document(self, document_name: str, input_directory: Path | None) -> Path:
        with self._console_step_announcer.step("Validando el documento"):
            document_path = self._source_document_locator.locate(document_name, input_directory)
        return document_path

    def _analyze_and_export(
        self,
        services: CliAnalysisServices,
        document_path: Path,
        output_directory: Path | None,
    ) -> int:
        report_file_paths = self._build_report_file_paths(
            document_path, output_directory, services.model_name, services.prompt_source
        )
        if services.uses_local_language_model:
            with self._console_step_announcer.step(
                "Verificando el servidor del modelo de lenguaje"
            ):
                services.ensure_language_model_server_use_case.execute()
        if services.warms_up_language_model:
            with self._console_step_announcer.step("Precargando el modelo de lenguaje"):
                services.warm_up_language_model_use_case.execute()
        with self._console_step_announcer.step("Analizando el documento"):
            report = services.analyze_document_use_case.execute(
                document_path=str(document_path),
                document_name=document_path.name,
            )
        self._create_output_directory(report_file_paths)
        if not self._export_report(
            "Guardando el informe Word",
            services.word_report_use_case,
            report,
            report_file_paths.word_path,
        ):
            self._console_step_announcer.announce_error(self.WORD_SAVE_FAILED_MESSAGE)
            return self.FAILURE_STATUS
        if not self._export_report(
            "Guardando el informe JSON",
            services.json_report_use_case,
            report,
            report_file_paths.json_path,
        ):
            self._console_step_announcer.announce_error(self.JSON_SAVE_FAILED_MESSAGE)
            return self.FAILURE_STATUS
        if not self._export_report(
            "Guardando el informe HTML",
            services.html_report_use_case,
            report,
            report_file_paths.html_path,
        ):
            self._console_step_announcer.announce_error(self.HTML_SAVE_FAILED_MESSAGE)
            return self.FAILURE_STATUS
        self._console_step_announcer.announce_completion(
            [report_file_paths.word_path, report_file_paths.json_path, report_file_paths.html_path]
        )
        return self.SUCCESS_STATUS

    def _build_report_file_paths(
        self,
        document_path: Path,
        output_directory: Path | None,
        model_name: str,
        prompt_source: PromptSourceDTO,
    ) -> ReportFilePaths:
        with self._console_step_announcer.step("Calculando las rutas de los informes"):
            report_file_paths = self._report_file_paths_builder.build(
                document_path, output_directory, model_name, prompt_source
            )
        return report_file_paths

    def _create_output_directory(self, report_file_paths: ReportFilePaths) -> None:
        with self._console_step_announcer.step("Creando el directorio de salida"):
            report_file_paths.word_path.parent.mkdir(parents=True, exist_ok=True)

    def _export_report(
        self,
        step_description: str,
        export_use_case: ExportReportUseCase,
        report: ReportInputDTO,
        output_path: Path,
    ) -> bool:
        self._console_step_announcer.announce_start(step_description)
        was_exported = export_use_case.execute(report_input=report, output_path=str(output_path))
        if was_exported:
            self._console_step_announcer.announce_finish(step_description)
        return was_exported

    def _release_language_model_server(self, services: CliAnalysisServices) -> bool:
        """Release the language model server and return whether the release succeeded."""
        try:
            services.release_language_model_server_use_case.execute()
        except Exception as error:
            logger.exception("Language model server release failed")
            self._console_step_announcer.announce_error(
                f"{self.RELEASE_FAILED_MESSAGE}: {self._describe_error(error)}"
            )
            return False
        return True

    @staticmethod
    def _describe_error(error: Exception) -> str:
        if isinstance(error, BaseSrcError):
            return error.dict()["error"]
        return str(error)
