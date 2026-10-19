from pathlib import Path

from src.infrastructure.cli.batch_file_reader import BatchFileReader
from src.infrastructure.cli.batch_runner import BatchRunner
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand


class BatchCommand:
    """Read a batch file and run its plan, reporting the errors that stop the batch."""

    READ_FAILED_MESSAGE = "No se pudo leer el archivo de lote"

    def __init__(
        self,
        batch_file_reader: BatchFileReader,
        batch_runner: BatchRunner,
        console_step_announcer: ConsoleStepAnnouncer,
    ) -> None:
        """Keep the reader that builds the plan, the runner that executes it and the announcer."""
        self._batch_file_reader = batch_file_reader
        self._batch_runner = batch_runner
        self._console_step_announcer = console_step_announcer

    def run(self, batch_file_path: Path) -> int:
        """Run the batch file and return the process exit status."""
        try:
            return self._read_and_run(batch_file_path)
        except KeyboardInterrupt:
            self._console_step_announcer.announce_error(DocumentAnalysisCommand.INTERRUPTED_MESSAGE)
            return DocumentAnalysisCommand.INTERRUPTED_STATUS

    def _read_and_run(self, batch_file_path: Path) -> int:
        try:
            plan = self._batch_file_reader.read(batch_file_path)
        except (OSError, ValueError, TypeError) as error:
            self._console_step_announcer.announce_error(
                f"{self.READ_FAILED_MESSAGE} '{batch_file_path}': {error}"
            )
            return DocumentAnalysisCommand.FAILURE_STATUS
        return self._batch_runner.run(plan)
