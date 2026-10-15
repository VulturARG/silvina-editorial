from argparse import ArgumentParser
from collections.abc import Sequence
from logging import NullHandler, getLogger
from pathlib import Path

from src.infrastructure.wirings.ollama_idle_shutdown_watcher_wiring import (
    OllamaIdleShutdownWatcherWiring,
)


def main(argument_list: Sequence[str] | None = None) -> None:
    """Run the detached Ollama idle shutdown watcher process."""
    getLogger().addHandler(NullHandler())
    parser = ArgumentParser(description="Ollama server idle shutdown watcher")
    parser.add_argument(
        "--server-process-id",
        type=int,
        required=True,
        help="Process identifier of the Ollama server to monitor",
    )
    parser.add_argument(
        "--idle-seconds",
        type=float,
        default=300.0,
        help="Inactivity duration before stopping the server",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=10.0,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--lease-file",
        type=Path,
        default=None,
        help="Path to the JSON lease metadata file",
    )
    parsed_arguments = parser.parse_args(argument_list)

    wiring = OllamaIdleShutdownWatcherWiring(
        server_process_id=parsed_arguments.server_process_id,
        idle_seconds=parsed_arguments.idle_seconds,
        poll_interval_seconds=parsed_arguments.poll_interval_seconds,
        lease_file_path=parsed_arguments.lease_file,
    )
    watcher = wiring.create_watcher()
    watcher.run()


if __name__ == "__main__":
    main()
