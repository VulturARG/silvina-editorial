from pathlib import Path
from unittest import TestCase

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.prompt_source_builder import PromptSourceBuilder


class TestPromptSourceBuilder(TestCase):
    ROOT_PATH = Path("resources") / "v2"

    def setUp(self):
        self.builder = PromptSourceBuilder()

    def test_default_without_root_and_without_overrides(self):
        prompt_source = self.builder.build(None, None)

        self.assertEqual(
            prompt_source, PromptSourceDTO(base_label="default", replaced_prompt_names=())
        )
        self.assertEqual(prompt_source.describe(), "default")

    def test_root_folder_name_without_overrides(self):
        prompt_source = self.builder.build(self.ROOT_PATH, None)

        self.assertEqual(prompt_source.describe(), "v2")

    def test_root_folder_name_with_one_replaced_prompt(self):
        prompt_source = self.builder.build(
            self.ROOT_PATH, {"alignment_prompt": Path("a") / "alignment_prompt.txt"}
        )

        self.assertEqual(prompt_source.describe(), "v2 + alignment_prompt")

    def test_default_with_replaced_prompts_in_fixed_prompt_order(self):
        prompt_source = self.builder.build(
            None,
            {
                "research_lines": Path("r") / "research_lines.txt",
                "clarity_coherence_prompt": Path("c") / "clarity_coherence_prompt.txt",
            },
        )

        self.assertEqual(
            prompt_source.describe(),
            "default + clarity_coherence_prompt, research_lines",
        )

    def test_replaced_names_ignore_mapping_iteration_order(self):
        overrides = {
            "research_lines": Path("r") / "research_lines.txt",
            "alignment_prompt": Path("a") / "alignment_prompt.txt",
        }

        prompt_source = self.builder.build(self.ROOT_PATH, overrides)

        self.assertEqual(
            prompt_source.replaced_prompt_names,
            ("alignment_prompt", "research_lines"),
        )

    def test_none_overrides_are_not_reported_as_replaced(self):
        prompt_source = self.builder.build(
            self.ROOT_PATH,
            {
                "alignment_prompt": None,
                "contribution_prompt": Path("c") / "contribution_prompt.txt",
            },
        )

        self.assertEqual(prompt_source.replaced_prompt_names, ("contribution_prompt",))

    def test_empty_overrides_mean_no_replaced_prompts(self):
        prompt_source = self.builder.build(None, {})

        self.assertEqual(prompt_source.replaced_prompt_names, ())

    def test_unknown_override_keys_are_ignored(self):
        prompt_source = self.builder.build(
            None, {"unknown_prompt": Path("u") / "unknown_prompt.txt"}
        )

        self.assertEqual(prompt_source.describe(), "default")

    def test_every_prompt_name_is_reported_when_all_are_replaced(self):
        overrides = {
            prompt_name: Path("custom") / f"{prompt_name}.txt"
            for prompt_name in CommandLineArguments.PROMPT_NAMES
        }

        prompt_source = self.builder.build(None, overrides)

        self.assertEqual(prompt_source.replaced_prompt_names, CommandLineArguments.PROMPT_NAMES)

    def test_relative_root_dot_uses_current_folder_name(self):
        prompt_source = self.builder.build(Path("."), None)

        self.assertEqual(prompt_source.base_label, Path.cwd().name)

    def test_relative_root_with_trailing_separator_uses_folder_name(self):
        prompt_source = self.builder.build(Path("resources") / "v2" / "", None)

        self.assertEqual(prompt_source.base_label, "v2")

    def test_root_sets_uses_custom_prompts_root(self):
        prompt_source = self.builder.build(self.ROOT_PATH, None)

        self.assertTrue(prompt_source.uses_custom_prompts_root)

    def test_root_folder_named_default_sets_uses_custom_prompts_root(self):
        prompt_source = self.builder.build(Path("resources") / "default", None)

        self.assertEqual(prompt_source.base_label, "default")
        self.assertTrue(prompt_source.uses_custom_prompts_root)

    def test_without_root_does_not_set_uses_custom_prompts_root(self):
        prompt_source = self.builder.build(
            None, {"research_lines": Path("r") / "research_lines.txt"}
        )

        self.assertFalse(prompt_source.uses_custom_prompts_root)
