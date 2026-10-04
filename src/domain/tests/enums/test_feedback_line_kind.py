from unittest import TestCase

from src.domain.enums.feedback_line_kind import FeedbackLineKind


class TestFeedbackLineKind(TestCase):
    def test_contains_all_expected_kind_variants(self):
        expected_values = {
            "HEADING": "heading",
            "BOLD_TITLE": "bold_title",
            "PLAIN_TITLE": "plain_title",
            "BULLET": "bullet",
            "NUMBERED": "numbered",
            "TABLE_ROW": "table_row",
            "HORIZONTAL_RULE": "horizontal_rule",
            "TEXT": "text",
        }
        for name, value in expected_values.items():
            self.assertTrue(hasattr(FeedbackLineKind, name))
            self.assertEqual(getattr(FeedbackLineKind, name).value, value)
