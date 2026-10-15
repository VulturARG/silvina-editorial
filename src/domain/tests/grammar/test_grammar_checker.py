from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.grammar_error_dto import GrammarErrorDTO
from src.domain.grammar.grammar_checker import GrammarChecker
from src.domain.grammar.grammar_score_level import GrammarScoreLevel
from src.domain.tests.grammar.fake_grammar_check_port import FakeGrammarCheckPort


def _build_content(paragraphs: tuple[str, ...]) -> DocumentContentDTO:
    body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=paragraphs)
    return DocumentContentDTO(word_count=0, char_count=0, body=body)


class TestGrammarChecker(TestCase):
    def test_check_grammar_returns_perfect_score_when_no_errors(self):
        port = FakeGrammarCheckPort(errors=[])
        checker = GrammarChecker(grammar_check_port=port)

        result = checker.check_grammar(document_content=_build_content(("Todo bien.",)))

        self.assertEqual(result.errors, [])
        self.assertEqual(result.score, GrammarScoreLevel.PERFECT.score)
        self.assertEqual(result.feedback, GrammarScoreLevel.PERFECT.feedback)

    def test_check_grammar_returns_errors_and_matching_score_level(self):
        errors = [
            GrammarErrorDTO(
                number=i, message="err", context="ctx", offset=0, length=1, replacements=[]
            )
            for i in range(6)
        ]
        port = FakeGrammarCheckPort(errors=errors)
        checker = GrammarChecker(grammar_check_port=port)

        result = checker.check_grammar(document_content=_build_content(("Texto con errores.",)))

        self.assertEqual(len(result.errors), 6)
        self.assertEqual(result.score, GrammarScoreLevel.MODERATE.score)
        self.assertEqual(result.feedback, GrammarScoreLevel.MODERATE.feedback)
