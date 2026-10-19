from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import TestCase

from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector
from src.infrastructure.cli.batch_file_reader import BatchFileReader


class TestBatchFileReader(TestCase):
    def setUp(self):
        self.reader = BatchFileReader(BatchDocumentSelector())
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.batch_directory = Path(temporary_directory.name)
        self.input_directory = self.batch_directory / "inputs"
        self.input_directory.mkdir()

    def _create_documents(self, *document_names: str) -> None:
        for document_name in document_names:
            (self.input_directory / document_name).write_bytes(b"")

    def _read(self, content: str):
        batch_file_path = self.batch_directory / "batch.toml"
        batch_file_path.write_text(dedent(content), encoding="utf-8")
        return self.reader.read(batch_file_path)

    def test_runs_keep_the_order_of_the_file(self):
        self._create_documents("01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "gemma"

            [[run]]
            name = "qwen"
            """
        )

        self.assertEqual([run.name for run in plan.runs], ["gemma", "qwen"])

    def test_omitted_documents_select_every_document_of_the_input_directory(self):
        self._create_documents("02_y.docx", "01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "gemma"
            """
        )

        self.assertEqual(
            [argument.document_name for argument in plan.runs[0].document_arguments],
            ["01_x.docx", "02_y.docx"],
        )

    def test_batch_documents_apply_to_every_run(self):
        self._create_documents("01_x.docx", "02_y.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"
            documents = ["02_y.docx"]

            [[run]]
            name = "gemma"

            [[run]]
            name = "qwen"
            """
        )

        for run in plan.runs:
            self.assertEqual(
                [argument.document_name for argument in run.document_arguments],
                ["02_y.docx"],
            )

    def test_run_documents_override_batch_documents(self):
        self._create_documents("01_x.docx", "02_y.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"
            documents = ["02_y.docx"]

            [[run]]
            name = "gemma"
            documents = ["01_x.docx"]

            [[run]]
            name = "qwen"
            """
        )

        self.assertEqual(
            [argument.document_name for argument in plan.runs[0].document_arguments],
            ["01_x.docx"],
        )
        self.assertEqual(
            [argument.document_name for argument in plan.runs[1].document_arguments],
            ["02_y.docx"],
        )

    def test_every_document_argument_carries_the_run_fields(self):
        self._create_documents("01_x.docx", "02_y.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "gemma"
            ollama_model_name = "gemma4-26b-adapted"
            """
        )

        self.assertEqual(
            [argument.ollama_model_name for argument in plan.runs[0].document_arguments],
            ["gemma4-26b-adapted", "gemma4-26b-adapted"],
        )

    def test_relative_paths_resolve_against_the_batch_file_directory(self):
        self._create_documents("01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"
            output_directory = "outputs"
            prompts_directory = "prompts"

            [[run]]
            name = "gemma"
            alignment_prompt = "custom/alignment"
            """
        )

        argument = plan.runs[0].document_arguments[0]
        self.assertEqual(argument.input_directory, self.input_directory)
        self.assertEqual(argument.output_directory, self.batch_directory / "outputs")
        self.assertEqual(argument.prompts_directory, self.batch_directory / "prompts")
        self.assertEqual(argument.alignment_prompt, self.batch_directory / "custom" / "alignment")

    def test_absolute_paths_stay_as_they_are(self):
        self._create_documents("01_x.docx")
        absolute_output_directory = self.batch_directory / "elsewhere"

        plan = self._read(
            f"""
            [batch]
            input_directory = "{self.input_directory.as_posix()}"
            output_directory = "{absolute_output_directory.as_posix()}"

            [[run]]
            name = "gemma"
            """
        )

        argument = plan.runs[0].document_arguments[0]
        self.assertEqual(argument.input_directory, self.input_directory)
        self.assertEqual(argument.output_directory, absolute_output_directory)

    def test_use_external_llm_defaults_to_false(self):
        self._create_documents("01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "gemma"
            """
        )

        self.assertIs(plan.runs[0].document_arguments[0].use_external_llm, False)

    def test_run_can_enable_external_llm_in_debug_app_mode(self):
        self._create_documents("01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "claude"
            use_external_llm = true
            app_mode = "DEBUG"
            """
        )

        self.assertIs(plan.runs[0].document_arguments[0].use_external_llm, True)

    def test_external_llm_accepts_lowercase_debug_app_mode(self):
        self._create_documents("01_x.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"

            [[run]]
            name = "claude"
            use_external_llm = true
            app_mode = "debug"
            """
        )

        self.assertIs(plan.runs[0].document_arguments[0].use_external_llm, True)

    def test_external_llm_with_non_debug_app_mode_raises_naming_the_run(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError) as context:
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "claude"
                use_external_llm = true
                app_mode = "PROD"
                """
            )

        self.assertIn("claude", str(context.exception))
        self.assertIn("DEBUG", str(context.exception))

    def test_external_llm_without_app_mode_raises(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError):
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "claude"
                use_external_llm = true
                """
            )

    def test_run_without_name_raises_naming_its_index(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError) as context:
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "gemma"

                [[run]]
                ollama_model_name = "qwen"
                """
            )

        self.assertIn("2", str(context.exception))

    def test_file_without_runs_raises(self):
        with self.assertRaises(ValueError):
            self._read(
                """
                [batch]
                input_directory = "inputs"
                """
            )

    def test_run_without_input_directory_raises(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError) as context:
            self._read(
                """
                [[run]]
                name = "gemma"
                """
            )

        self.assertIn("gemma", str(context.exception))

    def test_run_with_no_document_in_input_directory_raises(self):
        with self.assertRaises(ValueError):
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "gemma"
                """
            )

    def test_unknown_run_key_raises_type_error(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(TypeError):
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "gemma"
                unknown_setting = 1
                """
            )

    def test_document_name_in_run_raises(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError):
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "gemma"
                document_name = "01_x.docx"
                """
            )

    def test_document_name_in_batch_raises(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError):
            self._read(
                """
                [batch]
                input_directory = "inputs"
                document_name = "01_x.docx"

                [[run]]
                name = "gemma"
                """
            )
