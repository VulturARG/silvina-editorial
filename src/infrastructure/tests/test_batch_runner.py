from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, call

from src.infrastructure.cli.batch_plan import BatchPlan
from src.infrastructure.cli.batch_run import BatchRun
from src.infrastructure.cli.batch_runner import BatchRunner
from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand


class TestBatchRunner(TestCase):
    def setUp(self):
        self._printed_lines: list[str] = []
        self._analysis_command = MagicMock(spec=DocumentAnalysisCommand)
        self._analysis_command.run.return_value = DocumentAnalysisCommand.SUCCESS_STATUS
        self._runner = BatchRunner(
            analysis_command=self._analysis_command,
            console_step_announcer=ConsoleStepAnnouncer(write_function=self._printed_lines.append),
        )

    def test_runs_every_document_of_every_run_in_order_and_returns_success(self):
        plan = self._plan(
            ("gemma", ("a.docx", "b.docx")),
            ("qwen", ("a.docx", "c.docx")),
        )

        status = self._runner.run(plan)

        self.assertEqual(status, DocumentAnalysisCommand.SUCCESS_STATUS)
        self.assertEqual(
            self._analysis_command.run.call_args_list,
            [
                call(self._arguments_of(plan, 0, 0)),
                call(self._arguments_of(plan, 0, 1)),
                call(self._arguments_of(plan, 1, 0)),
                call(self._arguments_of(plan, 1, 1)),
            ],
        )

    def test_stops_at_first_failure_and_returns_its_status_unchanged(self):
        plan = self._plan(("gemma", ("a.docx", "b.docx", "c.docx")), ("qwen", ("a.docx",)))
        for failure_status in (
            DocumentAnalysisCommand.FAILURE_STATUS,
            DocumentAnalysisCommand.INVALID_DOCUMENT_STATUS,
            DocumentAnalysisCommand.INTERRUPTED_STATUS,
        ):
            with self.subTest(failure_status=failure_status):
                self._analysis_command.reset_mock()
                self._analysis_command.run.side_effect = [
                    DocumentAnalysisCommand.SUCCESS_STATUS,
                    failure_status,
                ]

                status = self._runner.run(plan)

                self.assertEqual(status, failure_status)
                self.assertEqual(self._analysis_command.run.call_count, 2)

    def test_failed_document_is_announced_with_its_run_and_status_but_not_as_finished(self):
        self._analysis_command.run.side_effect = [DocumentAnalysisCommand.FAILURE_STATUS]
        plan = self._plan(("gemma-7b", ("tesis.docx",)))

        self._runner.run(plan)

        self.assertEqual(
            self._printed_lines,
            [
                "⏳ Análisis de tesis.docx con la configuración gemma-7b (1/1)...",
                "❌ Se detiene el lote: fallo en el análisis de tesis.docx con la configuración "
                "gemma-7b (1/1), estado 1",
            ],
        )

    def test_announces_start_and_finish_of_each_successful_document(self):
        plan = self._plan(("gemma", ("tesis.docx",)), ("qwen", ("tesis.docx",)))

        self._runner.run(plan)

        self.assertEqual(
            self._printed_lines,
            [
                "⏳ Análisis de tesis.docx con la configuración gemma (1/2)...",
                "✅ Análisis de tesis.docx con la configuración gemma (1/2): terminado",
                "⏳ Análisis de tesis.docx con la configuración qwen (2/2)...",
                "✅ Análisis de tesis.docx con la configuración qwen (2/2): terminado",
            ],
        )

    def test_announces_each_document_before_the_command_runs_it(self):
        lines_seen_by_command: list[list[str]] = []
        self._analysis_command.run.side_effect = lambda arguments: (
            lines_seen_by_command.append(list(self._printed_lines)),
            DocumentAnalysisCommand.SUCCESS_STATUS,
        )[1]
        plan = self._plan(("gemma", ("tesis.docx",)))

        self._runner.run(plan)

        self.assertEqual(
            lines_seen_by_command,
            [["⏳ Análisis de tesis.docx con la configuración gemma (1/1)..."]],
        )

    def test_exceptions_from_command_propagate_and_stop_the_batch(self):
        for error_type in (RuntimeError, KeyboardInterrupt):
            with self.subTest(error_type=error_type.__name__):
                self._analysis_command.reset_mock()
                self._analysis_command.run.side_effect = [
                    DocumentAnalysisCommand.SUCCESS_STATUS,
                    error_type(),
                ]
                plan = self._plan(
                    ("gemma", ("a.docx", "b.docx", "c.docx")),
                    ("qwen", ("a.docx",)),
                )

                with self.assertRaises(error_type):
                    self._runner.run(plan)

                self.assertEqual(self._analysis_command.run.call_count, 2)

    def _plan(self, *runs: tuple[str, tuple[str, ...]]) -> BatchPlan:
        return BatchPlan(
            runs=tuple(
                BatchRun(
                    name=run_name,
                    document_arguments=tuple(
                        CommandLineArguments(
                            document_name=document_name,
                            input_directory=Path("entrada"),
                        )
                        for document_name in document_names
                    ),
                )
                for run_name, document_names in runs
            )
        )

    @staticmethod
    def _arguments_of(plan: BatchPlan, run_index: int, document_index: int) -> CommandLineArguments:
        return plan.runs[run_index].document_arguments[document_index]
