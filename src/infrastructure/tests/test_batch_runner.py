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

    def test_runs_every_document_of_every_run_in_order(self):
        plan = self._plan(
            ("gemma", ("a.docx", "b.docx")),
            ("qwen", ("a.docx", "c.docx")),
        )

        self._runner.run(plan)

        self.assertEqual(
            self._analysis_command.run.call_args_list,
            [
                call(self._arguments_of(plan, 0, 0)),
                call(self._arguments_of(plan, 0, 1)),
                call(self._arguments_of(plan, 1, 0)),
                call(self._arguments_of(plan, 1, 1)),
            ],
        )

    def test_passes_the_same_argument_objects_of_the_plan_to_the_command(self):
        plan = self._plan(("gemma", ("a.docx",)))

        self._runner.run(plan)

        passed_arguments = self._analysis_command.run.call_args.args[0]
        self.assertIs(passed_arguments, plan.runs[0].document_arguments[0])

    def test_returns_success_status_when_every_document_succeeds(self):
        plan = self._plan(("gemma", ("a.docx", "b.docx")), ("qwen", ("a.docx",)))

        status = self._runner.run(plan)

        self.assertEqual(status, DocumentAnalysisCommand.SUCCESS_STATUS)

    def test_stops_at_first_failure_without_running_remaining_documents_or_runs(self):
        self._analysis_command.run.side_effect = [0, 1, 0, 0]
        plan = self._plan(("gemma", ("a.docx", "b.docx", "c.docx")), ("qwen", ("a.docx",)))

        status = self._runner.run(plan)

        self.assertEqual(status, 1)
        self.assertEqual(self._analysis_command.run.call_count, 2)

    def test_returns_failure_status_unchanged(self):
        plan = self._plan(("gemma", ("a.docx", "b.docx")))
        for failure_status in (1, 2, DocumentAnalysisCommand.INTERRUPTED_STATUS):
            with self.subTest(failure_status=failure_status):
                self._analysis_command.reset_mock()
                self._analysis_command.run.side_effect = [0, failure_status]

                status = self._runner.run(plan)

                self.assertEqual(status, failure_status)
                self.assertEqual(self._analysis_command.run.call_count, 2)

    def test_failure_announcement_names_run_document_and_status(self):
        self._analysis_command.run.side_effect = [0, 2]
        plan = self._plan(("gemma-7b", ("a.docx", "tesis.docx")))

        self._runner.run(plan)

        failure_line = self._printed_lines[-1]
        self.assertTrue(failure_line.startswith("❌ "))
        self.assertIn("tesis.docx", failure_line)
        self.assertIn("gemma-7b", failure_line)
        self.assertIn("(1/1)", failure_line)
        self.assertIn("estado 2", failure_line)

    def test_failed_document_is_not_announced_as_finished(self):
        self._analysis_command.run.side_effect = [1]
        plan = self._plan(("gemma", ("tesis.docx",)))

        self._runner.run(plan)

        self.assertFalse(any(line.startswith("✅ ") for line in self._printed_lines))

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

    def test_exception_from_command_propagates_and_stops_the_batch(self):
        self._analysis_command.run.side_effect = [0, RuntimeError("fallo inesperado")]
        plan = self._plan(("gemma", ("a.docx", "b.docx", "c.docx")))

        with self.assertRaises(RuntimeError):
            self._runner.run(plan)

        self.assertEqual(self._analysis_command.run.call_count, 2)

    def test_keyboard_interrupt_from_command_propagates_and_stops_the_batch(self):
        self._analysis_command.run.side_effect = [0, KeyboardInterrupt()]
        plan = self._plan(("gemma", ("a.docx", "b.docx", "c.docx")), ("qwen", ("a.docx",)))

        with self.assertRaises(KeyboardInterrupt):
            self._runner.run(plan)

        self.assertEqual(self._analysis_command.run.call_count, 2)

    def test_empty_plan_returns_success_and_never_runs_the_command(self):
        status = self._runner.run(BatchPlan(runs=()))

        self.assertEqual(status, DocumentAnalysisCommand.SUCCESS_STATUS)
        self._analysis_command.run.assert_not_called()
        self.assertEqual(self._printed_lines, [])

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
