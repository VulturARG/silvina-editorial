from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from src.domain.exceptions.document_errors import (
    DocumentEmpty,
    DocumentInvalidType,
    DocumentTooLarge,
    DocumentUnreadable,
)


def validate_and_persist(
    upload_file: UploadFile | None,
    maximum_size_bytes: int,
) -> Path:
    """Validate an uploaded document file and persist it to a temporary path."""
    if upload_file is None or upload_file.filename is None or not upload_file.filename.strip():
        raise DocumentEmpty()

    file_extension = Path(upload_file.filename).suffix.lower()
    if file_extension == ".doc":
        raise DocumentUnreadable()
    if file_extension != ".docx":
        raise DocumentInvalidType()

    try:
        if upload_file.file.seekable():
            upload_file.file.seek(0)
    except AttributeError:
        pass

    total_size_bytes = 0
    chunks: list[bytes] = []
    chunk_size = 65536

    while chunk := upload_file.file.read(chunk_size):
        total_size_bytes += len(chunk)
        if total_size_bytes > maximum_size_bytes:
            raise DocumentTooLarge()
        chunks.append(chunk)

    try:
        if upload_file.file.seekable():
            upload_file.file.seek(0)
    except AttributeError:
        pass

    with NamedTemporaryFile(suffix=".docx", delete=False) as temporary_file:
        for chunk in chunks:
            temporary_file.write(chunk)

    return Path(temporary_file.name)
