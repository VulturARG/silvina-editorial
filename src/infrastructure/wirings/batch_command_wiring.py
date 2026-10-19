from src.infrastructure.cli.batch_command import BatchCommand
from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector
from src.infrastructure.cli.batch_file_reader import BatchFileReader
from src.infrastructure.cli.batch_runner import BatchRunner
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand
from src.infrastructure.wirings.document_analysis_command_wiring import (
    DocumentAnalysisCommandWiring,
)


class BatchCommandWiring:
    """Composition root for the batch analysis command."""

    def create_command(self) -> BatchCommand:
        """Return the batch command wired with the batch reader, the runner and the announcer."""
        return BatchCommand(
            batch_file_reader=self._batch_file_reader(),
            batch_runner=self._batch_runner(),
            console_step_announcer=self._console_step_announcer(),
        )

    def _batch_file_reader(self) -> BatchFileReader:
        return BatchFileReader(document_selector=self._batch_document_selector())

    def _batch_document_selector(self) -> BatchDocumentSelector:
        return BatchDocumentSelector()

    def _batch_runner(self) -> BatchRunner:
        return BatchRunner(
            analysis_command=self._document_analysis_command(),
            console_step_announcer=self._console_step_announcer(),
        )

    def _document_analysis_command(self) -> DocumentAnalysisCommand:
        return DocumentAnalysisCommandWiring().create_command()

    def _console_step_announcer(self) -> ConsoleStepAnnouncer:
        return ConsoleStepAnnouncer()
