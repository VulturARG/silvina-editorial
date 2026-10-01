from enum import Enum


class ExecutionStatus(Enum):
    """Lifecycle status of an analysis or of an external AI interaction."""

    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
