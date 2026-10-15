from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.domain.tests.dtos.editorial_norms_builder_for_test import (
    build_editorial_norms_for_test,
)
from src.infrastructure.adapters.document.docx_eumic_adapter import DocxEumicAdapter

_DEFAULT_MINIMUM_WORDS_FOR_ABSTRACT_CHECK = 1000


class DocxEumicAdapterBuilderForTest:
    """Builds DocxEumicAdapter instances configured for tests."""

    def build(
        self,
        norms: EditorialNormsDTO | None = None,
        minimum_words_for_abstract_check: int = _DEFAULT_MINIMUM_WORDS_FOR_ABSTRACT_CHECK,
    ) -> DocxEumicAdapter:
        """Create a DocxEumicAdapter with test-owned or supplied norms and threshold."""
        resolved_norms = norms if norms is not None else build_editorial_norms_for_test()
        return DocxEumicAdapter(
            norms=resolved_norms,
            minimum_words_for_abstract_check=minimum_words_for_abstract_check,
        )
