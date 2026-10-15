from src.domain.dtos.article_length_norms_dto import ArticleLengthNormsDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentBodyNotLocated, DocumentBodyTooLong


class ArticleLengthChecker:
    """Domain service that rejects article bodies longer than the editorial maximum."""

    def __init__(self, article_length_norms: ArticleLengthNormsDTO) -> None:
        self._article_length_norms = article_length_norms

    def check(self, document_content: DocumentContentDTO) -> None:
        """Raise when the body is missing or has more characters than the maximum allowed."""
        body = document_content.body
        if body is None:
            raise DocumentBodyNotLocated()
        maximum_body_characters = self._article_length_norms.max_body_chars
        if body.char_count > maximum_body_characters:
            raise DocumentBodyTooLong(
                body_characters=body.char_count,
                maximum_body_characters=maximum_body_characters,
            )
