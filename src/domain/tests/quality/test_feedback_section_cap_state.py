from unittest import TestCase

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_section_cap_state import FeedbackSectionCapState


class TestFeedbackSectionCapState(TestCase):
    def test_level_zero_blocks_capped_at_maximum_items(self):
        state = FeedbackSectionCapState(maximum_items=2)
        block_1 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Item 1", level=0, marker="•")
        block_2 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Item 2", level=0, marker="•")
        block_3 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Item 3", level=0, marker="•")

        state.process_block(block_1)
        state.process_block(block_2)
        state.process_block(block_3)

        self.assertEqual(state.kept_blocks(), [block_1, block_2])

    def test_level_one_blocks_capped_at_maximum_items_per_parent(self):
        state = FeedbackSectionCapState(maximum_items=2)
        parent = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Parent", level=0, marker="•")
        child_1 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Child 1", level=1, marker="•")
        child_2 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Child 2", level=1, marker="•")
        child_3 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Child 3", level=1, marker="•")

        state.process_block(parent)
        state.process_block(child_1)
        state.process_block(child_2)
        state.process_block(child_3)

        self.assertEqual(state.kept_blocks(), [parent, child_1, child_2])

    def test_level_one_blocks_dropped_if_parent_dropped(self):
        state = FeedbackSectionCapState(maximum_items=1)
        parent_1 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="P1", level=0, marker="•")
        parent_2 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="P2", level=0, marker="•")
        child = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Child", level=1, marker="•")

        state.process_block(parent_1)
        state.process_block(parent_2)
        state.process_block(child)

        self.assertEqual(state.kept_blocks(), [parent_1])

    def test_new_level_zero_resets_level_one_count(self):
        state = FeedbackSectionCapState(maximum_items=2)
        parent_1 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="P1", level=0, marker="•")
        child_1 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="C1", level=1, marker="•")
        parent_2 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="P2", level=0, marker="•")
        child_2 = FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="C2", level=1, marker="•")

        state.process_block(parent_1)
        state.process_block(child_1)
        state.process_block(parent_2)
        state.process_block(child_2)

        self.assertEqual(state.kept_blocks(), [parent_1, child_1, parent_2, child_2])
