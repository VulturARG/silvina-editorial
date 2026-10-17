from unittest import TestCase

from src.domain.dtos.article_body_dto import ArticleBodyDTO
from src.domain.dtos.body_table_dto import BodyTableDTO

FIRST_TABLE_MARKDOWN = "| Name | Score |\n| --- | --- |\n| Ana | 9 |"
SECOND_TABLE_MARKDOWN = "| Key | Value |\n| --- | --- |\n| x | y |"


class TestArticleBodyDTOParagraphsTextWithTables(TestCase):
    def test_equals_plain_join_of_paragraphs_when_there_are_no_tables(self):
        body = ArticleBodyDTO(
            title="Title", abstract_paragraphs=(), paragraphs=("First.", "Second.")
        )

        self.assertEqual(body.paragraphs_text_with_tables, "First. Second.")

    def test_inserts_table_between_surrounding_paragraphs_with_blank_lines(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("Before.", "Caption.", "After."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),),
        )

        self.assertEqual(
            body.paragraphs_text_with_tables,
            f"Before. Caption.\n\n{FIRST_TABLE_MARKDOWN}\n\nAfter.",
        )

    def test_places_table_at_position_zero_before_the_first_paragraph(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=0),),
        )

        self.assertEqual(
            body.paragraphs_text_with_tables,
            f"{FIRST_TABLE_MARKDOWN}\n\nFirst. Second.",
        )

    def test_places_table_at_the_end_when_position_equals_paragraph_count(self):
        body = ArticleBodyDTO(
            title="Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),),
        )

        self.assertEqual(
            body.paragraphs_text_with_tables,
            f"First. Second.\n\n{FIRST_TABLE_MARKDOWN}",
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
            body.paragraphs_text_with_tables,
            f"A\n\n{FIRST_TABLE_MARKDOWN}\n\nB C\n\n{SECOND_TABLE_MARKDOWN}",
        )

    def test_never_contains_the_title_with_or_without_tables(self):
        body_without_tables = ArticleBodyDTO(
            title="Unique Heading Title", abstract_paragraphs=(), paragraphs=("First.",)
        )
        body_with_tables = ArticleBodyDTO(
            title="Unique Heading Title",
            abstract_paragraphs=(),
            paragraphs=("First.", "Second."),
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),),
        )

        self.assertNotIn("Unique Heading Title", body_without_tables.paragraphs_text_with_tables)
        self.assertNotIn("Unique Heading Title", body_with_tables.paragraphs_text_with_tables)
