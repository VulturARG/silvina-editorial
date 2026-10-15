from signal import SIGTERM
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.llm_generator.process_tree_terminator import (
    ProcessTreeTerminator,
)
from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NO_WINDOW,
)


class TestProcessTreeTerminator(TestCase):
    def test_windows_terminates_process_tree_with_taskkill(self):
        fake_runner = MagicMock()
        terminator = ProcessTreeTerminator(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_tree_terminator.name", "nt"):
            terminator.terminate(12345)

        fake_runner.assert_called_once_with(
            ["taskkill", "/PID", "12345", "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )

    def test_windows_termination_failure_is_logged_and_not_raised(self):
        fake_runner = MagicMock(side_effect=OSError("taskkill execution failed"))
        terminator = ProcessTreeTerminator(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_tree_terminator.name", "nt"):
            with self.assertLogs(
                "src.infrastructure.adapters.llm_generator.process_tree_terminator",
                level="WARNING",
            ) as captured_logs:
                terminator.terminate(12345)

        self.assertEqual(len(captured_logs.records), 1)
        self.assertIn("12345", captured_logs.output[0])

    def test_posix_terminates_process_group_with_sigterm(self):
        fake_getpgid = MagicMock(return_value=999)
        fake_killpg = MagicMock()
        terminator = ProcessTreeTerminator(
            get_process_group_id_function=fake_getpgid,
            kill_process_group_function=fake_killpg,
        )

        with patch(
            "src.infrastructure.adapters.llm_generator.process_tree_terminator.name", "posix"
        ):
            terminator.terminate(12345)

        fake_getpgid.assert_called_once_with(12345)
        fake_killpg.assert_called_once_with(999, SIGTERM)

    def test_posix_termination_failure_is_logged_and_not_raised(self):
        fake_getpgid = MagicMock(side_effect=ProcessLookupError("no such process"))
        fake_killpg = MagicMock()
        terminator = ProcessTreeTerminator(
            get_process_group_id_function=fake_getpgid,
            kill_process_group_function=fake_killpg,
        )

        with patch(
            "src.infrastructure.adapters.llm_generator.process_tree_terminator.name", "posix"
        ):
            with self.assertLogs(
                "src.infrastructure.adapters.llm_generator.process_tree_terminator",
                level="WARNING",
            ) as captured_logs:
                terminator.terminate(12345)

        self.assertEqual(len(captured_logs.records), 1)
        self.assertIn("12345", captured_logs.output[0])
