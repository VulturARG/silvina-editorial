from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.infrastructure.cli.report_file_paths_builder import ReportFilePathsBuilder
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class TestReportFilePathsBuilder(TestCase):
    DOCUMENT_PATH = Path("C:/docs/tesis.docx")

    def setUp(self):
        self.builder = ReportFilePathsBuilder(file_name_sanitizer=WindowsFileNameSanitizer())
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.temporary_directory = Path(temporary_directory.name)

    def test_default_directory_is_analisis_folder_next_to_document(self):
        paths = self.builder.build(self.DOCUMENT_PATH, None, "gemma")

        self.assertEqual(paths.word_path.parent, Path("C:/docs") / "análisis")

    def test_explicit_output_directory_is_used_as_given(self):
        output_directory = Path("D:/salida/informes")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma")

        self.assertEqual(paths.word_path.parent, output_directory)
        self.assertEqual(paths.json_path.parent, output_directory)
        self.assertEqual(paths.html_path.parent, output_directory)

    def test_three_paths_share_base_name_and_use_their_extensions(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma")

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")
        self.assertEqual(paths.json_path, output_directory / "tesis_analisis_gemma.json")
        self.assertEqual(paths.html_path, output_directory / "tesis_analisis_gemma.html")

    def test_model_name_slashes_and_colons_are_sanitized(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(
            self.DOCUMENT_PATH, output_directory, "hf.co/unsloth/gemma:UD-IQ4"
        )

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_hf.co_unsloth_gemma_UD-IQ4.docx",
        )

    def test_empty_model_name_omits_model_suffix(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "")

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis.docx")
        self.assertEqual(paths.json_path, output_directory / "tesis_analisis.json")
        self.assertEqual(paths.html_path, output_directory / "tesis_analisis.html")

    def test_document_stem_with_invalid_characters_is_sanitized(self):
        output_directory = Path("D:/salida")
        document_path = Path("C:/docs/tesis|v2.docx")

        paths = self.builder.build(document_path, output_directory, "gemma")

        self.assertEqual(paths.word_path, output_directory / "tesis_v2_analisis_gemma.docx")

    def test_building_paths_creates_no_default_output_directory(self):
        document_path = self.temporary_directory / "tesis.docx"

        self.builder.build(document_path, None, "gemma")

        self.assertFalse((self.temporary_directory / "análisis").exists())

    def test_building_paths_creates_no_explicit_output_directory(self):
        output_directory = self.temporary_directory / "salida"
        document_path = self.temporary_directory / "tesis.docx"

        self.builder.build(document_path, output_directory, "gemma")

        self.assertFalse(output_directory.exists())

    def test_missing_prompt_source_keeps_base_name(self):
        output_directory = Path("D:/salida")

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", None)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")

    def test_default_root_without_replaced_prompts_keeps_base_name(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL, replaced_prompt_names=()
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")

    def test_custom_root_name_is_appended_after_model_name(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="v2", replaced_prompt_names=(), uses_custom_prompts_root=True
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma_v2.docx")

    def test_custom_root_name_and_replaced_prompt_are_joined_with_plus(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="v2",
            replaced_prompt_names=("alignment_prompt",),
            uses_custom_prompts_root=True,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_gemma_v2+alignment_prompt.docx",
        )

    def test_replaced_prompts_follow_model_name_when_root_is_default(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL,
            replaced_prompt_names=("clarity_coherence_prompt", "research_lines"),
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_gemma_clarity_coherence_prompt+research_lines.docx",
        )

    def test_word_default_never_appears_in_file_name(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL,
            replaced_prompt_names=("research_lines",),
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertNotIn(PromptSourceDTO.DEFAULT_BASE_LABEL, paths.word_path.name)

    def test_root_name_with_forbidden_character_is_sanitized(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="v:2", replaced_prompt_names=(), uses_custom_prompts_root=True
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma_v_2.docx")

    def test_prompt_source_suffix_applies_to_json_and_html_paths(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="v2",
            replaced_prompt_names=("alignment_prompt",),
            uses_custom_prompts_root=True,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(
            paths.json_path, output_directory / "tesis_analisis_gemma_v2+alignment_prompt.json"
        )
        self.assertEqual(
            paths.html_path, output_directory / "tesis_analisis_gemma_v2+alignment_prompt.html"
        )

    def test_empty_model_name_places_prompt_source_suffix_after_base_name(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="v2", replaced_prompt_names=(), uses_custom_prompts_root=True
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_v2.docx")

    def test_empty_root_name_is_skipped_and_replaced_prompts_remain(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="",
            replaced_prompt_names=("research_lines",),
            uses_custom_prompts_root=True,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_gemma_research_lines.docx",
        )

    def test_empty_root_name_without_replaced_prompts_adds_no_suffix(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label="", replaced_prompt_names=(), uses_custom_prompts_root=True
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")

    def test_custom_root_named_default_is_appended_as_suffix(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL,
            replaced_prompt_names=(),
            uses_custom_prompts_root=True,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma_default.docx")

    def test_custom_root_named_default_is_joined_with_replaced_prompt_by_plus(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL,
            replaced_prompt_names=("research_lines",),
            uses_custom_prompts_root=True,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(
            paths.word_path,
            output_directory / "tesis_analisis_gemma_default+research_lines.docx",
        )

    def test_default_source_without_custom_root_flag_adds_no_suffix(self):
        output_directory = Path("D:/salida")
        prompt_source = PromptSourceDTO(
            base_label=PromptSourceDTO.DEFAULT_BASE_LABEL,
            replaced_prompt_names=(),
            uses_custom_prompts_root=False,
        )

        paths = self.builder.build(self.DOCUMENT_PATH, output_directory, "gemma", prompt_source)

        self.assertEqual(paths.word_path, output_directory / "tesis_analisis_gemma.docx")
