from unittest import TestCase

from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector
from src.infrastructure.cli.batch_file_reader import BatchFileReader
from src.infrastructure.resources.project import PROJECT_ROOT_DIR


class TestBatchSampleFiles(TestCase):
    PACK_DIRECTORY = PROJECT_ROOT_DIR / "sandbox" / "pack_2"
    TWO_DOCUMENTS_BATCH_FILE_PATH = PACK_DIRECTORY / "batch_two_documents.toml"
    ALL_DOCUMENTS_BATCH_FILE_PATH = PACK_DIRECTORY / "batch_all_documents.toml"

    def setUp(self):
        self.reader = BatchFileReader(BatchDocumentSelector(), PROJECT_ROOT_DIR)

    def test_two_documents_batch_plans_gemma_then_haiku_with_two_documents_each(self):
        plan = self.reader.read(self.TWO_DOCUMENTS_BATCH_FILE_PATH)

        self.assertEqual([run.name for run in plan.runs], ["gemma", "haiku"])
        self.assertEqual([len(run.document_arguments) for run in plan.runs], [2, 2])

    def test_all_documents_batch_plans_every_input_document_in_each_run(self):
        plan = self.reader.read(self.ALL_DOCUMENTS_BATCH_FILE_PATH)
        expected_document_names = sorted(
            entry.name
            for entry in (self.PACK_DIRECTORY / "inputs").iterdir()
            if entry.suffix.lower() == ".docx" and not entry.name.startswith("~$")
        )

        self.assertEqual([run.name for run in plan.runs], ["gemma", "haiku"])
        for run in plan.runs:
            self.assertEqual(
                [argument.document_name for argument in run.document_arguments],
                expected_document_names,
            )
