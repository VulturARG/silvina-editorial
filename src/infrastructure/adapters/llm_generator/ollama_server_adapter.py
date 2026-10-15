from collections.abc import Callable, Sequence
from logging import getLogger
from os import getpid, name
from pathlib import Path
from subprocess import DEVNULL, Popen
from time import monotonic, sleep, time
from typing import Any
from urllib.parse import urlparse

from httpx import HTTPError
from ollama import Client, RequestError, ResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelServerExecutableNotFound,
    LanguageModelServerStartFailed,
)
from src.domain.language_model.language_model_server_port import (
    LanguageModelServerPort,
)
from src.infrastructure.adapters.llm_generator.ollama_executable_locator import (
    OllamaExecutableLocator,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease import (
    OllamaServerLease,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)
from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NEW_PROCESS_GROUP,
    CREATE_NO_WINDOW,
)

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})

logger = getLogger(__name__)


class OllamaServerAdapter(LanguageModelServerPort):
    """Adapter for verifying and launching the local system Ollama server."""

    def __init__(
        self,
        base_url: str,
        startup_timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 0.5,
        probe_timeout_seconds: float = 2.0,
        executable_locator: Callable[..., str | None] | None = None,
        process_launcher: Callable[..., Any] = Popen,
        sleep_function: Callable[[float], None] = sleep,
        clock_function: Callable[[], float] = monotonic,
        client_factory: Callable[..., Any] | None = None,
        lease_store: OllamaServerLeaseStore | None = None,
        process_inspector: ProcessInspector | None = None,
        current_process_id_provider: Callable[[], int] = getpid,
        wall_clock_function: Callable[[], float] = time,
        watcher_launch_command: Sequence[str] | None = None,
        watcher_working_directory: Path | str | None = None,
        idle_seconds: float = 300.0,
    ) -> None:
        self._base_url = base_url
        self._startup_timeout_seconds = startup_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._probe_timeout_seconds = probe_timeout_seconds
        self._executable_locator = (
            executable_locator
            if executable_locator is not None
            else OllamaExecutableLocator().locate
        )
        self._process_launcher = process_launcher
        self._sleep_function = sleep_function
        self._clock_function = clock_function
        self._client_factory = client_factory
        self._lease_store = lease_store
        self._process_inspector = process_inspector
        self._current_process_id_provider = current_process_id_provider
        self._wall_clock_function = wall_clock_function
        self._watcher_launch_command = watcher_launch_command
        self._watcher_working_directory = watcher_working_directory
        self._idle_seconds = idle_seconds

    def is_running(self) -> bool:
        """Return True when the Ollama server responds to a list request."""
        try:
            effective_client_factory = self._client_factory or Client
            client = effective_client_factory(
                host=self._base_url, timeout=self._probe_timeout_seconds
            )
            client.list()
            return True
        except (ConnectionError, HTTPError, RequestError, ResponseError):
            return False

    def start(self) -> None:
        """Start the local Ollama server process and wait until it responds."""
        self._validate_local_host()
        executable_path = self._locate_executable()
        server_process = self._launch_process(executable_path)
        server_process_id = getattr(server_process, "pid", None)
        if server_process_id is not None:
            self._record_started_server_lease(server_process_id)
            self._spawn_idle_shutdown_watcher(server_process_id)
        self._wait_until_running()

    def mark_in_use(self) -> None:
        """Mark the active lease as currently in use by the calling process."""
        if self._lease_store is None:
            return
        try:
            lease = self._lease_store.read()
            if lease is None:
                return
            if self._process_inspector is not None:
                image_name = self._process_inspector.image_name(lease.server_process_id)
                if image_name is None or not image_name.lower().startswith("ollama"):
                    self._lease_store.clear()
                    return
            updated_lease = OllamaServerLease(
                server_process_id=lease.server_process_id,
                active_process_id=self._current_process_id_provider(),
                last_use_epoch_seconds=self._wall_clock_function(),
            )
            self._lease_store.write(updated_lease)
        except OSError as error:
            logger.warning("Failed to mark Ollama server in use: %s", error)

    def mark_idle(self) -> None:
        """Mark the active lease as no longer held by any running process."""
        if self._lease_store is None:
            return
        try:
            lease = self._lease_store.read()
            if lease is None:
                return
            updated_lease = OllamaServerLease(
                server_process_id=lease.server_process_id,
                active_process_id=None,
                last_use_epoch_seconds=self._wall_clock_function(),
            )
            self._lease_store.write(updated_lease)
        except OSError as error:
            logger.warning("Failed to mark Ollama server idle: %s", error)

    def _validate_local_host(self) -> None:
        normalized_url = self._base_url if "://" in self._base_url else f"http://{self._base_url}"
        hostname = urlparse(normalized_url).hostname
        if hostname not in _LOCAL_HOSTS:
            raise LanguageModelServerStartFailed()

    def _locate_executable(self) -> str:
        try:
            executable_path = self._executable_locator()
        except TypeError:
            executable_path = self._executable_locator("ollama")
        if executable_path is None:
            raise LanguageModelServerExecutableNotFound()
        return executable_path

    def _launch_process(self, executable_path: str) -> Any:
        command = [executable_path, "serve"]
        try:
            if name == "nt":
                creation_flags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
                return self._process_launcher(
                    command,
                    stdin=DEVNULL,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    creationflags=creation_flags,
                )
            return self._process_launcher(
                command,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
                start_new_session=True,
            )
        except OSError as error:
            raise LanguageModelServerStartFailed() from error

    def _record_started_server_lease(self, server_process_id: int) -> None:
        if self._lease_store is None:
            return
        lease = OllamaServerLease(
            server_process_id=server_process_id,
            active_process_id=self._current_process_id_provider(),
            last_use_epoch_seconds=self._wall_clock_function(),
        )
        try:
            self._lease_store.write(lease)
        except OSError as error:
            logger.warning("Failed to record Ollama server lease: %s", error)

    def _spawn_idle_shutdown_watcher(self, server_process_id: int) -> None:
        if self._watcher_launch_command is None:
            return
        command = list(self._watcher_launch_command) + [
            "--server-process-id",
            str(server_process_id),
        ]
        try:
            if name == "nt":
                creation_flags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
                self._process_launcher(
                    command,
                    stdin=DEVNULL,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    creationflags=creation_flags,
                    cwd=self._watcher_working_directory,
                )
            else:
                self._process_launcher(
                    command,
                    stdin=DEVNULL,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    start_new_session=True,
                    cwd=self._watcher_working_directory,
                )
        except OSError as error:
            logger.warning("Failed to launch Ollama idle shutdown watcher: %s", error)

    def _wait_until_running(self) -> None:
        deadline = self._clock_function() + self._startup_timeout_seconds
        while self._clock_function() < deadline:
            self._sleep_function(self._poll_interval_seconds)
            if self.is_running():
                return
        if self.is_running():
            return
        raise LanguageModelServerStartFailed()
