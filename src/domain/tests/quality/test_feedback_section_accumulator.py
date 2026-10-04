from unittest import TestCase

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_section_accumulator import FeedbackSectionAccumulator


class TestFeedbackSectionAccumulator(TestCase):
    def test_initially_preceded_by_blank_is_true(self):
        accumulator = FeedbackSectionAccumulator()
        self.assertTrue(accumulator.is_preceded_by_blank())

    def test_mark_non_empty_line_makes_preceded_by_blank_false(self):
        accumulator = FeedbackSectionAccumulator()
        accumulator.mark_non_empty_line()
        self.assertFalse(accumulator.is_preceded_by_blank())

    def test_mark_blank_line_makes_preceded_by_blank_true(self):
        accumulator = FeedbackSectionAccumulator()
        accumulator.mark_non_empty_line()
        accumulator.mark_blank_line()
        self.assertTrue(accumulator.is_preceded_by_blank())

    def test_set_previous_line_counts_as_blank_controls_state(self):
        accumulator = FeedbackSectionAccumulator()
        accumulator.mark_non_empty_line()
        accumulator.set_previous_line_counts_as_blank(True)
        self.assertTrue(accumulator.is_preceded_by_blank())

        accumulator.set_previous_line_counts_as_blank(False)
        self.assertFalse(accumulator.is_preceded_by_blank())

    def test_accumulates_blocks_and_sections_across_title_openings(self):
        accumulator = FeedbackSectionAccumulator()
        first_title = FeedbackBlockDTO(
            kind=FeedbackBlockKind.TITLE, text="Sección 1", level=0, marker=""
        )
        first_item = FeedbackBlockDTO(
            kind=FeedbackBlockKind.ITEM, text="Item 1", level=0, marker="•"
        )
        second_title = FeedbackBlockDTO(
            kind=FeedbackBlockKind.TITLE, text="Sección 2", level=0, marker=""
        )
        second_item = FeedbackBlockDTO(
            kind=FeedbackBlockKind.ITEM, text="Item 2", level=0, marker="•"
        )

        accumulator.open_title(first_title)
        accumulator.append_block(first_item)
        accumulator.open_title(second_title)
        accumulator.append_block(second_item)

        sections = accumulator.finish()

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0], (first_title, [first_item]))
        self.assertEqual(sections[1], (second_title, [second_item]))

    def test_finish_returns_empty_when_no_blocks_or_titles_added(self):
        accumulator = FeedbackSectionAccumulator()
        sections = accumulator.finish()
        self.assertEqual(sections, [])

    def test_blocks_before_first_title_accumulate_with_none_title(self):
        accumulator = FeedbackSectionAccumulator()
        initial_text = FeedbackBlockDTO(
            kind=FeedbackBlockKind.TEXT, text="Intro", level=0, marker=""
        )
        title = FeedbackBlockDTO(kind=FeedbackBlockKind.TITLE, text="Título", level=0, marker="")
        item = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Item", level=0, marker="•")

        accumulator.append_block(initial_text)
        accumulator.open_title(title)
        accumulator.append_block(item)

        sections = accumulator.finish()

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0], (None, [initial_text]))
        self.assertEqual(sections[1], (title, [item]))
