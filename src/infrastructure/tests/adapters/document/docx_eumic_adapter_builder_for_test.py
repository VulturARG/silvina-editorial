from pathlib import Path

from src.domain.dtos.editorial_norms_dto import EditorialNormsDTO
from src.infrastructure.adapters.document.docx_eumic_adapter import DocxEumicAdapter
from src.infrastructure.editorial_norms_loader import EditorialNormsLoader

_PROJECT_ROOT_PATH = Path(__file__).resolve().parents[5]
_DEFAULT_EDITORIAL_NORMS_PATH = _PROJECT_ROOT_PATH / "editorial_norms.toml"
_DEFAULT_MINIMUM_WORDS_FOR_ABSTRACT_CHECK = 1000


class DocxEumicAdapterBuilderForTest:
    """Builds DocxEumicAdapter instances configured for tests."""

    def build(
        self,
        norms: EditorialNormsDTO | None = None,
        minimum_words_for_abstract_check: int = _DEFAULT_MINIMUM_WORDS_FOR_ABSTRACT_CHECK,
    ) -> DocxEumicAdapter:
        """Create a DocxEumicAdapter with loaded or supplied norms and threshold."""
        resolved_norms = (
            norms
            if norms is not None
            else EditorialNormsLoader(_DEFAULT_EDITORIAL_NORMS_PATH).load()
        )
        return DocxEumicAdapter(
            norms=resolved_norms,
            minimum_words_for_abstract_check=minimum_words_for_abstract_check,
        )
