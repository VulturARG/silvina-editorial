from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.exceptions.document_errors import DocumentBodyNotLocated
from src.domain.grammar.grammar_checker import GrammarChecker
from src.domain.tests.grammar.recording_grammar_check_port import RecordingGrammarCheckPort

LONG_PARAGRAPH_CHARACTERS = 200_000


def _build_content(
    title: str = "Title",
    abstract_paragraphs: tuple[str, ...] = (),
    paragraphs: tuple[str, ...] = (),
) -> DocumentContentDTO:
    body = ArticleBodyDTO(
        title=title, abstract_paragraphs=abstract_paragraphs, paragraphs=paragraphs
    )
    return DocumentContentDTO(word_count=0, char_count=0, body=body)


class TestGrammarCheckerDocumentBody(TestCase):
    def setUp(self):
        self._port = RecordingGrammarCheckPort()
        self._checker = GrammarChecker(grammar_check_port=self._port)

    def test_passes_abstract_title_and_every_body_paragraph_to_the_port_in_order(self):
        content = _build_content(
            title="Title",
            abstract_paragraphs=("Abstract.",),
            paragraphs=("First.", "Second.", "Third."),
        )

        self._checker.check_grammar(document_content=content)

        self.assertEqual(
            self._port.received_paragraphs,
            ["Abstract.", "Title", "First.", "Second.", "Third."],
        )

    def test_does_not_cut_a_body_of_two_hundred_thousand_characters(self):
        long_paragraph = "a" * LONG_PARAGRAPH_CHARACTERS
        content = _build_content(title="Title", paragraphs=(long_paragraph,))

        self._checker.check_grammar(document_content=content)

        self.assertEqual(self._port.received_paragraphs, ["Title", long_paragraph])

    def test_raises_document_body_not_located_when_body_is_missing(self):
        content = DocumentContentDTO(word_count=0, char_count=0)

        with self.assertRaises(DocumentBodyNotLocated):
            self._checker.check_grammar(document_content=content)

    def test_does_not_call_the_port_when_body_is_missing(self):
        content = DocumentContentDTO(word_count=0, char_count=0)

        with self.assertRaises(DocumentBodyNotLocated):
            self._checker.check_grammar(document_content=content)

        self.assertIsNone(self._port.received_paragraphs)
