from pathlib import Path


class BatchDocumentSelector:
    """Chooses the document names a batch run analyzes, from a directory or an explicit list."""

    ALL_DOCUMENTS = "all"
    DOCUMENT_EXTENSION = ".docx"
    WORD_LOCK_FILE_PREFIX = "~$"

    def select(self, input_directory: Path, documents: str | list[str] | None) -> tuple[str, ...]:
        """Return the document names to analyze, in the order the batch file defines them."""
        if documents is None or documents == self.ALL_DOCUMENTS:
            return self._all_document_names(input_directory)
        if (
            isinstance(documents, list)
            and documents
            and all(isinstance(name, str) for name in documents)
        ):
            return tuple(documents)
        raise ValueError(
            f'documents must be "{self.ALL_DOCUMENTS}", a non-empty list of document names '
            f"or omitted, not {documents!r}"
        )

    def _all_document_names(self, input_directory: Path) -> tuple[str, ...]:
        document_names = tuple(sorted(self._word_document_names(input_directory)))
        if not document_names:
            raise ValueError(
                f'No {self.DOCUMENT_EXTENSION} document found in "{input_directory}" '
                f'for documents = "{self.ALL_DOCUMENTS}"'
            )
        return document_names

    def _word_document_names(self, input_directory: Path) -> list[str]:
        if not input_directory.is_dir():
            return []
        return [entry.name for entry in input_directory.iterdir() if self._is_word_document(entry)]

    def _is_word_document(self, entry: Path) -> bool:
        return (
            entry.is_file()
            and not entry.name.startswith(self.WORD_LOCK_FILE_PREFIX)
            and entry.suffix.lower() == self.DOCUMENT_EXTENSION
        )
