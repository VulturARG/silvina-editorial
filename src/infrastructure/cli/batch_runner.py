from src.infrastructure.cli.batch_plan import BatchPlan
from src.infrastructure.cli.batch_run import BatchRun
from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand


class BatchRunner:
    """Analyze every document of a batch plan in order and stop at the first failure."""

    def __init__(
        self,
        analysis_command: DocumentAnalysisCommand,
        console_step_announcer: ConsoleStepAnnouncer,
    ) -> None:
        """Keep the analysis command reused for every document and the console announcer."""
        self._analysis_command = analysis_command
        self._console_step_announcer = console_step_announcer

    def run(self, plan: BatchPlan) -> int:
        """Analyze every document of every run and return the first failing status, or success."""
        run_count = len(plan.runs)
        for run_position, run in enumerate(plan.runs, start=1):
            for arguments in run.document_arguments:
                analysis_label = self._analysis_label(run, run_position, run_count, arguments)
                status = self._analyze_document(analysis_label, arguments)
                if status != DocumentAnalysisCommand.SUCCESS_STATUS:
                    self._console_step_announcer.announce_error(
                        f"Se detiene el lote: fallo en el análisis de {analysis_label}, "
                        f"estado {status}"
                    )
                    return status
        return DocumentAnalysisCommand.SUCCESS_STATUS

    def _analyze_document(self, analysis_label: str, arguments: CommandLineArguments) -> int:
        self._console_step_announcer.announce_start(f"Análisis de {analysis_label}")
        try:
            status = self._analysis_command.run(arguments)
        except Exception as error:
            self._console_step_announcer.announce_error(
                f"Se detiene el lote: error en el análisis de {analysis_label}: {error}"
            )
            raise
        if status == DocumentAnalysisCommand.SUCCESS_STATUS:
            self._console_step_announcer.announce_finish(f"Análisis de {analysis_label}")
        return status

    @staticmethod
    def _analysis_label(
        run: BatchRun,
        run_position: int,
        run_count: int,
        arguments: CommandLineArguments,
    ) -> str:
        return (
            f"{arguments.document_name} con la configuración {run.name} "
            f"({run_position}/{run_count})"
        )
