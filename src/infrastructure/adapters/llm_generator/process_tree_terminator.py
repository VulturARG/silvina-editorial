from collections.abc import Callable
from logging import getLogger
from os import name
from signal import SIGTERM
from subprocess import SubprocessError, run
from sys import modules
from typing import Any

from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NO_WINDOW,
)

os_module = modules.get("os")
default_get_process_group_id = getattr(os_module, "getpgid", None)
default_kill_process_group = getattr(os_module, "killpg", None)

logger = getLogger(__name__)


class ProcessTreeTerminator:
    """Terminates process trees across platforms."""

    def __init__(
        self,
        command_runner: Callable[..., Any] = run,
        get_process_group_id_function: Callable[[int], int] | None = None,
        kill_process_group_function: Callable[[int, int], None] | None = None,
    ) -> None:
        self._command_runner = command_runner
        self._get_process_group_id_function = (
            get_process_group_id_function
            if get_process_group_id_function is not None
            else default_get_process_group_id
        )
        self._kill_process_group_function = (
            kill_process_group_function
            if kill_process_group_function is not None
            else default_kill_process_group
        )

    def terminate(self, process_id: int) -> None:
        """Terminate the process and any descendant processes."""
        try:
            if name == "nt":
                self._terminate_windows(process_id)
            else:
                self._terminate_posix(process_id)
        except (OSError, SubprocessError) as error:
            logger.warning("Failed to terminate process %d: %s", process_id, error)

    def _terminate_windows(self, process_id: int) -> None:
        command = ["taskkill", "/PID", str(process_id), "/T", "/F"]
        self._command_runner(
            command,
            capture_output=True,
            text=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )

    def _terminate_posix(self, process_id: int) -> None:
        if self._get_process_group_id_function is None or self._kill_process_group_function is None:
            raise OSError("POSIX process group termination is not supported on this platform")
        process_group_id = self._get_process_group_id_function(process_id)
        self._kill_process_group_function(process_group_id, SIGTERM)
