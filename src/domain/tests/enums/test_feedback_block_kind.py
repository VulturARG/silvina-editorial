from enum import Enum
from unittest import TestCase

from src.domain.enums.feedback_block_kind import FeedbackBlockKind


class TestFeedbackBlockKind(TestCase):
    def test_is_subclass_of_enum(self):
        self.assertTrue(issubclass(FeedbackBlockKind, Enum))

    def test_has_expected_members_and_values(self):
        self.assertEqual(FeedbackBlockKind.TITLE.value, "title")
        self.assertEqual(FeedbackBlockKind.ITEM.value, "item")
        self.assertEqual(FeedbackBlockKind.TEXT.value, "text")
