from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.infrastructure.cli.ollama_idle_shutdown_watcher_main import main


class TestOllamaIdleShutdownWatcherMain(TestCase):
    def test_main_parses_arguments_and_runs_watcher(self):
        with patch(
            "src.infrastructure.cli.ollama_idle_shutdown_watcher_main.OllamaIdleShutdownWatcherWiring"
        ) as mock_wiring_class:
            mock_watcher = MagicMock()
            mock_wiring_class.return_value.create_watcher.return_value = mock_watcher

            main(
                [
                    "--server-process-id",
                    "1234",
                    "--idle-seconds",
                    "150.0",
                    "--poll-interval-seconds",
                    "5.0",
                    "--lease-file",
                    "custom/path/lease.json",
                ]
            )

        mock_wiring_class.assert_called_once_with(
            server_process_id=1234,
            idle_seconds=150.0,
            poll_interval_seconds=5.0,
            lease_file_path=Path("custom/path/lease.json"),
        )
        mock_watcher.run.assert_called_once()
