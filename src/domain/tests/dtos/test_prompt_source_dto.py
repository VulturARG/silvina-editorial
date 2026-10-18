from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.prompt_source_dto import PromptSourceDTO


class TestPromptSourceDTO(TestCase):
    def test_describe_returns_default_label_alone_without_replaced_prompts(self):
        prompt_source = PromptSourceDTO(base_label="default", replaced_prompt_names=())

        self.assertEqual(prompt_source.describe(), "default")

    def test_describe_returns_root_folder_name_alone_without_replaced_prompts(self):
        prompt_source = PromptSourceDTO(base_label="v2", replaced_prompt_names=())

        self.assertEqual(prompt_source.describe(), "v2")

    def test_describe_appends_replaced_prompt_names_separated_by_comma(self):
        prompt_source = PromptSourceDTO(
            base_label="default",
            replaced_prompt_names=("clarity_coherence_prompt", "research_lines"),
        )

        self.assertEqual(
            prompt_source.describe(),
            "default + clarity_coherence_prompt, research_lines",
        )

    def test_describe_keeps_replaced_prompt_names_in_given_order(self):
        prompt_source = PromptSourceDTO(
            base_label="v2",
            replaced_prompt_names=("alignment_prompt",),
        )

        self.assertEqual(prompt_source.describe(), "v2 + alignment_prompt")

    def test_default_base_label_constant_is_default(self):
        self.assertEqual(PromptSourceDTO.DEFAULT_BASE_LABEL, "default")

    def test_is_immutable(self):
        prompt_source = PromptSourceDTO(base_label="default", replaced_prompt_names=())

        with self.assertRaises(FrozenInstanceError):
            prompt_source.base_label = "v2"
