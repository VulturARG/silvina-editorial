from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.body_table_dto import BodyTableDTO

FIRST_TABLE_MARKDOWN = "| Name | Score |\n| --- | --- |\n| Ana | 9 |"
SECOND_TABLE_MARKDOWN = "| Key | Value |\n| --- | --- |\n| x | y |"


class TestArticleBodyDTOTextWithTables(TestCase):
    def test_separates_title_and_paragraphs_with_blank_lines_without_tables(self):
        body = ArticleBodyDTO(
            title="Title", abstract_paragraphs=(), paragraphs=("First.", "Second.")
        )

        self.assertEqual(body.text_with_tables, "Title\n\nFirst.\n\nSecond.")

    def test_separates_title_from_a_single_paragraph_with_blank_line(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=("Only.",))

        self.assertEqual(body.text_with_tables, "Title\n\nOnly.")

    def test_is_title_alone_when_there_are_no_paragraphs_and_no_tables(self):
        body = ArticleBodyDTO(title="Title", abstract_paragraphs=(), paragraphs=())

        self.assertEqual(body.text_with_tables, "Title")

    def test_places_only_table_after_the_title_when_there_are_no_paragraphs(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=(),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=0),),
        )

        self.assertEqual(body.text_with_tables, f"Title\n\n{FIRST_TABLE_MARKDOWN}")

    def test_inserts_table_between_surrounding_paragraphs_with_blank_lines(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("Before.", "Caption.", "After."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),),
        )

        self.assertEqual(
            body.text_with_tables,
            f"Title\n\nBefore.\n\nCaption.\n\n{FIRST_TABLE_MARKDOWN}\n\nAfter.",
        )

    def test_places_table_at_position_zero_right_after_the_title(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=0),),
        )

        self.assertEqual(
            body.text_with_tables,
            f"Title\n\n{FIRST_TABLE_MARKDOWN}\n\nFirst.\n\nSecond.",
        )

    def test_places_table_at_the_end_when_position_equals_paragraph_count(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),),
        )

        self.assertEqual(
            body.text_with_tables,
            f"Title\n\nFirst.\n\nSecond.\n\n{FIRST_TABLE_MARKDOWN}",
        )

    def test_places_two_tables_at_their_own_positions(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("A", "B", "C"),
            tables=(
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),
                BodyTableDTO(markdown=SECOND_TABLE_MARKDOWN, position=3),
            ),
        )

        self.assertEqual(
            body.text_with_tables,
            f"Title\n\nA\n\n{FIRST_TABLE_MARKDOWN}\n\nB\n\nC\n\n{SECOND_TABLE_MARKDOWN}",
        )

    def test_keeps_order_of_tables_sharing_a_position(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("A", "B"),
            tables=(
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),
                BodyTableDTO(markdown=SECOND_TABLE_MARKDOWN, position=1),
            ),
        )

        self.assertEqual(
            body.text_with_tables,
            f"Title\n\nA\n\n{FIRST_TABLE_MARKDOWN}\n\n{SECOND_TABLE_MARKDOWN}\n\nB",
        )

    def test_text_and_char_count_ignore_tables(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=("Abstract.",),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),),
        )

        self.assertEqual(body.text, "Title First. Second.")
        self.assertEqual(body.char_count, len("Title First. Second."))
