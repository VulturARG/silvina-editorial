from pathlib import Path
from unittest import TestCase

from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector
from src.infrastructure.cli.batch_file_reader import BatchFileReader
from src.infrastructure.resources.project import PROJECT_ROOT_DIR


class TestBatchSampleFiles(TestCase):
    PACK_DIRECTORY = PROJECT_ROOT_DIR / "sandbox" / "pack_2"
    TWO_DOCUMENTS_BATCH_FILE_PATH = PACK_DIRECTORY / "batch_two_documents.toml"
    ALL_DOCUMENTS_BATCH_FILE_PATH = PACK_DIRECTORY / "batch_all_documents.toml"
    INPUT_DIRECTORY = PACK_DIRECTORY / "inputs"
    OUTPUT_DIRECTORY = PACK_DIRECTORY / "outputs"

    def setUp(self):
        self.reader = BatchFileReader(BatchDocumentSelector())

    def _document_names_of(self, batch_file_path: Path) -> list[list[str]]:
        plan = self.reader.read(batch_file_path)
        return [
            [arguments.document_name for arguments in run.document_arguments] for run in plan.runs
        ]

    def test_two_documents_batch_runs_gemma_then_haiku(self):
        plan = self.reader.read(self.TWO_DOCUMENTS_BATCH_FILE_PATH)

        self.assertEqual([run.name for run in plan.runs], ["gemma", "haiku"])

    def test_two_documents_batch_processes_documents_01_and_02_in_every_run(self):
        expected_document_names = ["01_IMRyD_Cano_Martinez.docx", "02_IMRyD_Martinez_Garcia.docx"]

        self.assertEqual(
            self._document_names_of(self.TWO_DOCUMENTS_BATCH_FILE_PATH),
            [expected_document_names, expected_document_names],
        )

    def test_all_documents_batch_processes_every_input_document_in_every_run(self):
        expected_document_names = sorted(
            entry.name for entry in self.INPUT_DIRECTORY.iterdir() if entry.suffix == ".docx"
        )

        self.assertEqual(len(expected_document_names), 15)
        self.assertEqual(
            self._document_names_of(self.ALL_DOCUMENTS_BATCH_FILE_PATH),
            [expected_document_names, expected_document_names],
        )

    def test_sample_batches_resolve_inputs_and_outputs_inside_pack_2(self):
        for batch_file_path in (
            self.TWO_DOCUMENTS_BATCH_FILE_PATH,
            self.ALL_DOCUMENTS_BATCH_FILE_PATH,
        ):
            with self.subTest(batch_file=batch_file_path.name):
                plan = self.reader.read(batch_file_path)

                for run in plan.runs:
                    for arguments in run.document_arguments:
                        self.assertEqual(arguments.input_directory, self.INPUT_DIRECTORY)
                        self.assertEqual(arguments.output_directory, self.OUTPUT_DIRECTORY)
                self.assertTrue(self.INPUT_DIRECTORY.is_dir())
                self.assertTrue(self.OUTPUT_DIRECTORY.is_dir())

    def test_haiku_run_uses_external_llm_and_gemma_run_does_not(self):
        plan = self.reader.read(self.TWO_DOCUMENTS_BATCH_FILE_PATH)
        runs_by_name = {run.name: run for run in plan.runs}

        gemma_arguments = runs_by_name["gemma"].document_arguments[0]
        haiku_arguments = runs_by_name["haiku"].document_arguments[0]
        self.assertIs(gemma_arguments.use_external_llm, False)
        self.assertIs(haiku_arguments.use_external_llm, True)
