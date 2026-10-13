from os import chdir, getcwd
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.exceptions.document_errors import DocumentInvalidType, DocumentNotFound
from src.infrastructure.cli.source_document_locator import SourceDocumentLocator


class TestSourceDocumentLocator(TestCase):
    def setUp(self):
        self.locator = SourceDocumentLocator()
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.input_directory = Path(temporary_directory.name)

    @staticmethod
    def _create_file(file_path: Path) -> Path:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"")
        return file_path

    def _change_current_directory(self, directory: Path) -> None:
        original_directory = getcwd()
        self.addCleanup(chdir, original_directory)
        chdir(directory)

    def test_resolves_bare_name_inside_input_directory(self):
        expected = self._create_file(self.input_directory / "report.docx").resolve()

        self.assertEqual(self.locator.locate("report.docx", self.input_directory), expected)

    def test_resolves_bare_name_inside_current_directory_when_input_directory_is_none(self):
        expected = self._create_file(self.input_directory / "report.docx").resolve()
        self._change_current_directory(self.input_directory)

        self.assertEqual(self.locator.locate("report.docx", None), expected)

    def test_document_name_with_directory_ignores_input_directory(self):
        document_path = self._create_file(self.input_directory / "sub" / "report.docx").resolve()
        other_directory = self.input_directory / "other"
        other_directory.mkdir()

        self.assertEqual(self.locator.locate(str(document_path), other_directory), document_path)

    def test_missing_document_raises_document_not_found_with_path_in_detail(self):
        missing_path = (self.input_directory / "missing.docx").resolve()

        with self.assertRaises(DocumentNotFound) as context:
            self.locator.locate("missing.docx", self.input_directory)

        self.assertEqual(context.exception.detail, str(missing_path))

    def test_doc_extension_raises_document_invalid_type_with_path_in_detail(self):
        doc_path = self._create_file(self.input_directory / "old.doc").resolve()

        with self.assertRaises(DocumentInvalidType) as context:
            self.locator.locate("old.doc", self.input_directory)

        self.assertEqual(context.exception.detail, str(doc_path))

    def test_existence_is_checked_before_extension(self):
        with self.assertRaises(DocumentNotFound):
            self.locator.locate("missing.doc", self.input_directory)

    def test_uppercase_docx_extension_is_accepted(self):
        expected = self._create_file(self.input_directory / "REPORT.DOCX").resolve()

        self.assertEqual(self.locator.locate("REPORT.DOCX", self.input_directory), expected)

    def test_directory_named_like_a_docx_is_not_accepted_as_document(self):
        (self.input_directory / "folder.docx").mkdir()

        with self.assertRaises(DocumentNotFound):
            self.locator.locate("folder.docx", self.input_directory)
