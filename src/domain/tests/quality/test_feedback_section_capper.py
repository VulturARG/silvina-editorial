from unittest import TestCase

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.quality.feedback_section_capper import FeedbackSectionCapper


class TestFeedbackSectionCapper(TestCase):
    def test_caps_top_level_items_to_maximum_limit(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=2)
        blocks = [
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Uno", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Dos", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Tres", level=0, marker="•"),
        ]
        sections = [(None, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].text, "Uno")
        self.assertEqual(result[1].text, "Dos")

    def test_caps_level_one_children_per_parent_to_maximum_limit(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=2)
        blocks = [
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Padre", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo 1", level=1, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo 2", level=1, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo 3", level=1, marker="•"),
        ]
        sections = [(None, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 3)
        self.assertEqual([block.text for block in result], ["Padre", "Hijo 1", "Hijo 2"])

    def test_drops_title_when_no_blocks_are_kept_in_section(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=2)
        title = FeedbackBlockDTO(kind=FeedbackBlockKind.TITLE, text="Título", level=0, marker="")
        sections = [(title, [])]

        result = capper.cap_sections(sections)

        self.assertEqual(result, ())

    def test_preserves_title_when_at_least_one_block_is_kept(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=2)
        title = FeedbackBlockDTO(kind=FeedbackBlockKind.TITLE, text="Título", level=0, marker="")
        blocks = [FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Item", level=0, marker="•")]
        sections = [(title, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].text, "Título")
        self.assertEqual(result[1].text, "Item")

    def test_drops_level_one_children_when_parent_is_capped_out(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=1)
        blocks = [
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Padre 1", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo 1.1", level=1, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Padre 2", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo 2.1", level=1, marker="•"),
        ]
        sections = [(None, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 2)
        self.assertEqual([block.text for block in result], ["Padre 1", "Hijo 1.1"])

    def test_blocks_without_title_are_kept_up_to_cap(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=3)
        blocks = [
            FeedbackBlockDTO(kind=FeedbackBlockKind.TEXT, text="Párrafo", level=0, marker=""),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Punto", level=0, marker="•"),
        ]
        sections = [(None, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].text, "Párrafo")
        self.assertEqual(result[1].text, "Punto")

    def test_dead_branch_levels_above_one_are_never_included(self):
        capper = FeedbackSectionCapper(maximum_items_per_section=5)
        blocks = [
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Padre", level=0, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Hijo", level=1, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Nieto", level=2, marker="•"),
            FeedbackBlockDTO(kind=FeedbackBlockKind.ITEM, text="Bisnieto", level=3, marker="•"),
        ]
        sections = [(None, blocks)]

        result = capper.cap_sections(sections)

        self.assertEqual(len(result), 2)
        self.assertEqual([b.text for b in result], ["Padre", "Hijo"])
        self.assertTrue(all(block.level in (0, 1) for block in result))
