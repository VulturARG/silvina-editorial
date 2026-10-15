from collections.abc import Callable
from csv import reader
from io import StringIO
from os import name
from subprocess import run
from typing import Any

from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NO_WINDOW,
)


class ProcessInspector:
    """Inspects operating system processes for liveness and image names."""

    def __init__(self, command_runner: Callable[..., Any] = run) -> None:
        self._command_runner = command_runner

    def is_alive(self, process_id: int) -> bool:
        """Return True when the process with the given identifier is running."""
        return self.image_name(process_id) is not None

    def image_name(self, process_id: int) -> str | None:
        """Return the executable image name of the process or None when not running."""
        try:
            if name == "nt":
                return self._inspect_windows(process_id)
            return self._inspect_posix(process_id)
        except (OSError, ValueError):
            return None

    def _inspect_windows(self, process_id: int) -> str | None:
        command = ["tasklist", "/FI", f"PID eq {process_id}", "/FO", "CSV", "/NH"]
        result = self._command_runner(
            command,
            capture_output=True,
            text=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            return None
        csv_reader = reader(StringIO(result.stdout))
        for row in csv_reader:
            if len(row) >= 2 and row[1].strip() == str(process_id):
                detected_name = row[0].strip()
                if detected_name and not detected_name.upper().startswith(("INFO", "INFORMACI")):
                    return detected_name
        return None

    def _inspect_posix(self, process_id: int) -> str | None:
        command = ["ps", "-p", str(process_id), "-o", "comm="]
        result = self._command_runner(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        return output if output else None
