from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.classified_feedback_line_dto import ClassifiedFeedbackLineDTO
from src.domain.dtos.feedback_line_dto import FeedbackLineDTO
from src.domain.enums.feedback_line_kind import FeedbackLineKind


class TestClassifiedFeedbackLineDTO(TestCase):
    def test_inherits_from_base_dto(self):
        self.assertTrue(issubclass(ClassifiedFeedbackLineDTO, BaseDTO))

    def test_instantiation_with_defaults(self):
        line = FeedbackLineDTO(text="Texto", indentation=0)
        dto = ClassifiedFeedbackLineDTO(kind=FeedbackLineKind.TEXT, line=line)

        self.assertEqual(dto.kind, FeedbackLineKind.TEXT)
        self.assertEqual(dto.line, line)
        self.assertEqual(dto.title_text, "")
        self.assertEqual(dto.heading_level, 0)
        self.assertEqual(dto.list_marker, "")
        self.assertEqual(dto.item_content, "")
        self.assertFalse(dto.starts_unindented_children)

    def test_instantiation_with_all_fields(self):
        line = FeedbackLineDTO(text="- Item con detalle:", indentation=2)
        dto = ClassifiedFeedbackLineDTO(
            kind=FeedbackLineKind.BULLET,
            line=line,
            title_text="",
            heading_level=0,
            list_marker="•",
            item_content="Item con detalle:",
            starts_unindented_children=True,
        )

        self.assertEqual(dto.kind, FeedbackLineKind.BULLET)
        self.assertEqual(dto.list_marker, "•")
        self.assertEqual(dto.item_content, "Item con detalle:")
        self.assertTrue(dto.starts_unindented_children)
