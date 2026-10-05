from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.domain.exceptions.language_model_errors import LanguageModelNotFound
from src.infrastructure.fastapi.src.utils.language_model_warm_up_starter import (
    LanguageModelWarmUpStarter,
)

LOGGER_NAME = "src.infrastructure.fastapi.src.utils.language_model_warm_up_starter"


class TestLanguageModelWarmUpStarter(TestCase):
    @patch("src.infrastructure.fastapi.src.utils.language_model_warm_up_starter.Thread")
    def test_start_builds_daemon_thread_and_starts_it_once(
        self,
        mock_thread_class: MagicMock,
    ) -> None:
        mock_use_case = MagicMock()
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        starter = LanguageModelWarmUpStarter(mock_use_case)
        returned_thread = starter.start()

        mock_thread_class.assert_called_once_with(target=starter._run, daemon=True)
        mock_thread_instance.start.assert_called_once_with()
        self.assertIs(returned_thread, mock_thread_instance)

    def test_run_logs_warning_on_domain_error_and_does_not_raise(self) -> None:
        mock_use_case = MagicMock()
        mock_use_case.execute.side_effect = LanguageModelNotFound()

        starter = LanguageModelWarmUpStarter(mock_use_case)
        with self.assertLogs(LOGGER_NAME, level="WARNING") as captured_logs:
            starter._run()

        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("Language model warmup failed", captured_logs.output[0])
        self.assertIn(LanguageModelNotFound.MESSAGE, captured_logs.output[0])

    def test_run_logs_warning_on_unexpected_exception_and_does_not_raise(self) -> None:
        mock_use_case = MagicMock()
        mock_use_case.execute.side_effect = RuntimeError("Ollama connection broke")

        starter = LanguageModelWarmUpStarter(mock_use_case)
        with self.assertLogs(LOGGER_NAME, level="WARNING") as captured_logs:
            starter._run()

        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("Language model warmup failed unexpectedly", captured_logs.output[0])
        self.assertIn("Ollama connection broke", captured_logs.output[0])

    def test_run_logs_no_warning_on_successful_execute(self) -> None:
        mock_use_case = MagicMock()

        starter = LanguageModelWarmUpStarter(mock_use_case)
        with self.assertNoLogs(LOGGER_NAME, level="WARNING"):
            starter._run()

        mock_use_case.execute.assert_called_once_with()
