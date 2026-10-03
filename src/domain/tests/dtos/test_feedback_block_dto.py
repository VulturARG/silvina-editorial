from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind


class TestFeedbackBlockDTO(TestCase):
    def test_is_frozen_dataclass_extending_base_dto(self):
        self.assertTrue(issubclass(FeedbackBlockDTO, BaseDTO))
        block = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Sample text")
        with self.assertRaises(FrozenInstanceError):
            block.text = "New text"

    def test_default_values_for_level_and_marker(self):
        block = FeedbackBlockDTO(kind=FeedbackBlockKind.TITLE, text="Fortalezas")
        self.assertEqual(block.kind, FeedbackBlockKind.TITLE)
        self.assertEqual(block.text, "Fortalezas")
        self.assertEqual(block.level, 0)
        self.assertEqual(block.marker, "")

    def test_custom_values_for_numbered_and_nested_item(self):
        block = FeedbackBlockDTO(
            kind=FeedbackBlockKind.ITEM,
            text="Composición estadística",
            level=1,
            marker="1.",
        )
        self.assertEqual(block.kind, FeedbackBlockKind.ITEM)
        self.assertEqual(block.text, "Composición estadística")
        self.assertEqual(block.level, 1)
        self.assertEqual(block.marker, "1.")
