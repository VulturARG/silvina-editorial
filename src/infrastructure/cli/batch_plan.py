from dataclasses import dataclass

from src.infrastructure.cli.batch_run import BatchRun


@dataclass(frozen=True)
class BatchPlan:
    """The runs of a batch file, in the order they are executed."""

    runs: tuple[BatchRun, ...]
