from unittest import TestCase

from src.domain.quality.feedback_text_cleaner import FeedbackTextCleaner


class TestFeedbackTextCleaner(TestCase):
    def test_clean_title_text_strips_surrounding_whitespace(self):
        cleaner = FeedbackTextCleaner()

        result = cleaner.clean_title_text("   Título simple   ")

        self.assertEqual(result, "Título simple")

    def test_clean_title_text_removes_trailing_colon(self):
        cleaner = FeedbackTextCleaner()

        result = cleaner.clean_title_text("Observaciones generales:")

        self.assertEqual(result, "Observaciones generales")

    def test_clean_title_text_removes_wrapping_bold_markers(self):
        cleaner = FeedbackTextCleaner()

        result = cleaner.clean_title_text("**Sección principal**")

        self.assertEqual(result, "Sección principal")

    def test_clean_title_text_removes_colon_both_inside_and_outside_bold(self):
        cleaner = FeedbackTextCleaner()

        self.assertEqual(
            cleaner.clean_title_text("**Puntos clave:**"),
            "Puntos clave",
        )
        self.assertEqual(
            cleaner.clean_title_text("**Puntos clave**:"),
            "Puntos clave",
        )

    def test_clean_dangling_bold_leaves_balanced_bold_intact(self):
        cleaner = FeedbackTextCleaner()

        text = "Este es un **texto destacado** sin cambios."

        self.assertEqual(cleaner.clean_dangling_bold(text), text)

    def test_clean_dangling_bold_removes_unmatched_trailing_bold_marker_and_normalizes_spaces(self):
        cleaner = FeedbackTextCleaner()

        text = "Texto con un marcador residual ** final"

        self.assertEqual(
            cleaner.clean_dangling_bold(text),
            "Texto con un marcador residual final",
        )

    def test_clean_dangling_bold_removes_single_unmatched_bold_at_start(self):
        cleaner = FeedbackTextCleaner()

        text = "**Elemento inicial sin cierre"

        self.assertEqual(
            cleaner.clean_dangling_bold(text),
            "Elemento inicial sin cierre",
        )
