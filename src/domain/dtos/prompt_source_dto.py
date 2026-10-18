from dataclasses import dataclass
from typing import ClassVar

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class PromptSourceDTO(BaseDTO):
    """Describes the prompt set used by one analysis run and the prompts replaced on top of it."""

    DEFAULT_BASE_LABEL: ClassVar[str] = "default"

    base_label: str
    replaced_prompt_names: tuple[str, ...]

    def describe(self) -> str:
        """Return the base label, followed by the replaced prompt names when there are any."""
        if not self.replaced_prompt_names:
            return self.base_label
        return f"{self.base_label} + {', '.join(self.replaced_prompt_names)}"
