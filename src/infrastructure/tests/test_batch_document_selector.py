from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector


class TestBatchDocumentSelector(TestCase):
    def setUp(self):
        self.selector = BatchDocumentSelector()
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.input_directory = Path(temporary_directory.name)

    @staticmethod
    def _create_file(file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"")

    def _create_files(self, *relative_paths: str) -> None:
        for relative_path in relative_paths:
            self._create_file(self.input_directory / relative_path)

    def test_none_selects_every_docx_sorted_by_name(self):
        self._create_files("02_b.docx", "01_a.docx", "10_c.docx")

        self.assertEqual(
            self.selector.select(self.input_directory, None),
            ("01_a.docx", "02_b.docx", "10_c.docx"),
        )

    def test_text_all_selects_every_docx_sorted_by_name(self):
        self._create_files("02_b.docx", "01_a.docx")

        self.assertEqual(
            self.selector.select(self.input_directory, "all"),
            ("01_a.docx", "02_b.docx"),
        )

    def test_all_skips_word_lock_files(self):
        self._create_files("~$01_a.docx", "01_a.docx")

        self.assertEqual(self.selector.select(self.input_directory, None), ("01_a.docx",))

    def test_all_skips_files_with_other_extensions(self):
        self._create_files("notes.txt", "old.doc", "report.docx")

        self.assertEqual(self.selector.select(self.input_directory, None), ("report.docx",))

    def test_all_matches_docx_suffix_case_insensitively(self):
        self._create_files("A.DOCX", "b.Docx")

        self.assertEqual(self.selector.select(self.input_directory, None), ("A.DOCX", "b.Docx"))

    def test_all_does_not_look_into_subdirectories(self):
        self._create_files("top.docx", "sub/nested.docx")

        self.assertEqual(self.selector.select(self.input_directory, None), ("top.docx",))

    def test_all_ignores_directories_named_like_documents(self):
        self._create_files("report.docx")
        (self.input_directory / "folder.docx").mkdir()

        self.assertEqual(self.selector.select(self.input_directory, None), ("report.docx",))

    def test_none_raises_when_no_document_is_found(self):
        self._create_files("notes.txt")

        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, None)

    def test_text_all_raises_when_no_document_is_found(self):
        self._create_files("notes.txt")

        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, "all")

    def test_all_raises_when_input_directory_does_not_exist(self):
        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory / "missing", None)

    def test_explicit_list_is_returned_in_the_given_order_without_checking_files(self):
        self.assertEqual(
            self.selector.select(self.input_directory, ["02_b.docx", "01_a.docx"]),
            ("02_b.docx", "01_a.docx"),
        )

    def test_unknown_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, "report.docx")

    def test_non_text_non_list_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, 3)

    def test_list_with_non_text_item_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, ["01_a.docx", 2])

    def test_empty_list_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.selector.select(self.input_directory, [])
