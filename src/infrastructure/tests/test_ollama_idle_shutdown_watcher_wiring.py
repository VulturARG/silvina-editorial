from pathlib import Path
from unittest import TestCase

from src.infrastructure.adapters.llm_generator.ollama_idle_shutdown_watcher import (
    OllamaIdleShutdownWatcher,
)
from src.infrastructure.wirings.ollama_idle_shutdown_watcher_wiring import (
    OllamaIdleShutdownWatcherWiring,
)


class TestOllamaIdleShutdownWatcherWiring(TestCase):
    def test_create_watcher_assembles_idle_shutdown_watcher(self):
        lease_path = Path("custom/lease.json")
        wiring = OllamaIdleShutdownWatcherWiring(
            server_process_id=5432,
            idle_seconds=120.0,
            poll_interval_seconds=5.0,
            lease_file_path=lease_path,
        )

        watcher = wiring.create_watcher()

        self.assertIsInstance(watcher, OllamaIdleShutdownWatcher)
        self.assertEqual(watcher._server_process_id, 5432)
        self.assertEqual(watcher._idle_seconds, 120.0)
        self.assertEqual(watcher._poll_interval_seconds, 5.0)
        self.assertEqual(watcher._lease_store._path, lease_path)
