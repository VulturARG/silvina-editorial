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

    def test_runs_keep_the_file_order_and_omitted_documents_select_every_document(self):
        self._create_documents("02_y.docx", "01_x.docx")

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
        for run in plan.runs:
            self.assertEqual(
                [argument.document_name for argument in run.document_arguments],
                ["01_x.docx", "02_y.docx"],
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

    def test_run_fields_override_batch_defaults_for_every_document_argument(self):
        self._create_documents("01_x.docx", "02_y.docx")

        plan = self._read(
            """
            [batch]
            input_directory = "inputs"
            ollama_model_name = "batch-model"

            [[run]]
            name = "gemma"
            ollama_model_name = "gemma4-26b-adapted"

            [[run]]
            name = "qwen"
            """
        )

        self.assertEqual(
            [argument.ollama_model_name for argument in plan.runs[0].document_arguments],
            ["gemma4-26b-adapted", "gemma4-26b-adapted"],
        )
        self.assertEqual(
            [argument.ollama_model_name for argument in plan.runs[1].document_arguments],
            ["batch-model", "batch-model"],
        )

    def test_relative_paths_resolve_against_batch_directory_and_absolute_paths_stay(self):
        self._create_documents("01_x.docx")
        absolute_output_directory = self.batch_directory / "elsewhere"

        plan = self._read(
            f"""
            [batch]
            input_directory = "inputs"
            output_directory = "{absolute_output_directory.as_posix()}"
            prompts_directory = "prompts"

            [[run]]
            name = "gemma"
            alignment_prompt = "custom/alignment"
            """
        )

        argument = plan.runs[0].document_arguments[0]
        self.assertEqual(argument.input_directory, self.input_directory)
        self.assertEqual(argument.output_directory, absolute_output_directory)
        self.assertEqual(argument.prompts_directory, self.batch_directory / "prompts")
        self.assertEqual(argument.alignment_prompt, self.batch_directory / "custom" / "alignment")

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

        for app_mode_line, expected_app_mode in (("", "DEBUG"), ('app_mode = "PROD"', "PROD")):
            with self.subTest(app_mode_line=app_mode_line):
                plan = self._read(
                    f"""
                    [batch]
                    input_directory = "inputs"

                    [[run]]
                    name = "gemma"
                    {app_mode_line}
                    """
                )

                self.assertEqual(plan.runs[0].document_arguments[0].app_mode, expected_app_mode)

    def test_external_llm_is_accepted_in_debug_app_mode_ignoring_case_and_surrounding_spaces(self):
        self._create_documents("01_x.docx")

        for app_mode_line, expected_app_mode in (
            ("", "DEBUG"),
            ('app_mode = "DEBUG"', "DEBUG"),
            ('app_mode = "debug"', "debug"),
            ('app_mode = " debug "', " debug "),
        ):
            with self.subTest(app_mode_line=app_mode_line):
                plan = self._read(
                    f"""
                    [batch]
                    input_directory = "inputs"

                    [[run]]
                    name = "claude"
                    use_external_llm = true
                    {app_mode_line}
                    """
                )

                argument = plan.runs[0].document_arguments[0]
                self.assertIs(argument.use_external_llm, True)
                self.assertEqual(argument.app_mode, expected_app_mode)

    def test_external_llm_outside_debug_app_mode_raises_naming_the_run(self):
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

    def test_external_llm_that_is_not_a_boolean_raises_naming_the_run_and_value(self):
        self._create_documents("01_x.docx")

        for external_llm_literal, external_llm_value in (('"false"', "false"), ("1", 1)):
            with self.subTest(external_llm_literal=external_llm_literal):
                with self.assertRaises(ValueError) as context:
                    self._read(
                        f"""
                        [batch]
                        input_directory = "inputs"

                        [[run]]
                        name = "claude"
                        use_external_llm = {external_llm_literal}
                        app_mode = "DEBUG"
                        """
                    )

                self.assertIn("claude", str(context.exception))
                self.assertIn(repr(external_llm_value), str(context.exception))

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

    def test_name_in_batch_table_raises_pointing_to_the_run_tables(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError) as context:
            self._read(
                """
                [batch]
                input_directory = "inputs"
                name = "gemma"

                [[run]]
                name = "qwen"
                """
            )

        self.assertIn("[[run]]", str(context.exception))

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

    def test_unknown_run_key_raises_value_error_naming_the_run(self):
        self._create_documents("01_x.docx")

        with self.assertRaises(ValueError) as context:
            self._read(
                """
                [batch]
                input_directory = "inputs"

                [[run]]
                name = "gemma"
                unknown_setting = 1
                """
            )

        self.assertIn("gemma", str(context.exception))

    def test_document_name_is_rejected_in_batch_or_run(self):
        self._create_documents("01_x.docx")

        for batch_line, run_line in (
            ('document_name = "01_x.docx"', ""),
            ("", 'document_name = "01_x.docx"'),
        ):
            with self.subTest(batch_line=batch_line, run_line=run_line):
                with self.assertRaises(ValueError):
                    self._read(
                        f"""
                        [batch]
                        input_directory = "inputs"
                        {batch_line}

                        [[run]]
                        name = "gemma"
                        {run_line}
                        """
                    )
