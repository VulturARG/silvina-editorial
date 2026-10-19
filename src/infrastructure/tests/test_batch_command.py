from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

from src.infrastructure.cli.batch_command import BatchCommand
from src.infrastructure.cli.batch_file_reader import BatchFileReader
from src.infrastructure.cli.batch_plan import BatchPlan
from src.infrastructure.cli.batch_runner import BatchRunner
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand


class TestBatchCommand(TestCase):
    BATCH_FILE_PATH = Path("batches/main.toml")

    def setUp(self):
        self._printed_lines: list[str] = []
        self._batch_file_reader = MagicMock(spec=BatchFileReader)
        self._batch_plan = BatchPlan(runs=())
        self._batch_file_reader.read.return_value = self._batch_plan
        self._batch_runner = MagicMock(spec=BatchRunner)
        self._batch_runner.run.return_value = DocumentAnalysisCommand.SUCCESS_STATUS
        self._command = BatchCommand(
            batch_file_reader=self._batch_file_reader,
            batch_runner=self._batch_runner,
            console_step_announcer=ConsoleStepAnnouncer(write_function=self._printed_lines.append),
        )

    def _printed_text(self) -> str:
        return "\n".join(self._printed_lines)

    def test_reads_the_given_batch_file_and_runs_its_plan(self):
        self._command.run(self.BATCH_FILE_PATH)

        self._batch_file_reader.read.assert_called_once_with(self.BATCH_FILE_PATH)
        self._batch_runner.run.assert_called_once_with(self._batch_plan)

    def test_returns_runner_status_unchanged(self):
        for runner_status in (
            DocumentAnalysisCommand.SUCCESS_STATUS,
            DocumentAnalysisCommand.FAILURE_STATUS,
            DocumentAnalysisCommand.INTERRUPTED_STATUS,
        ):
            with self.subTest(runner_status=runner_status):
                self._batch_runner.run.return_value = runner_status

                status = self._command.run(self.BATCH_FILE_PATH)

                self.assertEqual(status, runner_status)

    def test_read_errors_return_failure_status_without_running_and_name_file_and_error(self):
        for read_error in (
            OSError("file not found"),
            ValueError("invalid TOML"),
            TypeError("unknown field"),
        ):
            with self.subTest(read_error=type(read_error).__name__):
                self._batch_file_reader.read.side_effect = read_error

                status = self._command.run(self.BATCH_FILE_PATH)

                self.assertEqual(status, DocumentAnalysisCommand.FAILURE_STATUS)
                self._batch_runner.run.assert_not_called()
                self.assertIn(str(self.BATCH_FILE_PATH), self._printed_text())
                self.assertIn(str(read_error), self._printed_text())

    def test_keyboard_interrupt_while_reading_returns_interrupted_status(self):
        self._batch_file_reader.read.side_effect = KeyboardInterrupt

        status = self._command.run(self.BATCH_FILE_PATH)

        self.assertEqual(status, DocumentAnalysisCommand.INTERRUPTED_STATUS)
        self.assertIn(DocumentAnalysisCommand.INTERRUPTED_MESSAGE, self._printed_text())
        self._batch_runner.run.assert_not_called()

    def test_keyboard_interrupt_while_running_returns_interrupted_status(self):
        self._batch_runner.run.side_effect = KeyboardInterrupt

        status = self._command.run(self.BATCH_FILE_PATH)

        self.assertEqual(status, DocumentAnalysisCommand.INTERRUPTED_STATUS)
        self.assertIn(DocumentAnalysisCommand.INTERRUPTED_MESSAGE, self._printed_text())

    def test_other_read_exceptions_propagate(self):
        self._batch_file_reader.read.side_effect = RuntimeError("unexpected")

        with self.assertRaises(RuntimeError):
            self._command.run(self.BATCH_FILE_PATH)

    def test_other_run_exceptions_propagate(self):
        self._batch_runner.run.side_effect = RuntimeError("unexpected")

        with self.assertRaises(RuntimeError):
            self._command.run(self.BATCH_FILE_PATH)
