from pathlib import Path
from time import sleep, time

from src.infrastructure.adapters.llm_generator.ollama_idle_shutdown_watcher import (
    OllamaIdleShutdownWatcher,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)
from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.adapters.llm_generator.process_tree_terminator import (
    ProcessTreeTerminator,
)
from src.infrastructure.resources.project import PROJECT_ROOT_DIR


class OllamaIdleShutdownWatcherWiring:
    """Assembles the collaborators required by the Ollama idle shutdown watcher."""

    DEFAULT_IDLE_SECONDS: float = 300.0
    DEFAULT_POLL_INTERVAL_SECONDS: float = 10.0
    DEFAULT_LEASE_FILE_PATH: Path = PROJECT_ROOT_DIR / "data" / "ollama_server_lease.json"

    def __init__(
        self,
        server_process_id: int,
        idle_seconds: float = DEFAULT_IDLE_SECONDS,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        lease_file_path: Path | None = None,
    ) -> None:
        self._server_process_id = server_process_id
        self._idle_seconds = idle_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._lease_file_path = (
            lease_file_path if lease_file_path is not None else self.DEFAULT_LEASE_FILE_PATH
        )

    def create_watcher(self) -> OllamaIdleShutdownWatcher:
        """Create and return a configured Ollama idle shutdown watcher instance."""
        return OllamaIdleShutdownWatcher(
            server_process_id=self._server_process_id,
            lease_store=self._lease_store(),
            process_inspector=self._process_inspector(),
            process_tree_terminator=self._process_tree_terminator(),
            idle_seconds=self._idle_seconds,
            poll_interval_seconds=self._poll_interval_seconds,
            sleep_function=sleep,
            wall_clock_function=time,
        )

    def _lease_store(self) -> OllamaServerLeaseStore:
        return OllamaServerLeaseStore(self._lease_file_path)

    def _process_inspector(self) -> ProcessInspector:
        return ProcessInspector()

    def _process_tree_terminator(self) -> ProcessTreeTerminator:
        return ProcessTreeTerminator()
