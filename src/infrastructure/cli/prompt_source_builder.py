from collections.abc import Mapping
from pathlib import Path

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.cli.command_line_arguments import CommandLineArguments


class PromptSourceBuilder:
    """Build the prompt source description of one command line analysis run."""

    def build(
        self,
        prompts_root: Path | None,
        prompt_file_overrides: Mapping[str, Path | None] | None,
    ) -> PromptSourceDTO:
        """Return the base label and the replaced prompt names in the fixed prompt order."""
        return PromptSourceDTO(
            base_label=self._base_label(prompts_root),
            replaced_prompt_names=self._replaced_prompt_names(prompt_file_overrides),
            uses_custom_prompts_root=prompts_root is not None,
        )

    def _base_label(self, prompts_root: Path | None) -> str:
        if prompts_root is None:
            return PromptSourceDTO.DEFAULT_BASE_LABEL
        return prompts_root.resolve().name

    def _replaced_prompt_names(
        self, prompt_file_overrides: Mapping[str, Path | None] | None
    ) -> tuple[str, ...]:
        if prompt_file_overrides is None:
            return ()
        return tuple(
            prompt_name
            for prompt_name in CommandLineArguments.PROMPT_NAMES
            if prompt_file_overrides.get(prompt_name) is not None
        )
