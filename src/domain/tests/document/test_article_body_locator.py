from unittest import TestCase

from src.domain.document.article_body_locator import ArticleBodyLocator
from src.domain.exceptions.document_errors import DocumentBodyNotLocated, DocumentEmpty
from src.domain.tests.dtos.editorial_norms_builder_for_test import build_editorial_norms_for_test


class TestArticleBodyLocator(TestCase):
    def test_splits_abstract_keywords_and_body_around_repeated_title(self):
        locator = self._build_locator()

        result = locator.locate(
            [
                "Main title",
                "Resumen",
                "An abstract sentence.",
                "Keywords: alpha; beta; gamma",
                "Main title",
                "Body one.",
                "Body two.",
            ]
        )

        self.assertEqual(result.title, "Main title")
        self.assertEqual(result.abstract_paragraphs, ("An abstract sentence.",))
        self.assertEqual(result.paragraphs, ("Body one.", "Body two."))

    def test_abstract_without_keywords_line_ends_at_repeated_title(self):
        locator = self._build_locator()

        result = locator.locate(
            [
                "Main title",
                "Resumen",
                "Abstract sentence one.",
                "Abstract sentence two.",
                "Main title",
                "Body.",
            ]
        )

        self.assertEqual(
            result.abstract_paragraphs, ("Abstract sentence one.", "Abstract sentence two.")
        )
        self.assertEqual(result.paragraphs, ("Body.",))

    def test_abstract_is_empty_when_there_is_no_abstract_heading(self):
        locator = self._build_locator()

        result = locator.locate(["Main title", "Plain paragraph.", "Main title", "Body."])

        self.assertEqual(result.abstract_paragraphs, ())
        self.assertEqual(result.paragraphs, ("Body.",))

    def test_finds_repeated_title_that_appends_a_subtitle(self):
        locator = self._build_locator()

        result = locator.locate(
            ["Main title:", "Resumen", "Abstract.", "Main title: subtitle", "Body."]
        )

        self.assertEqual(result.title, "Main title: subtitle")
        self.assertEqual(result.abstract_paragraphs, ("Abstract.",))
        self.assertEqual(result.paragraphs, ("Body.",))

    def test_later_paragraph_starting_like_the_first_does_not_replace_repeated_title(self):
        locator = self._build_locator()

        result = locator.locate(
            [
                "Main title",
                "Resumen",
                "Abstract.",
                "Main title: subtitle",
                "Body one.",
                "Main title returns later.",
                "Body two.",
            ]
        )

        self.assertEqual(result.title, "Main title: subtitle")
        self.assertEqual(result.paragraphs, ("Body one.", "Main title returns later.", "Body two."))

    def test_bibliography_header_closes_body_and_excludes_references(self):
        locator = self._build_locator()

        result = locator.locate(
            [
                "Main title",
                "Main title",
                "Body one.",
                "Refs",
                "Reference entry one.",
                "Reference entry two.",
            ]
        )

        self.assertEqual(result.paragraphs, ("Body one.",))

    def test_long_paragraph_containing_a_marker_is_not_bibliography_header(self):
        locator = self._build_locator()
        long_paragraph = "This long paragraph talks about refs in the middle of the body text."

        result = locator.locate(
            ["Main title", "Main title", "Body one.", long_paragraph, "Body two."]
        )

        self.assertEqual(result.paragraphs, ("Body one.", long_paragraph, "Body two."))

    def test_header_exactly_at_the_maximum_length_closes_the_body(self):
        locator = self._build_locator(bibliography_header_max_length=21)

        result = locator.locate(
            ["Main title", "Main title", "Body one.", "Refs and more entries", "Entry."]
        )

        self.assertEqual(result.paragraphs, ("Body one.",))

    def test_header_one_character_over_the_maximum_length_does_not_close_the_body(self):
        locator = self._build_locator(bibliography_header_max_length=21)

        result = locator.locate(
            ["Main title", "Main title", "Body one.", "Refs and more entries.", "Entry."]
        )

        self.assertEqual(result.paragraphs, ("Body one.", "Refs and more entries.", "Entry."))

    def test_body_runs_to_last_paragraph_without_bibliography_header(self):
        locator = self._build_locator()

        result = locator.locate(["Main title", "Main title", "Body one.", "Body two."])

        self.assertEqual(result.paragraphs, ("Body one.", "Body two."))

    def test_short_marker_paragraph_before_repeated_title_is_ignored(self):
        locator = self._build_locator()

        result = locator.locate(["Main title", "Refs", "Main title", "Body."])

        self.assertEqual(result.paragraphs, ("Body.",))

    def test_raises_when_repeated_title_is_not_found(self):
        locator = self._build_locator()

        with self.assertRaises(DocumentBodyNotLocated):
            locator.locate(["Main title", "Other paragraph.", "Another one."])

    def test_matches_markers_case_insensitively(self):
        locator = self._build_locator(
            abstract_section_keywords=("RESUMEN",),
            keyword_section_markers=("KEYWORDS",),
            bibliography_header_markers=("REFS",),
        )

        result = locator.locate(
            [
                "Main title",
                "Resumen",
                "Abstract.",
                "Keywords: alpha",
                "Main title",
                "Body.",
                "Refs",
                "Reference entry.",
            ]
        )

        self.assertEqual(result.abstract_paragraphs, ("Abstract.",))
        self.assertEqual(result.paragraphs, ("Body.",))

    def test_raises_when_there_are_no_paragraphs(self):
        locator = self._build_locator()

        with self.assertRaises(DocumentEmpty):
            locator.locate([])

    def test_successive_calls_return_independent_results(self):
        locator = self._build_locator()
        first_input = ["Main title", "Main title", "Body one."]
        second_input = ["Other title", "Resumen", "Abstract.", "Other title", "Body two."]

        first_result = locator.locate(first_input)
        second_result = locator.locate(second_input)
        first_result_again = locator.locate(first_input)

        self.assertEqual(first_result, first_result_again)
        self.assertEqual(second_result.title, "Other title")
        self.assertEqual(second_result.abstract_paragraphs, ("Abstract.",))
        self.assertEqual(second_result.paragraphs, ("Body two.",))

    def _build_locator(
        self,
        abstract_section_keywords: tuple[str, ...] = ("resumen",),
        keyword_section_markers: tuple[str, ...] = ("keywords",),
        bibliography_header_markers: tuple[str, ...] = ("refs", "biblio"),
        bibliography_header_max_length: int = 21,
    ) -> ArticleBodyLocator:
        editorial_norms = build_editorial_norms_for_test(
            abstract_section_keywords=abstract_section_keywords,
            keyword_section_markers=keyword_section_markers,
            bibliography_header_markers=bibliography_header_markers,
            bibliography_header_max_length=bibliography_header_max_length,
        )
        return ArticleBodyLocator(
            abstract_norms=editorial_norms.abstract,
            keyword_norms=editorial_norms.keywords,
            bibliography_norms=editorial_norms.bibliography,
        )
