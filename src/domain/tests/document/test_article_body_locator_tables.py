from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.dtos.body_table_dto import BodyTableDTO
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test

ARTICLE_PARAGRAPHS = [
    "Main title",
    "Resumen",
    "Abstract.",
    "Main title",
    "Body one.",
    "Body two.",
    "Refs",
    "Entry.",
]
FIRST_TABLE_MARKDOWN = "| A | B |\n| --- | --- |\n| 1 | 2 |"
SECOND_TABLE_MARKDOWN = "| C | D |\n| --- | --- |\n| 3 | 4 |"


class TestArticleBodyLocatorTables(TestCase):
    def test_keeps_table_inside_body_and_rebases_position_to_body_paragraphs(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=5)],
        )

        self.assertEqual(result.tables, (BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),))

    def test_keeps_table_before_first_body_paragraph_with_position_zero(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=4)],
        )

        self.assertEqual(result.tables, (BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=0),))

    def test_keeps_table_at_bibliography_header_boundary_with_position_equal_to_body_length(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=6)],
        )

        self.assertEqual(result.tables, (BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),))

    def test_keeps_table_at_end_of_body_when_there_is_no_bibliography_header(self):
        locator = self._build_locator()

        result = locator.locate(
            ["Main title", "Main title", "Body one."],
            tables=[BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=3)],
        )

        self.assertEqual(result.tables, (BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),))

    def test_drops_tables_before_the_repeated_title(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=0),
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=2),
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=3),
            ],
        )

        self.assertEqual(result.tables, ())

    def test_drops_tables_after_the_bibliography_header(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=7),
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=8),
            ],
        )

        self.assertEqual(result.tables, ())

    def test_keeps_tables_sharing_a_position_in_their_original_order(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=[
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=5),
                BodyTableDTO(markdown=SECOND_TABLE_MARKDOWN, position=5),
            ],
        )

        self.assertEqual(
            result.tables,
            (
                BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),
                BodyTableDTO(markdown=SECOND_TABLE_MARKDOWN, position=1),
            ),
        )

    def test_accepts_tables_given_as_tuple(self):
        locator = self._build_locator()

        result = locator.locate(
            ARTICLE_PARAGRAPHS,
            tables=(BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=5),),
        )

        self.assertEqual(result.tables, (BodyTableDTO(markdown=FIRST_TABLE_MARKDOWN, position=1),))

    def test_returns_no_tables_when_none_are_given(self):
        locator = self._build_locator()

        result = locator.locate(ARTICLE_PARAGRAPHS)

        self.assertEqual(result.tables, ())

    def _build_locator(self) -> ArticleBodyLocator:
        editorial_norms = build_editorial_norms_for_test(
            abstract_section_keywords=("resumen",),
            keyword_section_markers=("keywords",),
            bibliography_header_markers=("refs", "biblio"),
            bibliography_header_max_length=21,
        )
        return ArticleBodyLocator(
            abstract_norms=editorial_norms.abstract,
            keyword_norms=editorial_norms.keywords,
            bibliography_norms=editorial_norms.bibliography,
        )
