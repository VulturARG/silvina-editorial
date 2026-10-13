from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path


class ConsoleStepAnnouncer:
    """Announce the steps of the CLI run on the console, one line per message."""

    def __init__(self, write_function: Callable[[str], None] = print) -> None:
        """Keep the function used to write each line, so tests can capture them."""
        self._write_function = write_function

    def announce_start(self, step_description: str) -> None:
        """Announce that a step has started."""
        self._write_function(f"⏳ {step_description}...")

    def announce_finish(self, step_description: str) -> None:
        """Announce that a step has finished successfully."""
        self._write_function(f"✅ {step_description}: terminado")

    @contextmanager
    def step(self, step_description: str) -> Iterator[None]:
        """Announce the start of a step and its finish, only when the body completes."""
        self.announce_start(step_description)
        yield
        self.announce_finish(step_description)

    def announce_error(self, message: str) -> None:
        """Announce an error that stops the run."""
        self._write_function(f"❌ {message}")

    def announce_completion(self, generated_paths: Sequence[Path]) -> None:
        """Announce the end of the run followed by the path of every generated file."""
        self._write_function("🎉 Ejecución terminada")
        for generated_path in generated_paths:
            self._write_function(f"   📄 {generated_path}")
