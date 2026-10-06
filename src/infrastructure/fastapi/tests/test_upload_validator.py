from io import BytesIO
from pathlib import Path
from tempfile import gettempdir
from unittest import TestCase

from fastapi import UploadFile

from src.domain.exceptions.document_errors import (
    DocumentEmpty,
    DocumentInvalidType,
    DocumentTooLarge,
    DocumentUnreadable,
)
from src.infrastructure.fastapi.src.utils.upload_validator import validate_and_persist


class TestUploadValidator(TestCase):
    """Unit tests for the upload validator component."""

    def test_valid_docx_file_is_persisted_to_temp_path(self):
        for valid_filename in ("document.docx", "DOCUMENT.DOCX"):
            with self.subTest(valid_filename=valid_filename):
                file_content = b"sample valid docx payload content"
                upload_file = UploadFile(
                    filename=valid_filename,
                    file=BytesIO(file_content),
                )
                persisted_path = validate_and_persist(
                    upload_file=upload_file,
                    maximum_size_bytes=1024,
                )
                self.addCleanup(
                    lambda path_to_clean=persisted_path: path_to_clean.unlink(missing_ok=True)
                )

                self.assertTrue(persisted_path.exists())
                self.assertEqual(persisted_path.suffix, ".docx")
                self.assertEqual(persisted_path.read_bytes(), file_content)

    def test_legacy_doc_extension_raises_document_unreadable(self):
        for legacy_filename in ("document.doc", "DOCUMENT.DOC"):
            with self.subTest(legacy_filename=legacy_filename):
                upload_file = UploadFile(
                    filename=legacy_filename,
                    file=BytesIO(b"legacy doc content"),
                )
                with self.assertRaises(DocumentUnreadable) as context_manager:
                    validate_and_persist(
                        upload_file=upload_file,
                        maximum_size_bytes=1024,
                    )
                self.assertEqual(
                    context_manager.exception.dict()["error"],
                    DocumentUnreadable.MESSAGE,
                )

    def test_invalid_extension_raises_document_invalid_type(self):
        for invalid_filename in ("document.pdf", "document.txt", "document"):
            with self.subTest(invalid_filename=invalid_filename):
                upload_file = UploadFile(
                    filename=invalid_filename,
                    file=BytesIO(b"invalid type content"),
                )
                with self.assertRaises(DocumentInvalidType) as context_manager:
                    validate_and_persist(
                        upload_file=upload_file,
                        maximum_size_bytes=1024,
                    )
                self.assertEqual(
                    context_manager.exception.dict()["error"],
                    DocumentInvalidType.MESSAGE,
                )

    def test_oversized_file_raises_document_too_large_and_creates_no_file(self):
        oversized_content = b"a" * 1024
        upload_file = UploadFile(
            filename="oversized.docx",
            file=BytesIO(oversized_content),
        )
        temporary_directory = Path(gettempdir())
        existing_files_before = set(temporary_directory.glob("*.docx"))

        with self.assertRaises(DocumentTooLarge) as context_manager:
            validate_and_persist(
                upload_file=upload_file,
                maximum_size_bytes=512,
            )

        existing_files_after = set(temporary_directory.glob("*.docx"))
        newly_created_files = existing_files_after - existing_files_before

        self.assertEqual(len(newly_created_files), 0)
        self.assertEqual(
            context_manager.exception.dict()["error"],
            DocumentTooLarge.MESSAGE,
        )

    def test_empty_or_missing_filename_raises_document_empty(self):
        test_cases = [
            None,
            UploadFile(filename="", file=BytesIO(b"content")),
            UploadFile(filename="   ", file=BytesIO(b"content")),
            UploadFile(filename=None, file=BytesIO(b"content")),
        ]
        for upload_file in test_cases:
            with self.subTest(upload_file=upload_file):
                with self.assertRaises(DocumentEmpty) as context_manager:
                    validate_and_persist(
                        upload_file=upload_file,
                        maximum_size_bytes=1024,
                    )
                self.assertEqual(
                    context_manager.exception.dict()["error"],
                    DocumentEmpty.MESSAGE,
                )
