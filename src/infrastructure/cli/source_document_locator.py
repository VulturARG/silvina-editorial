from pathlib import Path

from src.domain.exceptions.document_errors import DocumentInvalidType, DocumentNotFound


class SourceDocumentLocator:
    """Find the .docx document to analyze and validate that it can be used."""

    DOCUMENT_EXTENSION = ".docx"
    BARE_NAME_PARENT = Path(".")

    def locate(self, document_name: str, input_directory: Path | None) -> Path:
        """Return the absolute path of the document, validating that it is an existing .docx file."""
        document_path = Path(document_name)
        if document_path.parent == self.BARE_NAME_PARENT:
            base_directory = Path.cwd() if input_directory is None else input_directory
            document_path = base_directory / document_path
        resolved_path = document_path.resolve()
        if not resolved_path.is_file():
            raise DocumentNotFound(detail=str(resolved_path))
        if resolved_path.suffix.lower() != self.DOCUMENT_EXTENSION:
            raise DocumentInvalidType(detail=str(resolved_path))
        return resolved_path
