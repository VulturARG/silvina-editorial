from subprocess import CompletedProcess
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NO_WINDOW,
)


class TestProcessInspector(TestCase):
    def test_windows_process_alive_returns_true_and_image_name(self):
        fake_runner = MagicMock()
        fake_runner.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout='"ollama.exe","12345","Console","1","50,000 K"\n',
            stderr="",
        )
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "nt"):
            is_alive = inspector.is_alive(12345)
            image_name = inspector.image_name(12345)

        self.assertTrue(is_alive)
        self.assertEqual(image_name, "ollama.exe")
        fake_runner.assert_called_with(
            ["tasklist", "/FI", "PID eq 12345", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )

    def test_windows_process_not_alive_when_no_tasks_info_message(self):
        fake_runner = MagicMock()
        fake_runner.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout="INFO: No tasks are running which match the specified criteria.\n",
            stderr="",
        )
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "nt"):
            is_alive = inspector.is_alive(99999)
            image_name = inspector.image_name(99999)

        self.assertFalse(is_alive)
        self.assertIsNone(image_name)

    def test_windows_process_not_alive_when_spanish_info_message(self):
        fake_runner = MagicMock()
        fake_runner.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout="INFORMACIÓN: no hay tareas ejecutándose que coincidan con los criterios especificados.\n",
            stderr="",
        )
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "nt"):
            is_alive = inspector.is_alive(99999)
            image_name = inspector.image_name(99999)

        self.assertFalse(is_alive)
        self.assertIsNone(image_name)

    def test_windows_process_not_alive_when_runner_raises_os_error(self):
        fake_runner = MagicMock(side_effect=OSError("command not found"))
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "nt"):
            is_alive = inspector.is_alive(12345)
            image_name = inspector.image_name(12345)

        self.assertFalse(is_alive)
        self.assertIsNone(image_name)

    def test_posix_process_alive_returns_true_and_image_name(self):
        fake_runner = MagicMock()
        fake_runner.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout="ollama\n",
            stderr="",
        )
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "posix"):
            is_alive = inspector.is_alive(12345)
            image_name = inspector.image_name(12345)

        self.assertTrue(is_alive)
        self.assertEqual(image_name, "ollama")
        fake_runner.assert_called_with(
            ["ps", "-p", "12345", "-o", "comm="],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_posix_process_not_alive_when_ps_exits_with_error(self):
        fake_runner = MagicMock()
        fake_runner.return_value = CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="error",
        )
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "posix"):
            is_alive = inspector.is_alive(99999)
            image_name = inspector.image_name(99999)

        self.assertFalse(is_alive)
        self.assertIsNone(image_name)

    def test_posix_process_not_alive_when_runner_raises_os_error(self):
        fake_runner = MagicMock(side_effect=OSError("ps not found"))
        inspector = ProcessInspector(command_runner=fake_runner)

        with patch("src.infrastructure.adapters.llm_generator.process_inspector.name", "posix"):
            is_alive = inspector.is_alive(12345)
            image_name = inspector.image_name(12345)

        self.assertFalse(is_alive)
        self.assertIsNone(image_name)
