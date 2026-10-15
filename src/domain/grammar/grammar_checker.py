from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.exceptions.document_errors import DocumentBodyNotLocated
from src.domain.grammar.grammar_check_port import GrammarCheckPort
from src.domain.grammar.grammar_score_level import GrammarScoreLevel


class GrammarChecker:
    """Domain service that checks grammar and computes the resulting score level."""

    def __init__(self, grammar_check_port: GrammarCheckPort) -> None:
        self._grammar_check_port = grammar_check_port

    def check_grammar(self, document_content: DocumentContentDTO) -> GrammarCheckResultDTO:
        """Check grammar errors in the article body and map them to a score level."""
        body = document_content.body
        if body is None:
            raise DocumentBodyNotLocated()
        errors = self._grammar_check_port.check(paragraphs=body.abstract_and_body_paragraphs)
        level = GrammarScoreLevel.from_error_count(error_count=len(errors))
        return GrammarCheckResultDTO(score=level.score, feedback=level.feedback, errors=errors)
