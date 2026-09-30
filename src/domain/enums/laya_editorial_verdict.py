from enum import Enum


class LayaEditorialVerdict(Enum):
    """Choice labels Laya returns for the contribution verdict question."""

    SUSTAINED = "SUSTENTADA"
    PARTIAL = "PARCIAL"
    NOT_SUSTAINED = "NO SUSTENTADA"
