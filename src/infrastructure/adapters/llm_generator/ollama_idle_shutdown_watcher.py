from collections.abc import Callable
from time import sleep, time

from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)
from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.adapters.llm_generator.process_tree_terminator import (
    ProcessTreeTerminator,
)


class OllamaIdleShutdownWatcher:
    """Monitors the Ollama server lease and terminates the process tree after inactivity."""

    def __init__(
        self,
        server_process_id: int,
        lease_store: OllamaServerLeaseStore,
        process_inspector: ProcessInspector,
        process_tree_terminator: ProcessTreeTerminator,
        idle_seconds: float,
        poll_interval_seconds: float,
        sleep_function: Callable[[float], None] = sleep,
        wall_clock_function: Callable[[], float] = time,
    ) -> None:
        self._server_process_id = server_process_id
        self._lease_store = lease_store
        self._process_inspector = process_inspector
        self._process_tree_terminator = process_tree_terminator
        self._idle_seconds = idle_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep_function = sleep_function
        self._wall_clock_function = wall_clock_function

    def run(self) -> None:
        """Poll the server lease state and terminate the server when idle expiration is reached."""
        while True:
            self._sleep_function(self._poll_interval_seconds)
            lease = self._lease_store.read()
            if lease is None:
                return
            if lease.server_process_id != self._server_process_id:
                return
            if not self._process_inspector.is_alive(self._server_process_id):
                self._lease_store.clear()
                return
            if lease.active_process_id is not None and self._process_inspector.is_alive(
                lease.active_process_id
            ):
                continue
            now = self._wall_clock_function()
            if now - lease.last_use_epoch_seconds >= self._idle_seconds:
                image_name = self._process_inspector.image_name(self._server_process_id)
                if image_name is not None and image_name.lower().startswith("ollama"):
                    self._process_tree_terminator.terminate(self._server_process_id)
                self._lease_store.clear()
                return
